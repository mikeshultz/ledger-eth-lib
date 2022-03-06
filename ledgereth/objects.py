from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum
from typing import List, Tuple

from eth_utils import encode_hex, to_checksum_address
from rlp import Serializable, decode, encode
from rlp.sedes import BigEndianInt, Binary, CountableList
from rlp.sedes import List as ListSedes
from rlp.sedes import big_endian_int, binary

from ledgereth.constants import DEFAULT_CHAIN_ID
from ledgereth.utils import coerce_list_types, is_bip32_path, is_bytes, parse_bip32_path

address = Binary.fixed_length(20, allow_empty=False)
access_list_sede_type = CountableList(
    ListSedes(
        [
            address,
            CountableList(BigEndianInt(32)),
        ]
    ),
)
RPC_TX_PROP_TRANSLATION = {
    "gas_price": "gasPrice",
    "gas_limit": "gas",
    "amount": "value",
    "destination": "to",
    "max_priority_fee_per_gas": "maxPriorityFeePerGas",
    "max_fee_per_gas": "maxFeePerGas",
}
RPC_TX_PROPS = [
    "from",
    "to",
    "gas",
    "gasPrice",
    "value",
    "data",
    "nonce",
    "maxFeePerGas",
    "maxPriorityFeePerGas",
    "chainId",
]


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


class SerializableTransaction(Serializable):
    @classmethod
    @abstractmethod
    def from_rawtx(cls, rawtx: bytes) -> SerializableTransaction:
        """Instantiates a SerializableTransaction given a raw encoded
        transaction"""
        pass

    def to_dict(self) -> dict:
        d = {}
        for name, _ in self.__class__._meta.fields:
            d[name] = getattr(self, name)
        return d

    def to_rpc_dict(self) -> dict:
        """To a dict compatible with web3.py"""
        d = {}
        for name, _ in self.__class__._meta.fields:
            key = (
                RPC_TX_PROP_TRANSLATION[name]
                if name in RPC_TX_PROP_TRANSLATION
                else name
            )
            if key in RPC_TX_PROPS:
                d[key] = getattr(self, name)
        return d


class Transaction(SerializableTransaction):
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

    @classmethod
    def from_rawtx(cls, rawtx: bytes) -> Transaction:
        """Instantiate a Transaction object from a raw encoded transaction"""
        if rawtx[0] < 127:
            raise ValueError("Transaction is not a legacy transaction")

        return Transaction(
            *coerce_list_types(
                [int, int, int, bytes, int, bytes, int, int, int], decode(rawtx)
            )
        )


class Type1Transaction(SerializableTransaction):
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

    @classmethod
    def from_rawtx(cls, rawtx: bytes) -> Type1Transaction:
        """Instantiate a Type1Transaction object from a raw encoded transaction"""
        if rawtx[0] != cls.transaction_type:
            raise ValueError(
                f"Transaction is not a type {cls.transaction_type} transaction"
            )

        return Type1Transaction(
            *coerce_list_types(
                [int, int, int, int, bytes, int, bytes, None],
                decode(rawtx[1:]),
            )
        )


class Type2Transaction(SerializableTransaction):
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

    @classmethod
    def from_rawtx(cls, rawtx: bytes) -> Type2Transaction:
        """Instantiate a Type2Transaction object from a raw encoded transaction"""
        if rawtx[0] != cls.transaction_type:
            raise ValueError(
                f"Transaction is not a type {cls.transaction_type} transaction"
            )

        return Type2Transaction(
            *coerce_list_types(
                [int, int, int, int, int, bytes, int, bytes, None],
                decode(rawtx[1:]),
            )
        )


class SignedTransaction(SerializableTransaction):
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

    @classmethod
    def from_rawtx(cls, rawtx: bytes) -> SignedTransaction:
        """Instantiate a SignedTransaction object from a raw encoded transaction"""
        if rawtx[0] < 127:
            raise ValueError("Transaction is not a legacy transaction")

        return SignedTransaction(
            *coerce_list_types([int, int, int, int, bytes, int, bytes], decode(rawtx))
        )

    def raw_transaction(self):
        return encode_hex(encode(self, SignedTransaction))

    # Match the API of the web3.py Transaction object
    rawTransaction = property(raw_transaction)


class SignedType1Transaction(SerializableTransaction):
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

    @classmethod
    def from_rawtx(cls, rawtx: bytes) -> SignedType1Transaction:
        """Instantiate a SignedType1Transaction object from a raw encoded transaction"""
        if rawtx[0] != cls.transaction_type:
            raise ValueError(
                f"Transaction is not a type {cls.transaction_type} transaction"
            )

        return SignedType1Transaction(
            *coerce_list_types(
                [int, int, int, int, bytes, int, bytes, None, int, int, int],
                decode(rawtx[1:]),
            )
        )

    def raw_transaction(self):
        return encode_hex(b"\x02" + encode(self, SignedType1Transaction))

    # Match the API of the web3.py Transaction object
    rawTransaction = property(raw_transaction)


class SignedType2Transaction(SerializableTransaction):
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

    @classmethod
    def from_rawtx(cls, rawtx: bytes) -> SignedType2Transaction:
        """Instantiate a SignedType2Transaction object from a raw encoded transaction"""
        if rawtx[0] != cls.transaction_type:
            raise ValueError(
                f"Transaction is not a type {cls.transaction_type} transaction"
            )

        return SignedType2Transaction(
            *coerce_list_types(
                [
                    int,
                    int,
                    int,
                    int,
                    int,
                    bytes,
                    int,
                    bytes,
                    None,
                    int,
                    int,
                    int,
                ],
                decode(rawtx[1:]),
            )
        )

    def raw_transaction(self):
        return encode_hex(b"\x02" + encode(self, SignedType2Transaction))

    # Match the API of the web3.py Transaction object
    rawTransaction = property(raw_transaction)
