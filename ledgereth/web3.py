from eth_utils import encode_hex
from rlp import encode

from ledgereth.accounts import find_account, get_accounts
from ledgereth.objects import SignedTransaction
from ledgereth.transactions import create_transaction

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


class LedgerSignerMiddleware:
    def __init__(self, make_request, w3):
        self.w3 = w3
        self.make_request = make_request

    def __call__(self, method, params):
        if method == "eth_sendTransaction":
            new_params = []
            for tx_obj in params:
                sender_address = tx_obj.get("from")
                nonce = tx_obj.get("nonce")

                if not sender_address:
                    # TODO: Should this use a default?
                    raise ValueError('"from" field not provided')

                sender_account = find_account(sender_address)

                if not sender_account:
                    raise Exception(f"Account {sender_address} not found")

                if nonce is None:
                    nonce = self.w3.eth.getTransactionCount(sender_address)

                raw_tx = create_transaction(
                    to=tx_obj.get("to"),
                    value=tx_obj.get("value"),
                    gas=tx_obj.get("gas"),
                    gas_price=tx_obj.get("gasPrice"),
                    nonce=nonce,
                    data=tx_obj.get("data", ""),
                    sender_path=sender_account.path,
                )

                new_params.append(encode_hex(encode(raw_tx, SignedTransaction)))

            # Change to raw tx call
            method = "eth_sendRawTransaction"
            params = new_params

        elif method == "eth_accounts":
            return {
                "id": 1,
                "jsonrpc": "2.0",
                "result": list(map(lambda a: a.address, get_accounts())),
            }

        elif method == "eth_sign":
            raise NotImplementedError("Not yet implemented by LedgerSignerMiddleware")

        response = self.make_request(method, params)
        return response
