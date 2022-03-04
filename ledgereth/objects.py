import rlp
from enum import IntEnum
from typing import List, Tuple

from eth_utils import encode_hex, to_checksum_address
from rlp.sedes import (
    BigEndianInt,
    Binary,
    CountableList,
    List as ListSedes,
    big_endian_int,
    binary,
)

from ledgereth.constants import DEFAULT_CHAIN_ID
from ledgereth.utils import is_bip32_path, is_bytes, parse_bip32_path


address = Binary.fixed_length(20, allow_empty=False)
access_list_sede_type = CountableList(
    ListSedes(
        [
            address,
            CountableList(BigEndianInt(32)),
        ]
    ),
)


class TransactionType(IntEnum):
    # Original and EIP-155
    LEGACY = 0
    # Access Lists
    EIP_2930 = 1
    # Transaction fee change to max fee and bribe
    EIP_1559 = 2

    def to_byte(self):
        return self.value.to_bytes(1, "big")


class ISO7816Command:
    def __init__(
        self,
        CLA: bytes,
        INS: bytes,
        P1: bytes,
        P2: bytes,
        Lc: bytes = None,
        Le: bytes = None,
        data: bytes = None,
    ):
        try:
            assert is_bytes(CLA)
            assert is_bytes(INS)
            assert is_bytes(P1)
            assert is_bytes(P2)
            assert is_bytes(Lc) or Lc is None
            assert is_bytes(Le) or Le is None
            assert is_bytes(data) or data is None
        except AssertionError:
            raise ValueError("Command parts must be type bytes")

        self.CLA = CLA
        self.INS = INS
        self.P1 = P1
        self.P2 = P2
        self.Lc = Lc or b"\x00"
        self.Le = Le
        self.data = data

    def set_data(self, data: bytes, Lc: bytes = None) -> None:
        self.data = data
        if len(self.data) > 255:
            # TODO: Warning?
            return
        if Lc is None:
            self.Lc = len(self.data).to_bytes(1, "big")
        else:
            self.Lc = Lc

    def encode(self) -> bytes:
        encoded = self.CLA + self.INS + self.P1 + self.P2
        if self.data is not None:
            if self.Lc is None:
                self.Lc = (len(self.data)).to_bytes(1, "big")
            encoded += self.Lc
            encoded += self.data
        else:
            encoded += self.Lc
        if self.Le is not None:
            encoded += self.Le
        return encoded

    def encode_hex(self) -> str:
        return self.encode().hex()


class LedgerAccount:
    def __init__(self, path, address):
        if not is_bip32_path(path):
            raise ValueError("Invalid BIP32 Ethereum path")

        self.path = path
        self.path_encoded = parse_bip32_path(path)
        self.address = to_checksum_address(address)


class Transaction(rlp.Serializable):
    """Unsigned legacy or EIP-155 transaction"""

    fields = [
        ("nonce", big_endian_int),
        ("gas_price", big_endian_int),
        ("gas_limit", big_endian_int),
        ("destination", address),
        ("amount", big_endian_int),
        ("data", binary),
        ("chain_id", big_endian_int),
        # Expected nine elements as part of EIP-155 transactions
        ("dummy1", big_endian_int),
        ("dummy2", big_endian_int),
    ]
    transaction_type = TransactionType.LEGACY

    def __init__(
        self,
        nonce: int,
        gas_price: int,
        gas_limit: int,
        destination: bytes,
        amount: int,
        data: bytes,
        chain_id: int = DEFAULT_CHAIN_ID,
        dummy1: int = 0,
        dummy2: int = 0,
    ):
        super().__init__(
            nonce,
            gas_price,
            gas_limit,
            destination,
            amount,
            data,
            chain_id,
            dummy1,
            dummy2,
        )

    def to_dict(self) -> dict:
        d = {}
        for name, _ in self.__class__._meta.fields:
            d[name] = getattr(self, name)
        return d


class Type1Transaction(rlp.Serializable):
    """An unsigned Type 1 transaction.

    Format spec:

    0x01 || rlp([chainId, nonce, gasPrice, gasLimit, destination, amount, data, accessList])
    """

    fields = [
        ("chain_id", big_endian_int),
        ("nonce", big_endian_int),
        ("gas_price", big_endian_int),
        ("gas_limit", big_endian_int),
        ("destination", address),
        ("amount", big_endian_int),
        ("data", binary),
        ("access_list", access_list_sede_type),
    ]
    transaction_type = TransactionType.EIP_2930

    def __init__(
        self,
        chain_id: int,
        nonce: int,
        gas_price: int,
        gas_limit: int,
        destination: bytes,
        amount: int,
        data: bytes,
        access_list: List[Tuple[bytes, List[int]]] = list(),
    ):
        super().__init__(
            chain_id,
            nonce,
            gas_price,
            gas_limit,
            destination,
            amount,
            data,
            access_list,
        )

    def to_dict(self) -> dict:
        d = {}
        for name, _ in self.__class__._meta.fields:
            d[name] = getattr(self, name)
        return d


