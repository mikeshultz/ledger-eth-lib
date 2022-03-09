from eth_utils import encode_hex
from rlp import encode

from ledgereth.accounts import find_account, get_accounts
from ledgereth.objects import SignedTransaction
from ledgereth.transactions import create_transaction
from ledgereth.utils import decode_web3_access_list

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
        self.dongle = None

    def __call__(self, method, params):
        if method == "eth_sendTransaction":
            new_params = []

            for tx_obj in params:
                sender_address = tx_obj.get("from")
                nonce = tx_obj.get("nonce")
                gas = tx_obj.get("gas")
                gas_price = tx_obj.get("gasPrice")
                max_fee_per_gas = tx_obj.get("maxFeePerGas")
                max_priority_fee_per_gas = tx_obj.get("maxPriorityFeePerGas")
                value = tx_obj.get("value", "0x00")
                access_list = None

                if not sender_address:
                    # TODO: Should this use a default?
                    raise ValueError('"from" field not provided')

                if not gas:
                    # TODO: What's the default web3.py behavior for this?
                    raise ValueError('"gas" field not provided')

                if not gas_price and not max_fee_per_gas:
                    raise ValueError('"gasPrice" or "maxFeePerGas" field not provided')

                sender_account = find_account(sender_address, dongle=self._dongle)

                if not sender_account:
                    raise Exception(f"Account {sender_address} not found")

                if nonce is None:
                    nonce = self.w3.eth.get_transaction_count(sender_address)

                if "accessList" in tx_obj:
                    access_list = decode_web3_access_list(tx_obj["accessList"])

                signed_tx = create_transaction(
                    chain_id=self.w3.eth.chain_id,
                    destination=tx_obj.get("to"),
                    amount=int(value, 16),
                    gas=int(gas, 16),
                    gas_price=int(gas_price, 16) if gas_price else None,
                    max_fee_per_gas=int(max_fee_per_gas, 16)
                    if max_fee_per_gas
                    else None,
                    max_priority_fee_per_gas=int(max_priority_fee_per_gas, 16)
                    if max_priority_fee_per_gas
                    else None,
                    nonce=nonce,
                    data=tx_obj.get("data", b""),
                    sender_path=sender_account.path,
                    access_list=access_list,
                    dongle=self._dongle,
                )

                new_params.append(signed_tx.rawTransaction)

            # Change to raw tx call
            method = "eth_sendRawTransaction"
            params = new_params

        elif method == "eth_accounts":
            return {
                # TODO: Can we get the request ID somehow?
                "id": 1,
                "jsonrpc": "2.0",
                "result": list(
                    map(lambda a: a.address, get_accounts(dongle=self._dongle))
                ),
            }

        elif method == "eth_sign":
            raise NotImplementedError("Not yet implemented by LedgerSignerMiddleware")

        response = self.make_request(method, params)
        return response
