import binascii
from typing import Any, List, Optional, Tuple, Union

from eth_utils import decode_hex
from rlp import Serializable, encode

from ledgereth.comms import chunks, dongle_send_data, init_dongle
from ledgereth.constants import DEFAULT_CHAIN_ID, DEFAULT_PATH_STRING
from ledgereth.objects import (
    SignedTransaction,
    SignedType1Transaction,
    SignedType2Transaction,
    Transaction,
    TransactionType,
    Type1Transaction,
    Type2Transaction,
)
from ledgereth.utils import is_bip32_path, is_hex_string, parse_bip32_path

Text = Union[str, bytes]


def coerce_access_list(access_list):
    """validate and type coerce an access list"""
    if access_list is None:
        return []

    if type(access_list) != list:
        raise ValueError("Expected access_list to be a list")

    for i, rule in enumerate(access_list):
        if type(rule) not in (list, tuple):
            raise ValueError("Expected access_list rules to be a list or tuple")

        if type(rule) == tuple:
            access_list[i] = list(rule)

        target, slots = rule

        if is_hex_string(target):
            access_list[i][0] = decode_hex(target)
        elif type(target) != bytes:
            raise ValueError(
                f"Unexpected type ({type(target)}) for access_list address at index {i}"
            )

        for j, slot in enumerate(slots):
            if is_hex_string(slot):
                access_list[i][1][j] = int(slot, 16)
            elif type(slot) != int:
                raise ValueError(
                    f"Unexpected type ({type(slot)}) for access_list slot at index {j}"
                )

    return access_list


def sign_transaction(
    tx: Serializable,
    sender_path: str = DEFAULT_PATH_STRING,
    dongle: Any = None,
) -> SignedTransaction:
    """Sign a transaction object (rlp.Serializable)"""
    given_dongle = dongle is not None
    dongle = init_dongle(dongle)
    retval = None

    if isinstance(tx, Transaction):
        encoded_tx = encode(tx, Transaction)
    elif isinstance(tx, Type1Transaction):
        encoded_tx = tx.transaction_type.to_byte() + encode(
            tx, Type1Transaction
        )
    elif isinstance(tx, Type2Transaction):
        encoded_tx = tx.transaction_type.to_byte() + encode(
            tx, Type2Transaction
        )
    else:
        raise ValueError(
            "Only Transaction and Type2Transaction objects are currently supported"
        )

    if not is_bip32_path(sender_path):
        raise ValueError("Invalid sender BIP32 path given to sign_transaction")

    path = parse_bip32_path(sender_path)
    payload = (len(path) // 4).to_bytes(1, "big") + path + encoded_tx

    chunk_count = 0
    for chunk in chunks(payload):
        chunk_size = len(chunk)
        if chunk_count == 0:
            retval = dongle_send_data(
                dongle,
                "SIGN_TX_FIRST_DATA",
                chunk,
                Lc=chunk_size.to_bytes(1, "big"),
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

    chain_id = tx.chain_id or DEFAULT_CHAIN_ID
    r = int(binascii.hexlify(retval[1:33]), 16)
    s = int(binascii.hexlify(retval[33:65]), 16)

    if tx.transaction_type < TransactionType.EIP_2930:
        if (chain_id * 2 + 35) + 1 > 255:
            ecc_parity = retval[0] - ((chain_id * 2 + 35) % 256)
            v = (chain_id * 2 + 35) + ecc_parity
        else:
            v = retval[0]

        signed = SignedTransaction(
            nonce=tx.nonce,
            gas_price=tx.gas_price,
            gas_limit=tx.gas_limit,
            destination=tx.destination,
            amount=tx.amount,
            data=tx.data,
            v=v,
            r=r,
            s=s,
        )
    else:
        y_parity = retval[0]

        if tx.transaction_type == TransactionType.EIP_2930:
            signed = SignedType1Transaction(
                chain_id=tx.chain_id,
                nonce=tx.nonce,
                gas_limit=tx.gas_limit,
                destination=tx.destination,
                amount=tx.amount,
                data=tx.data,
                gas_price=tx.gas_price,
                access_list=tx.access_list,
                y_parity=y_parity,
                sender_r=r,
                sender_s=s,
            )
        else:
            signed = SignedType2Transaction(
                chain_id=tx.chain_id,
                nonce=tx.nonce,
                gas_limit=tx.gas_limit,
                destination=tx.destination,
                amount=tx.amount,
                data=tx.data,
                max_priority_fee_per_gas=tx.max_priority_fee_per_gas,
                max_fee_per_gas=tx.max_fee_per_gas,
                access_list=tx.access_list,
                y_parity=y_parity,
                sender_r=r,
                sender_s=s,
            )

    # If this func inited the dongle, it close it, otherwise core dump
    if not given_dongle:
        dongle.close()

    return signed


def create_transaction(
    destination: Text,
    amount: int,
    gas: int,
    nonce: int,
    data: Text = b"",
    gas_price: int = 0,
    max_priority_fee_per_gas: int = 0,
    max_fee_per_gas: int = 0,
    chain_id: int = DEFAULT_CHAIN_ID,
    sender_path: str = DEFAULT_PATH_STRING,
    access_list: Optional[List[Tuple[bytes, List[int]]]] = None,
    dongle: Any = None,
) -> SignedTransaction:
    """Create and sign a transaction from indiv args"""
    given_dongle = dongle is not None
    dongle = init_dongle(dongle)

    if is_hex_string(destination):
        destination = decode_hex(destination)

    if not data:
        data = b""
    elif is_hex_string(data):
        data = decode_hex(data)

    # EIP-1559 transactions should never have gas_price
    if gas_price and (max_priority_fee_per_gas or max_fee_per_gas):
        raise ValueError(
            "gas_price is incompatible with max_priority_fee_per_gas and max_fee_per_gas"
        )

    # we need a gas price for a valid transaction
    if not gas_price and not max_fee_per_gas:
        raise ValueError("gas_price or max_fee_per_gas must be provided")

    # Create a serializable tx object
    if max_fee_per_gas:
        tx = Type2Transaction(
            destination=destination,
            amount=amount,
            gas_limit=gas,
            data=data,
            nonce=nonce,
            chain_id=chain_id,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
            max_fee_per_gas=max_fee_per_gas,
            access_list=coerce_access_list(access_list),
        )
    elif access_list is not None:
        tx = Type1Transaction(
            destination=destination,
            amount=amount,
            gas_limit=gas,
            data=data,
            nonce=nonce,
            chain_id=chain_id,
            gas_price=gas_price,
            access_list=coerce_access_list(access_list),
        )
    else:
        tx = Transaction(
            destination=destination,
            amount=amount,
            gas_limit=gas,
            gas_price=gas_price,
            data=data,
            nonce=nonce,
            chain_id=chain_id,
        )

    signed = sign_transaction(tx, sender_path, dongle=dongle)

    # If this func inited the dongle, it close it, otherwise core dump
    if not given_dongle:
        dongle.close()

    return signed
