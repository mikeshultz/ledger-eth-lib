import sys
import binascii
from rlp import Serializable, encode
from eth_utils import encode_hex, decode_hex

from ledgereth.constants import DEFAULT_PATH_ENCODED
from ledgereth.comms import (
    init_dongle,
    chunks,
    dongle_send,
    dongle_send_data,
    decode_response_address,
)
from ledgereth.objects import Transaction, SignedTransaction
from ledgereth.utils import is_hex_string, parse_bip32_path

from typing import Any, Union

Text = Union[str, bytes]
CHAIN_ID = 1
DEFAULT_ACCOUNTS_FETCH = 1


def get_accounts(dongle: Any = None, count: int = DEFAULT_ACCOUNTS_FETCH):
    """ Return available accounts """
    addresses = []
    dongle = init_dongle(dongle)

    if count == 1:
        response = dongle_send(dongle, 'GET_DEFAULT_ADDRESS_NO_CONFIRM')
        addresses.append(decode_response_address(response))
    else:
        """
        TODO: Verify path derivation is standard for ETH/ledger. Which one?
        1) 44'/60'/0'/0/1
        2) 44'/60'/0'/1/0
        2) 44'/60'/1'/0/0
        """
        for i in range(count):
            path = parse_bip32_path("44'/60'/0'/0/{}".format(i))
            lc = len(path).to_bytes(1, 'big')
            data = (len(path) // 4).to_bytes(1, 'big') + path
            response = dongle_send_data(
                dongle,
                'GET_ADDRESS_NO_CONFIRM',
                data,
                Lc=lc
            )
            addresses.append(decode_response_address(response))
    return addresses


def sign_transaction(tx: Serializable, dongle: Any = None):
    """ Sign a transaction object (rlp.Serializable) """
    dongle = init_dongle(dongle)
    retval = None

    assert isinstance(tx, Transaction), "Only RLPTx transaction objects are currently supported"
    print('tx: ', tx)
    encoded_tx = encode(tx, Transaction)
    payload = (len(DEFAULT_PATH_ENCODED) // 4).to_bytes(1, 'big') + DEFAULT_PATH_ENCODED + encoded_tx

    chunk_count = 0
    for chunk in chunks(payload):
        chunk_size = len(chunk)
        if chunk_count == 0:
            retval = dongle_send_data(
                dongle,
                'SIGN_TX_FIRST_DATA',
                chunk,
                Lc=chunk_size.to_bytes(1, 'big')
            )
        else:
            retval = dongle_send_data(
                dongle,
                'SIGN_TX_SECONDARY_DATA',
                chunk,
                Lc=chunk_size.to_bytes(1, 'big')
            )
        chunk_count += 1

    if retval is None or len(retval) < 64:
        raise Exception('Invalid response from Ledger')

    if (CHAIN_ID*2 + 35) + 1 > 255:
        ecc_parity = retval[0] - ((CHAIN_ID*2 + 35) % 256)
        v = (CHAIN_ID*2 + 35) + ecc_parity
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
        s=s
    )


def create_transaction(to: bytes, value: int, gas: int, gas_price: int, nonce: int, data: Text,
                       dongle: Any = None):
    """ Create and sign a transaction from indiv args """
    dongle = init_dongle(dongle)

    if not is_hex_string(data):
        data = decode_hex(data) or b''

    # Create a serializable tx object
    tx = Transaction(
        # to=decode_hex(address),
        to=decode_hex(to),
        #value=hex(value),
        value=value,
        startgas=gas,
        gasprice=gas_price,
        data=data,
        nonce=nonce,
    )

    return sign_transaction(tx, dongle=dongle)


class LedgerSignerMiddleware:
    def __init__(self, make_request, w3):
        self.w3 = w3
        self.make_request = make_request

    def __call__(self, method, params):
        if method == 'eth_sendTransaction':
            new_params = []
            for tx_obj in params:
                raw_tx = create_transaction(
                    to=tx_obj.get('to'),
                    value=tx_obj.get('value'),
                    gas=tx_obj.get('gas'),
                    gas_price=tx_obj.get('gasPrice'),
                    nonce=tx_obj.get('nonce'),
                    data=tx_obj.get('data', ''),
                )
                new_params.append(encode_hex(encode(raw_tx, SignedTransaction)))

            # Change to raw tx call
            method = 'eth_sendRawTransaction'
            params = new_params

        elif method == 'eth_accounts':
            return {
              "id": 1,
              "jsonrpc": "2.0",
              "result": get_accounts()
            }

        elif method == 'eth_sign':
            raise NotImplementedError('Not yet implemented by LedgerSignerMiddleware')

        response = self.make_request(method, params)
        return response
