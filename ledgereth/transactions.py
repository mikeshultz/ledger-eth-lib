import binascii
from typing import Any, Union

from eth_utils import decode_hex
from rlp import Serializable, encode

from ledgereth.comms import chunks, dongle_send_data, init_dongle
from ledgereth.constants import CHAIN_ID, DEFAULT_PATH_STRING
from ledgereth.objects import SignedTransaction, Transaction
from ledgereth.utils import is_bip32_path, is_hex_string, parse_bip32_path

Text = Union[str, bytes]


def sign_transaction(
    tx: Serializable, sender_path: str = DEFAULT_PATH_STRING, dongle: Any = None
) -> SignedTransaction:
    """Sign a transaction object (rlp.Serializable)"""
    dongle = init_dongle(dongle)
    retval = None

    assert isinstance(
        tx, Transaction
    ), "Only Transaction objects are currently supported"
    print("tx: ", tx)
    encoded_tx = encode(tx, Transaction)

    if not is_bip32_path(sender_path):
        raise ValueError("Invalid sender BIP32 path given to sign_transaction")

    path = parse_bip32_path(sender_path)
    payload = (len(path) // 4).to_bytes(1, "big") + path + encoded_tx

    chunk_count = 0
    for chunk in chunks(payload):
        chunk_size = len(chunk)
        if chunk_count == 0:
            retval = dongle_send_data(
                dongle, "SIGN_TX_FIRST_DATA", chunk, Lc=chunk_size.to_bytes(1, "big")
            )
        else:
            retval = dongle_send_data(
                dongle,
                "SIGN_TX_SECONDARY_DATA",
                chunk,
                Lc=chunk_size.to_bytes(1, "big"),
            )
        chunk_count += 1

    if retval is None or len(retval) < 64:
        raise Exception("Invalid response from Ledger")

    if (CHAIN_ID * 2 + 35) + 1 > 255:
        ecc_parity = retval[0] - ((CHAIN_ID * 2 + 35) % 256)
        v = (CHAIN_ID * 2 + 35) + ecc_parity
    else:
        v = retval[0]

    r = int(binascii.hexlify(retval[1:33]), 16)
    s = int(binascii.hexlify(retval[33:65]), 16)

    return SignedTransaction(
        nonce=tx.nonce,
        gasprice=tx.gasprice,
        startgas=tx.startgas,
        to=tx.to,
        value=tx.value,
        data=tx.data,
        v=v,
        r=r,
        s=s,
    )


def create_transaction(
    to: bytes,
    value: int,
    gas: int,
    gas_price: int,
    nonce: int,
    data: Text,
    sender_path: str = DEFAULT_PATH_STRING,
    dongle: Any = None,
) -> SignedTransaction:
    """Create and sign a transaction from indiv args"""
    dongle = init_dongle(dongle)

    if not is_hex_string(data):
        data = decode_hex(data) or b""

    # Create a serializable tx object
    tx = Transaction(
        to=decode_hex(to),
        value=value,
        startgas=gas,
        gasprice=gas_price,
        data=data,
        nonce=nonce,
    )

    return sign_transaction(tx, sender_path, dongle=dongle)
