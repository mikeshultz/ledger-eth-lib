from rlp import Serializable
from eth_utils import add_0x_prefix, remove_0x_prefix, encode_hex, decode_hex

from ledgereth.comms import init_dongle, dongle_send, decode_response_address
from ledgereth.objects import RLPTx
from ledgereth.utils import is_hex_string

from typing import Any, Union

Text = Union[str, bytes]


def get_accounts(dongle: Any = None):
    """ Return available accounts """
    dongle = init_dongle(dongle)

    # TODO: Support multiple accounts?
    response = dongle_send(dongle, 'GET_DEFAULT_ADDRESS_NO_CONFIRM')

    # Use a List for future support of multiple accounts
    return [decode_response_address(response)]


def sign_transaction(tx: Serializable, dongle: Any = None):
    """ Sign a transaction object (rlp.Serializable) """
    dongle = init_dongle(dongle)
    pass


def create_transaction(to: bytes, value: int, gas: int, gas_price: int, nonce: int, data: Text,
                       dongle: Any = None):
    """ Create and sign a transaction from indiv args """
    dongle = init_dongle(dongle)

    if not is_hex_string(data):
        data = decode_hex(data)

    # Create a serializable tx object
    tx = RLPTx(
        # to=decode_hex(address),
        to=to,
        value=value,
        startgas=gas,
        gasprice=gas_price,
        data=data,
        nonce=nonce,
    )

    return sign_transaction(tx, dongle=dongle)