class Type2Transaction(rlp.Serializable):
    """An unsigned Type 2 transaction.

    Format spec:

    0x02 || rlp([chain_id, nonce, max_priority_fee_per_gas, max_fee_per_gas, gas_limit, destination, amount, data, access_list])
    """

    fields = [
        ("chain_id", big_endian_int),
        ("nonce", big_endian_int),
        ("max_priority_fee_per_gas", big_endian_int),
        ("max_fee_per_gas", big_endian_int),
        ("gas_limit", big_endian_int),
        ("destination", address),
        ("amount", big_endian_int),
        ("data", binary),
        ("access_list", access_list_sede_type),
    ]
    transaction_type = TransactionType.EIP_1559

    def __init__(
        self,
        chain_id: int,
        nonce: int,
        max_priority_fee_per_gas: int,
        max_fee_per_gas: int,
        gas_limit: int,
        destination: bytes,
        amount: int,
        data: bytes,
        access_list: List[Tuple[bytes, List[int]]] = list(),
    ):
        super().__init__(
            chain_id,
            nonce,
            max_priority_fee_per_gas,
            max_fee_per_gas,
            gas_limit,
            destination,
            amount,
            data,
            access_list,
        )

    def to_dict(self) -> dict:
        d = {}
        for name, _ in self.__class__._meta.fields:
            d[name] = getattr(self, name)
        return d


class SignedTransaction(rlp.Serializable):
    """Signed legacy or EIP-155 transaction"""

    fields = [
        ("nonce", big_endian_int),
        ("gas_price", big_endian_int),
        ("gas_limit", big_endian_int),
        ("destination", address),
        ("amount", big_endian_int),
        ("data", binary),
        ("v", big_endian_int),
        ("r", big_endian_int),
        ("s", big_endian_int),
    ]
    transaction_type = TransactionType.LEGACY

    def __init__(
        self,
        nonce: int,
        gas_price: int,
        gas_limit: int,
        destination: bytes,
        amount: int,
        data: bytes,
        v: int,
        r: int,
        s: int,
    ):
        super().__init__(
            nonce, gas_price, gas_limit, destination, amount, data, v, r, s
        )

    def to_dict(self) -> dict:
        d = {}
        for name, _ in self.__class__._meta.fields:
            d[name] = getattr(self, name)
        return d

    def raw_transaction(self):
        return encode_hex(rlp.encode(self, SignedTransaction))

    # Match the API of the web3.py Transaction object
    rawTransaction = property(raw_transaction)


class SignedType1Transaction(rlp.Serializable):
    """A signed Type 1 transaction.

    Format spec:

    0x01 || rlp([chainId, nonce, gasPrice, gasLimit, destination, amount, data, accessList, signatureYParity, signatureR, signatureS])
    """

    fields = [
        ("chain_id", big_endian_int),
        ("nonce", big_endian_int),
        ("gas_price", big_endian_int),
        ("gas_limit", big_endian_int),
        ("destination", address),
        ("amount", big_endian_int),
        ("data", binary),
        ("access_list", access_list_sede_type),
        ("y_parity", big_endian_int),
        ("sender_r", big_endian_int),
        ("sender_s", big_endian_int),
    ]
    transaction_type = TransactionType.EIP_2930

    def __init__(
        self,
        chain_id: int,
        nonce: int,
        gas_price: int,
        gas_limit: int,
        destination: bytes,
        amount: int,
        data: bytes,
        access_list: List[Tuple[bytes, List[int]]],
        y_parity: int,
        sender_r: int,
        sender_s: int,
    ):
        super().__init__(
            chain_id,
            nonce,
            gas_price,
            gas_limit,
            destination,
            amount,
            data,
            access_list,
            y_parity,
            sender_r,
            sender_s,
        )

    def to_dict(self) -> dict:
        d = {}
        for name, _ in self.__class__._meta.fields:
            d[name] = getattr(self, name)
        return d

    def raw_transaction(self):
        return encode_hex(b"\x02" + rlp.encode(self, SignedType2Transaction))

    # Match the API of the web3.py Transaction object
    rawTransaction = property(raw_transaction)


class SignedType2Transaction(rlp.Serializable):
    """A signed Type 2 transaction.

    Format spec:

    0x02 || rlp([chain_id, nonce, max_priority_fee_per_gas, max_fee_per_gas, gas_limit, destination, amount, data, access_list, signature_y_parity, signature_r, signature_s])
    """

    fields = [
        ("chain_id", big_endian_int),
        ("nonce", big_endian_int),
        ("max_priority_fee_per_gas", big_endian_int),
        ("max_fee_per_gas", big_endian_int),
        ("gas_limit", big_endian_int),
        ("destination", address),
        ("amount", big_endian_int),
        ("data", binary),
        ("access_list", access_list_sede_type),
        ("y_parity", big_endian_int),
        ("sender_r", big_endian_int),
        ("sender_s", big_endian_int),
    ]
    transaction_type = TransactionType.EIP_1559

    def __init__(
        self,
        chain_id: int,
        nonce: int,
        max_priority_fee_per_gas: int,
        max_fee_per_gas: int,
        gas_limit: int,
        destination: bytes,
        amount: int,
        data: bytes,
        access_list: List[Tuple[bytes, List[int]]],
        y_parity: int,
        sender_r: int,
        sender_s: int,
    ):
        super().__init__(
            chain_id,
            nonce,
            max_priority_fee_per_gas,
            max_fee_per_gas,
            gas_limit,
            destination,
            amount,
            data,
            access_list,
            y_parity,
            sender_r,
            sender_s,
        )

    def to_dict(self) -> dict:
        d = {}
        for name, _ in self.__class__._meta.fields:
            d[name] = getattr(self, name)
        return d

    def raw_transaction(self):
        return encode_hex(b"\x02" + rlp.encode(self, SignedType2Transaction))

    # Match the API of the web3.py Transaction object
    rawTransaction = property(raw_transaction)


# Compat: Depreciated
RLPTx = Transaction
RLPSignedTx = SignedTransaction
