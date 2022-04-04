import binascii
import struct
from typing import Optional, Union

from ledgereth.comms import Dongle, dongle_send_data, init_dongle
from ledgereth.constants import DATA_CHUNK_SIZE, DEFAULT_CHAIN_ID, DEFAULT_PATH_STRING
from ledgereth.objects import SignedMessage, SignedTypedMessage
from ledgereth.utils import (
    chunks,
    coerce_access_list,
    is_bip32_path,
    is_hex_string,
    parse_bip32_path,
)

AnyText = Union[str, bytes]


def sign_message(
    message: AnyText,
    sender_path: str = DEFAULT_PATH_STRING,
    dongle: Optional[Dongle] = None,
) -> SignedMessage:
    """Sign a simple text message.  Message will be prefixed by the Ethereum
    app on the Ledger device according to `EIP-191`_.

    :param message: (:code:`str|bytes`) - A bit of text to sign
    :param sender_path: (:code:`str`) - HID derivation path for the account to
        sign with.
    :param dongle: (:class:`ledgerblue.Dongle.Dongle`) - The Web3 instance to use
    :return: :class:`ledgereth.objects.SignedMessage`

    .. _`EIP-191`: https://eips.ethereum.org/EIPS/eip-191
    """
    given_dongle = dongle is not None
    dongle = init_dongle(dongle)
    retval = None

    if type(message) == str:
        message = message.encode("utf-8")

    # Silence mypy due to type cohersion above
    assert type(message) == bytes

    encoded = struct.pack(">I", len(message))
    encoded += message

    if not is_bip32_path(sender_path):
        raise ValueError("Invalid sender BIP32 path given to sign_transaction")

    path = parse_bip32_path(sender_path)
    payload = (len(path) // 4).to_bytes(1, "big") + path + encoded

    chunk_count = 0
    for chunk in chunks(payload, DATA_CHUNK_SIZE):
        chunk_size = len(chunk)

        if chunk_count == 0:
            retval = dongle_send_data(
                dongle,
                "SIGN_MESSAGE_FIRST_DATA",
                chunk,
                Lc=chunk_size.to_bytes(1, "big"),
            )
        else:
            retval = dongle_send_data(
                dongle,
                "SIGN_MESSAGE_SECONDARY_DATA",
                chunk,
                Lc=chunk_size.to_bytes(1, "big"),
            )
        chunk_count += 1

    if retval is None or len(retval) < 64:
        raise Exception("Invalid response from Ledger")

    v = int(retval[0])
    r = int(binascii.hexlify(retval[1:33]), 16)
    s = int(binascii.hexlify(retval[33:65]), 16)

    signed = SignedMessage(message, v, r, s)

    # If this func inited the dongle, then close it, otherwise core dump
    if not given_dongle:
        dongle.close()

    return signed


def sign_typed_data_draft(
    domain_hash: AnyText,
    message_hash: AnyText,
    sender_path: str = DEFAULT_PATH_STRING,
    dongle: Optional[Dongle] = None,
) -> SignedTypedMessage:
    """Sign `EIP-721`_ typed data.

    .. DANGER::
        EIP-712 is still in DRAFT status and APIs may change, including the
        Ledger app-ethereum implementation.

    :param domain_hash: (:code:`str`) - Hash of the EIP-712 domain
    :param message_hash: (:code:`str`) - Hash of the message
    :param sender_path: (:code:`str`) - HID derivation path for the account to
        sign with. Defaults to first account in the derivation path.
    :param dongle: (:class:`ledgerblue.Dongle.Dongle`) -  The Dongle instance to
        use to communicate with the Ledger device
    :return: :class:`ledgereth.objects.SignedTypedMessage` Signed message object

    For a real example of usage, see how this is used with `eth_account`_ in
    `ledgereth's unit tests`_.

    .. _`EIP-721`: https://eips.ethereum.org/EIPS/eip-712
    .. _`eth_account`: https://eth-account.readthedocs.io/
    .. _`ledgereth's unit tests`: https://github.com/mikeshultz/ledger-eth-lib/blob/2e47e7b9d70136a6dda0229c7bf516ed6bbe850f/tests/test_message_signing.py#L55-L74
    """

    given_dongle = dongle is not None
    dongle = init_dongle(dongle)
    retval = None

    if type(domain_hash) == str:
        domain_hash = domain_hash.encode("utf-8")
    if type(message_hash) == str:
        message_hash = message_hash.encode("utf-8")

    # Silence mypy due to type cohersion above
    assert type(domain_hash) == bytes
    assert type(message_hash) == bytes

    encoded = domain_hash + message_hash

    if not is_bip32_path(sender_path):
        raise ValueError("Invalid sender BIP32 path given to sign_transaction")

    path = parse_bip32_path(sender_path)
    payload = (len(path) // 4).to_bytes(1, "big") + path + encoded

    retval = dongle_send_data(
        dongle,
        "SIGN_TYPED_DATA",
        payload,
        Lc=len(payload).to_bytes(1, "big"),
    )

    if retval is None or len(retval) < 64:
        raise Exception("Invalid response from Ledger")

    v = int(retval[0])
    r = int(binascii.hexlify(retval[1:33]), 16)
    s = int(binascii.hexlify(retval[33:65]), 16)

    signed = SignedTypedMessage(domain_hash, message_hash, v, r, s)

    # If this func inited the dongle, then close it, otherwise core dump
    if not given_dongle:
        dongle.close()

    return signed
