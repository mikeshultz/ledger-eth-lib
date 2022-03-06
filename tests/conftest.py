import os
from contextlib import contextmanager

import pytest
from eth_account.account import Account
from eth_utils import decode_hex, encode_hex
from ledgerblue.comm import getDongle

from ledgereth.constants import DATA_CHUNK_SIZE, MAGIC_NUMBER
from ledgereth.transactions import decode_transaction
from ledgereth.utils import decode_bip32_path

TEST_MNEMONIC = "test test test test test test test test test test test junk"
USE_REAL_DONGLE = os.environ.get("USE_REAL_DONGLE") is not None

# We must enable HD account derivation for eth_account while it's experimental
Account.enable_unaudited_hdwallet_features()


def get_account_by_path(path: bytes) -> Account:
    """Get a test account by derivation path"""
    path_string = decode_bip32_path(path)
    return Account.from_mnemonic(TEST_MNEMONIC, account_path=f"m/{path_string}")


class MockDongle:
    """Attempts to act like an actual Ledger dongle for the sake of not
    requiring user-intervention for every single test with a real ledger
    attached.
    """

    def __init__(self):
        self._reset()

    def _reset(self):
        self.account = None
        self.stack = []

    def _sign_transaction(self, encoded_tx):
        """Sign transaction data sent to the Ledger"""
        tx = decode_transaction(encoded_tx)
        resp = self.account.sign_transaction(tx.to_rpc_dict())

        """TODO: It's been a long day ad I feel like I'm losing my shit. I
        thought I knew how v and y worked but now I'm fudging these numbers to
        match what is expected from the Ledger and I'm not entirely sure why.
        Should revisit this at some point.
        """
        if (tx.chain_id * 2 + 35) + 1 > 255:
            ledger_v = resp.v - MAGIC_NUMBER
        elif resp.v > 1:
            ledger_v = (tx.chain_id * 2 + 35) + (resp.v - MAGIC_NUMBER)
        else:
            ledger_v = resp.v

        v = ledger_v.to_bytes(1, "big")
        r = resp.r.to_bytes(32, "big")
        s = resp.s.to_bytes(32, "big")

        # Reset the stack and account MockLegder working with
        self._reset()

        return bytearray(v + r + s)

    def handle_get_configuration(self, lc, data):
        # Return version 9.9.9
        return bytearray(b"\x00\x09\x09\x09")

    def handle_get_address(self, lc, data):
        # First byte is len(path) // 4
        encoded_path = data[1 : lc + 1]
        account = get_account_by_path(encoded_path)
        path = decode_bip32_path(encoded_path)

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

    def handle_tx_first_data(self, lc, data):
        path_length = data[0] * 4
        encoded_path = data[1 : path_length + 1]
        self.account = get_account_by_path(encoded_path)

        # Push this tx data onto the stack
        self.stack.append(data[path_length + 1 :])

        if len(data) < DATA_CHUNK_SIZE:
            encoded_tx = b"".join(self.stack)
            return self._sign_transaction(encoded_tx)

    def handle_tx_secondary_data(self, lc, data):
        # Push this tx data onto the stack
        self.stack.append(data[:lc])

        if len(data) < DATA_CHUNK_SIZE:
            encoded_tx = b"".join(self.stack)
            return self._sign_transaction(encoded_tx)

    def exchange(self, apdu, timeout=20000):
        cmd = apdu[:4]
        lc = apdu[4]
        data = apdu[5:]

        if cmd == b"\xe0\x06\x00\x00":
            return self.handle_get_configuration(lc, data)
        elif cmd == b"\xe0\x02\x00\x00":
            return self.handle_get_address(lc, data)
        elif cmd == b"\xe0\x04\x00\x00":
            return self.handle_tx_first_data(lc, data)
        elif cmd == b"\xe0\x04\x80\x00":
            return self.handle_tx_secondary_data(lc, data)
        else:
            raise ValueError(f"Unknown command {decode_hex(cmd)}")


def getMockDongle():
    return MockDongle()


@pytest.fixture
def yield_dongle():
    @contextmanager
    def yield_yield_dongle():
        if USE_REAL_DONGLE:
            dongle = getDongle(True)
            yield dongle
            dongle.close()
        else:
            yield getMockDongle()

    return yield_yield_dongle
