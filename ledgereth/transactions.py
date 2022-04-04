import binascii
from typing import List, Optional, Tuple, Union

from eth_utils import decode_hex
from rlp import Serializable, encode

from ledgereth.comms import Dongle, dongle_send_data, init_dongle
from ledgereth.constants import DATA_CHUNK_SIZE, DEFAULT_CHAIN_ID, DEFAULT_PATH_STRING
from ledgereth.objects import (
    SerializableTransaction,
    SignedTransaction,
    SignedType1Transaction,
    SignedType2Transaction,
    Transaction,
    TransactionType,
    Type1Transaction,
    Type2Transaction,
)
from ledgereth.utils import (
    chunks,
    coerce_access_list,
    is_bip32_path,
    is_hex_string,
    parse_bip32_path,
)

Text = Union[str, bytes]


def sign_transaction(
    tx: Serializable,
    sender_path: str = DEFAULT_PATH_STRING,
    dongle: Optional[Dongle] = None,
) -> SignedTransaction:
    """Sign a :class:`rlp.Serializable` transaction object.  Compatible with
    ledgereth and web3.py transaction objects.

    :param tx: (:class:`rlp.Serializable`) - Serializable transaction object to
        sign
    :param sender_path: (:code:`str`) - HID derivation path for the account to
        sign with. Defaults to first account in the derivation path.
    :param dongle: (:class:`ledgerblue.Dongle.Dongle`) -  The Dongle instance to
        use to communicate with the Ledger device
    :return: :class:`ledgereth.objects.SignedTransaction` instance for
        transaction
    """
    given_dongle = dongle is not None
    dongle = init_dongle(dongle)
    retval = None

    if isinstance(tx, Transaction):
        encoded_tx = encode(tx, Transaction)
    elif isinstance(tx, Type1Transaction):
        encoded_tx = tx.transaction_type.to_byte() + encode(tx, Type1Transaction)
    elif isinstance(tx, Type2Transaction):
        encoded_tx = tx.transaction_type.to_byte() + encode(tx, Type2Transaction)
    else:
        raise ValueError(
            "Only Transaction and Type2Transaction objects are currently supported"
        )

    if not is_bip32_path(sender_path):
        raise ValueError("Invalid sender BIP32 path given to sign_transaction")

    path = parse_bip32_path(sender_path)
    payload = (len(path) // 4).to_bytes(1, "big") + path + encoded_tx

    chunk_count = 0
    for chunk in chunks(payload, DATA_CHUNK_SIZE):
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

    # If this func inited the dongle, then close it, otherwise core dump
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
    access_list: Optional[List[Tuple[Union[bytes, str], List[int]]]] = None,
    dongle: Optional[Dongle] = None,
) -> SignedTransaction:
    """Create and sign a transaction from given arguments.

    :param destination: (:code:`str|bytes`) - Destination address (AKA :code:`to`)
    :param amount: (:code:`int`) - Transaction value in wei
    :param gas: (:code:`int`) - Gas limit for the transaction
    :param nonce: (:code:`int`) - Nonce for the transaction
    :param data: (:code:`str|bytes`) - Transaction data (e.g. contract calldata)
    :param gas_price: (:code:`int`) - Gas price in wei to use for the
        transaction.  This is not compatible with :code:`max_fee_per_gas`.
    :param max_priority_fee_per_gas: (:code:`int`) - Priority fee per gas (in
        wei) to provide to the miner of the block.
    :param max_fee_per_gas: (:code:`int`) - Maximum fee in wei to pay for the
        transaction.  This is not compatible with :code:`gas_price`.
    :param chain_id: (:code:`int`) - Chain ID to limit the transaction to.
        Defaults to :code:`1`.
    :param sender_path: (:code:`str`) - `BIP-44`_ HD derivation path for the
        account to sign with. Defaults to first account in the default
        derivation path.
    :param access_list: (:code:`List[Tuple[bytes, List[int]]]`) -
        `EIP-2930`_ access list to use for the transaction.
    :param dongle: (:class:`ledgerblue.Dongle.Dongle`) -  The Dongle instance to
        use to communicate with the Ledger device
    :return: :class:`ledgereth.objects.SignedTransaction` instance for transaction

    .. _`BIP-44`: https://en.bitcoin.it/wiki/BIP_0044
    .. _`EIP-2930`: https://eips.ethereum.org/EIPS/eip-2930
    """
    given_dongle = dongle is not None
    dongle = init_dongle(dongle)

    if type(destination) == str and is_hex_string(destination):
        destination = decode_hex(destination)

    if not data:
        data = b""
    elif type(data) == str and is_hex_string(data):
        data = decode_hex(data)

    # be cool mypy
    assert type(destination) == bytes
    assert type(data) == bytes

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

    # If this func inited the dongle, then close it, otherwise core dump
    if not given_dongle:
        dongle.close()

    return signed


def decode_transaction(rawtx: bytes, signed: bool = False) -> SerializableTransaction:
    """Decode a raw transaction to a Serializable transaction object

    :param rawtx: (:code:`bytes`) - Raw transaction to decode
    :param signed: (:code:`bool`) - If the raw transaction is a signed
        transaction.
    :return: Decoded :class:`ledgereth.objects.SerializableTransaction` instance
        for transaction
    """
    tx_type = rawtx[0]

    tx = None

    if tx_type < 127:
        if tx_type == 1:
            if signed:
                return SignedType1Transaction.from_rawtx(rawtx)
            else:
                return Type1Transaction.from_rawtx(rawtx)
        elif tx_type == 2:
            if signed:
                return SignedType2Transaction.from_rawtx(rawtx)
            else:
                return Type2Transaction.from_rawtx(rawtx)
        else:
            raise NotImplementedError(
                f"Support for transaction type {tx_type} has not yet been implemented"
            )
    elif signed:
        return SignedTransaction.from_rawtx(rawtx)

    return Transaction.from_rawtx(rawtx)
