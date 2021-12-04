import rlp
from eth_utils import encode_hex, to_checksum_address
from rlp.sedes import Binary, big_endian_int, binary

from ledgereth.utils import is_bip32_path, is_bytes, parse_bip32_path


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
    fields = [
        ("nonce", big_endian_int),
        ("gasprice", big_endian_int),
        ("startgas", big_endian_int),
        ("to", Binary.fixed_length(20, allow_empty=True)),
        ("value", big_endian_int),
        ("data", binary),
    ]

    def __init__(
        self, nonce: int, gasprice: int, startgas: int, to: bytes, value: int, data: str
    ):
        super(RLPTx, self).__init__(nonce, gasprice, startgas, to, value, data)

    def sender(self, value: str) -> None:
        self._sender = value

    def to_dict(self) -> dict:
        d = {}
        for name, _ in self.__class__._meta.fields:
            d[name] = getattr(self, name)
        return d


class SignedTransaction(rlp.Serializable):
    fields = [
        ("nonce", big_endian_int),
        ("gasprice", big_endian_int),
        ("startgas", big_endian_int),
        ("to", Binary.fixed_length(20, allow_empty=True)),
        ("value", big_endian_int),
        ("data", binary),
        ("v", big_endian_int),
        ("r", big_endian_int),
        ("s", big_endian_int),
    ]

    def __init__(
        self,
        nonce: int,
        gasprice: int,
        startgas: int,
        to: bytes,
        value: int,
        data: str,
        v: int,
        r: int,
        s: int,
    ):
        super().__init__(nonce, gasprice, startgas, to, value, data, v, r, s)

    def sender(self, value: str) -> None:
        self._sender = value

    def to_dict(self) -> dict:
        d = {}
        for name, _ in self.__class__._meta.fields:
            d[name] = getattr(self, name)
        return d

    def raw_transaction(self):
        return encode_hex(rlp.encode(self, SignedTransaction))

    # Match the API of the web3.py Transaction object
    rawTransaction = property(raw_transaction)


# Compat: Depreciated
RLPTx = Transaction
RLPSignedTx = SignedTransaction
