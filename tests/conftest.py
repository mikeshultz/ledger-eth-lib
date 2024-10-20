"""pytest conftest file with fixtures and else."""

import os
from contextlib import contextmanager

import pytest
from eth_account.account import Account
from eth_account.messages import SignableMessage, encode_defunct
from eth_account.signers.local import LocalAccount
from eth_utils.hexadecimal import decode_hex
from hexbytes import HexBytes
from ledgerblue.comm import getDongle

from ledgereth.constants import DATA_CHUNK_SIZE
from ledgereth.exceptions import LedgerError
from ledgereth.transactions import decode_transaction
from ledgereth.utils import decode_bip32_path

TEST_MNEMONIC = "test test test test test test test test test test test junk"
USE_REAL_DONGLE = os.environ.get("USE_REAL_DONGLE") is not None

# We must enable HD account derivation for eth_account while it's experimental
Account.enable_unaudited_hdwallet_features()


def get_account_by_path(path: bytes) -> LocalAccount:
    """Get a test account by derivation path."""
    path_string = decode_bip32_path(path)
    return Account.from_mnemonic(TEST_MNEMONIC, account_path=f"m/{path_string}")


class MockDongle:
    """Mock Ledger Dongle class.

    Attempts to act like an actual Ledger dongle for the sake of not
    requiring user-intervention for every single test with a real ledger
    attached.
    """

    def __init__(self):
        """Initialize a mock dongle."""
        self._reset()

    def _reset(self):
        self.account = None
        self.stack = []

    def _resp_to_bytearray(self, resp):
        # for large chain_id, v can be bigger than a byte. we'll take the lowest
        # byte for the signature
        v = resp.v.to_bytes(8, "big")[7].to_bytes(1, "big")
        r = resp.r.to_bytes(32, "big")
        s = resp.s.to_bytes(32, "big")

        # Reset the stack and account MockLegder working with
        self._reset()

        return bytearray(v + r + s)

    def _sign_transaction(self, encoded_tx):
        """Sign transaction data sent to the Ledger."""
        tx = decode_transaction(encoded_tx)
        assert self.account is not None
        resp = self.account.sign_transaction(tx.to_rpc_dict())

        return self._resp_to_bytearray(resp)

    def _sign_message(self, encoded):
        """Sign message accodign to EIP-191."""
        signable = encode_defunct(encoded)
        assert self.account is not None
        resp = self.account.sign_message(signable)

        return self._resp_to_bytearray(resp)

    def _sign_typed(self, domain_hash, message_hash):
        """Sign message accodign to EIP-191."""
        signable = SignableMessage(
            HexBytes(b"\x01"),
            domain_hash,
            message_hash,
        )
        assert self.account is not None
        resp = self.account.sign_message(signable)

        return self._resp_to_bytearray(resp)

    def _handle_get_configuration(self, lc, data):
        # Return version 9.9.9
        return bytearray(b"\x00\x09\x09\x09")

    def _handle_get_address(self, lc, data):
        # First byte is len(path) // 4
        encoded_path = data[1 : lc + 1]
        account = get_account_by_path(encoded_path)

        # This "junk" might mean something in the actual Ledger response, but I
        # don't know what it is and it's not needed to get the address.
        junk = os.urandom(64)
        offset = len(junk)

        resp = bytearray(
            offset.to_bytes(1, "big")
            + junk
            + b"("  # 40 chars/20 bytes?
            + account.address[2:].encode("utf-8")
        )

        return resp

    def _handle_tx_first_data(self, lc, data):
        path_length = data[0] * 4
        encoded_path = data[1 : path_length + 1]
        self.account = get_account_by_path(encoded_path)

        # Push this tx data onto the stack
        self.stack.append(data[path_length + 1 :])

        if len(data) < DATA_CHUNK_SIZE:
            encoded_tx = b"".join(self.stack)
            return self._sign_transaction(encoded_tx)

    def _handle_tx_secondary_data(self, lc, data):
        # Push this tx data onto the stack
        self.stack.append(data[:lc])

        if len(data) < DATA_CHUNK_SIZE:
            encoded_tx = b"".join(self.stack)
            return self._sign_transaction(encoded_tx)

    def _handle_message_first_data(self, lc, data):
        path_length = data[0] * 4
        path_end = path_length + 1
        encoded_path = data[1:path_end]
        self.account = get_account_by_path(encoded_path)

        # Message is preceeded by length in 4-byte chunk
        # message_length = struct.unpack(">I", data[path_end : path_end + 4])

        # Push this message data onto the stack
        self.stack.append(data[path_end + 4 :])

        if len(data) < DATA_CHUNK_SIZE:
            encoded = b"".join(self.stack)
            return self._sign_message(encoded)

    def _handle_message_secondary_data(self, lc, data):
        # Push this message data onto the stack
        self.stack.append(data[:lc])

        if len(data) < DATA_CHUNK_SIZE:
            encoded = b"".join(self.stack)
            return self._sign_message(encoded)

    def _handle_sign_typed(self, lc, data):
        path_length = data[0] * 4
        path_end = path_length + 1
        encoded_path = data[1:path_end]
        self.account = get_account_by_path(encoded_path)

        # Push this message data onto the stack
        payload = data[path_end:]
        domain_hash = payload[:32]
        message_hash = payload[32:]

        return self._sign_typed(domain_hash, message_hash)

    def exchange(self, apdu, timeout=20000):
        """Handle an exchange with the mock dongle."""
        cmd = apdu[:4]
        lc = apdu[4]
        data = apdu[5:]

        if cmd == b"\xe0\x06\x00\x00":
            return self._handle_get_configuration(lc, data)
        elif cmd == b"\xe0\x02\x00\x00":
            return self._handle_get_address(lc, data)
        elif cmd == b"\xe0\x04\x00\x00":
            return self._handle_tx_first_data(lc, data)
        elif cmd == b"\xe0\x04\x80\x00":
            return self._handle_tx_secondary_data(lc, data)
        elif cmd == b"\xe0\x08\x00\x00":
            return self._handle_message_first_data(lc, data)
        elif cmd == b"\xe0\x08\x80\x00":
            return self._handle_message_secondary_data(lc, data)
        elif cmd == b"\xe0\x0c\x00\x00":
            return self._handle_sign_typed(lc, data)
        else:
            raise ValueError(f"Unknown command {decode_hex(cmd)}")


class MockExceptionDongle(MockDongle):
    """MockDongle to cause errors."""

    exception: Exception

    def __init__(self, exception: Exception):
        """Initialize a mock dongle that raises an exception."""
        self._reset()
        self.exception = exception

    def exchange(self, apdu, timeout=20000):
        """Raise the exception."""
        raise self.exception

    def close(self):
        """Close the connection."""
        pass


def _get_mock_dongle():
    return MockDongle()


@pytest.fixture
def yield_dongle():
    """Yield a dongle for testing."""

    @contextmanager
    def yield_yield_dongle(exception: LedgerError | None = None):
        if exception is not None:
            dongle = MockExceptionDongle(exception=exception)
            yield dongle

        elif USE_REAL_DONGLE:
            dongle = getDongle(True)
            yield dongle
            # TODO: Figure out the below type error
            dongle.close()  # pyright: ignore

        else:
            yield _get_mock_dongle()

    return yield_yield_dongle
