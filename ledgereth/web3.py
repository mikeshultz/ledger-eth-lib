import sys
import binascii
from rlp import Serializable, encode
from eth_utils import encode_hex, decode_hex

from ledgereth.constants import LEGACY_ACCOUNTS, DEFAULT_PATH_STRING, DEFAULT_PATH_ENCODED
from ledgereth.comms import (
    init_dongle,
    chunks,
    dongle_send,
    dongle_send_data,
    decode_response_address,
)
from ledgereth.objects import LedgerAccount, Transaction, SignedTransaction
from ledgereth.utils import is_hex_string, parse_bip32_path, is_bip32_path

from typing import Any, Union

Text = Union[str, bytes]
CHAIN_ID = 1
DEFAULT_ACCOUNTS_FETCH = 1

"""
ACCOUNT DERIVATION ISSUES

Derivation path debate is ever ongoing.  Ledger Live app uses opton #3 here.
The old chrome app used #4.

1) 44'/60'/0'/0/x
2) 44'/60'/0'/x/0
3) 44'/60'/x'/0/0
4) 44'/60'/0'/x

The Ledger Live account enumeration algo appears to be:

1) Try legacy account X (if no balance, GOTO 3)
2) X+1 and GOTO 1
3) Try new-derivation Y (if no balance, RETURN)
4) Y+1 and GOTO 3

Since this library is trying not to resort to JSON-RPC calls, this algorithm is
not usable, so it's either or, and it currently defaults to the newer
derivation.

To use legacy derivation, set the environment variable LEDGER_LEGACY_ACCOUNTS

Ref (cannot find an authoritative source):
https://github.com/ethereum/EIPs/issues/84#issuecomment-292324521
"""


def get_account_by_path(path_string: str, dongle: Any = None):
    """ Return an account for a specific BIP32 derivation path """
    dongle = init_dongle(dongle)
    path = parse_bip32_path(path_string)
    lc = len(path).to_bytes(1, 'big')
    data = (len(path) // 4).to_bytes(1, 'big') + path
    response = dongle_send_data(
        dongle,
        'GET_ADDRESS_NO_CONFIRM',
        data,
        Lc=lc
    )
    return LedgerAccount(path_string, decode_response_address(response))


def get_accounts(dongle: Any = None, count: int = DEFAULT_ACCOUNTS_FETCH):
    """ Return available accounts """
    accounts = []
    dongle = init_dongle(dongle)

    for i in range(count):
        if LEGACY_ACCOUNTS:
            path_string = "44'/60'/0'/{}".format(i)
        else:
            path_string = "44'/60'/{}'/0/0".format(i)
        account = get_account_by_path(path_string, dongle)
        accounts.append(account)

    return accounts


def sign_transaction(tx: Serializable, sender_path: str = DEFAULT_PATH_STRING, dongle: Any = None):
    """ Sign a transaction object (rlp.Serializable) """
    dongle = init_dongle(dongle)
    retval = None

    assert isinstance(tx, Transaction), "Only RLPTx transaction objects are currently supported"
    print('tx: ', tx)
    encoded_tx = encode(tx, Transaction)

    if not is_bip32_path(sender_path):
        raise ValueError('Invalid sender BIP32 path given to sign_transaction')

    path = parse_bip32_path(sender_path)
    payload = (len(path) // 4).to_bytes(1, 'big') + path + encoded_tx

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
                       sender_path: str = DEFAULT_PATH_STRING, dongle: Any = None):
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

    return sign_transaction(sender_path, tx, dongle=dongle)


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
