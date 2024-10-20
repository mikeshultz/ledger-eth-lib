from typing import cast

from eth_account import Account
from eth_account.messages import encode_defunct, encode_typed_data
from eth_utils.address import to_checksum_address
from eth_utils.hexadecimal import encode_hex
from web3 import Web3
from web3.providers.eth_tester import EthereumTesterProvider
from web3.providers.eth_tester.defaults import API_ENDPOINTS, static_return
from web3.types import AccessList, TxReceipt, Wei

from ledgereth.accounts import get_accounts
from ledgereth.web3 import LedgerSignerMiddleware

from .fixtures import eip712_dict


def fund_account(web3: Web3, address: str, amount: int = int(1e18)) -> TxReceipt:
    funder = web3.eth.accounts[0]

    tx_hash = web3.eth.send_transaction(
        {
            "from": funder,
            "to": address,
            "value": Wei(amount),
            "gas": 21000,
            "gasPrice": Web3.to_wei(5e9, "wei"),
        }
    )

    return web3.eth.wait_for_transaction_receipt(tx_hash)


def test_web3_middleware_legacy(yield_dongle):
    """Test LedgerSignerMiddleware with a legacy transaction"""
    endpoints = {**API_ENDPOINTS}
    # Max chain ID for legacy transactions
    # Ref: https://github.com/mikeshultz/ledger-eth-lib/issues/41
    endpoints["eth"]["chainId"] = static_return(4294967295)
    provider = EthereumTesterProvider(api_endpoints=endpoints)
    web3 = Web3(provider)
    clean_web3 = Web3(provider)
    alice_address = web3.eth.accounts[0]

    with yield_dongle() as dongle:
        # Inject our middlware
        web3.middleware_onion.add(LedgerSignerMiddleware, "ledgereth_middleware")
        ledgereth_middleware = web3.middleware_onion.get("ledgereth_middleware")

        # Set to the test dongle to make sure it's not using the default dongle
        ledgereth_middleware._dongle = dongle  # pyright: ignore

        # Get an account from the Ledger
        bob = get_accounts(dongle)[0]

        # Make sure our Ledger account has funds
        fund_account(clean_web3, bob.address)

        bob_balance = web3.eth.get_balance(to_checksum_address(bob.address))
        assert bob_balance > 0

        amount = int(0.25e18)

        # Send a transaction using the dongle
        tx = web3.eth.send_transaction(
            {
                "from": bob.address,
                "to": alice_address,
                "value": Web3.to_wei(amount, "wei"),
                "gas": 21000,
                "gasPrice": Web3.to_wei(5e9, "wei"),
            }
        )
        receipt = web3.eth.wait_for_transaction_receipt(tx)

        assert receipt["blockNumber"]
        assert receipt["status"] == 1
        assert receipt["from"] == bob.address
        assert receipt["to"] == alice_address


def test_web3_middleware_type1(yield_dongle):
    """Test LedgerSignerMiddleware with type 1 transactions"""
    provider = EthereumTesterProvider()
    web3 = Web3(provider)
    clean_web3 = Web3(provider)
    alice_address = web3.eth.accounts[0]

    with yield_dongle() as dongle:
        # Inject our middlware
        web3.middleware_onion.add(LedgerSignerMiddleware, "ledgereth_middleware")
        ledgereth_middleware = web3.middleware_onion.get("ledgereth_middleware")

        # Set to the test dongle to make sure it's not using the default dongle
        ledgereth_middleware._dongle = dongle  # pyright: ignore

        # Get an account from the Ledger
        bob = get_accounts(dongle)[0]

        # Make sure our Ledger account has funds
        fund_account(clean_web3, bob.address)

        bob_balance = web3.eth.get_balance(to_checksum_address(bob.address))
        assert bob_balance > 0

        amount = int(0.25e18)

        # Send a transaction using the dongle
        tx = web3.eth.send_transaction(
            {
                "from": bob.address,
                "to": alice_address,
                "value": Web3.to_wei(amount, "wei"),
                "gas": 30000,
                "gasPrice": Web3.to_wei(5e9, "wei"),
                "accessList": cast(
                    AccessList,
                    [
                        {
                            "address": alice_address,
                            "storageKeys": [
                                "0x0000000000000000000000000000000000000000000000000000000000000001",
                                "0x0000000000000000000000000000000000000000000000000000000000000002",
                                "0x0000000000000000000000000000000000000000000000000000000000000003",
                            ],
                        }
                    ],
                ),
            }
        )
        receipt = web3.eth.wait_for_transaction_receipt(tx)

        assert receipt["blockNumber"]
        assert receipt["status"] == 1
        assert receipt["from"] == bob.address
        assert receipt["to"] == alice_address


def test_web3_middleware_type12(yield_dongle):
    """Test LedgerSignerMiddleware with type 1 transactions"""
    provider = EthereumTesterProvider()
    web3 = Web3(provider)
    clean_web3 = Web3(provider)
    alice_address = web3.eth.accounts[0]

    with yield_dongle() as dongle:
        # Inject our middlware
        web3.middleware_onion.add(LedgerSignerMiddleware, "ledgereth_middleware")
        ledgereth_middleware = web3.middleware_onion.get("ledgereth_middleware")

        # Set to the test dongle to make sure it's not using the default dongle
        ledgereth_middleware._dongle = dongle  # pyright: ignore

        # Get an account from the Ledger
        bob = get_accounts(dongle)[0]

        # Make sure our Ledger account has funds
        fund_account(clean_web3, bob.address)

        bob_balance = web3.eth.get_balance(to_checksum_address(bob.address))
        assert bob_balance > 0

        amount = int(0.25e18)

        # Send a transaction using the dongle
        tx = web3.eth.send_transaction(
            {
                "from": bob.address,
                "to": alice_address,
                "value": Web3.to_wei(amount, "wei"),
                "gas": 30000,
                "maxFeePerGas": Web3.to_wei(5e9, "wei"),
                "maxPriorityFeePerGas": Web3.to_wei(1e8, "wei"),
                "accessList": cast(
                    AccessList,
                    [
                        {
                            "address": alice_address,
                            "storageKeys": [
                                "0x0000000000000000000000000000000000000000000000000000000000000001",
                                "0x0000000000000000000000000000000000000000000000000000000000000002",
                                "0x0000000000000000000000000000000000000000000000000000000000000003",
                            ],
                        }
                    ],
                ),
            }
        )
        receipt = web3.eth.wait_for_transaction_receipt(tx)

        assert receipt["blockNumber"]
        assert receipt["status"] == 1
        assert receipt["from"] == bob.address
        assert receipt["to"] == alice_address


def test_web3_middleware_sign_data(yield_dongle):
    """Test LedgerSignerMiddleware EIP-191 message signing"""
    text_message = b"LedgerSignerMiddleware"
    provider = EthereumTesterProvider()
    web3 = Web3(provider)

    with yield_dongle() as dongle:
        # Inject our middlware
        web3.middleware_onion.add(LedgerSignerMiddleware, "ledgereth_middleware")
        ledgereth_middleware = web3.middleware_onion.get("ledgereth_middleware")

        # Set to the test dongle to make sure it's not using the default dongle
        ledgereth_middleware._dongle = dongle  # pyright: ignore

        # Get an account from the Ledger
        signer = get_accounts(dongle)[0]

        # Send a transaction using the dongle
        res = web3.eth.sign(signer.address, data=text_message)

        assert signer.address == Account.recover_message(
            encode_defunct(text_message), signature=res
        )


def test_web3_middleware_sign_hexstr(yield_dongle):
    """Test LedgerSignerMiddleware EIP-191 message signing"""
    text_message = encode_hex("LedgerSignerMiddleware")
    provider = EthereumTesterProvider()
    web3 = Web3(provider)

    with yield_dongle() as dongle:
        # Inject our middlware
        web3.middleware_onion.add(LedgerSignerMiddleware, "ledgereth_middleware")
        ledgereth_middleware = web3.middleware_onion.get("ledgereth_middleware")

        # Set to the test dongle to make sure it's not using the default dongle
        ledgereth_middleware._dongle = dongle  # pyright: ignore

        # Get an account from the Ledger
        signer = get_accounts(dongle)[0]

        # Send a transaction using the dongle
        res = web3.eth.sign(signer.address, hexstr=text_message)

        assert signer.address == Account.recover_message(
            encode_defunct(hexstr=text_message), signature=res
        )


def test_web3_middleware_sign_text(yield_dongle):
    """Test LedgerSignerMiddleware EIP-191 message signing"""
    text_message = "LedgerSignerMiddleware"
    provider = EthereumTesterProvider()
    web3 = Web3(provider)

    with yield_dongle() as dongle:
        # Inject our middlware
        web3.middleware_onion.add(LedgerSignerMiddleware, "ledgereth_middleware")
        ledgereth_middleware = web3.middleware_onion.get("ledgereth_middleware")

        # Set to the test dongle to make sure it's not using the default dongle
        ledgereth_middleware._dongle = dongle  # pyright: ignore

        # Get an account from the Ledger
        signer = get_accounts(dongle)[0]

        # Send a transaction using the dongle
        res = web3.eth.sign(signer.address, text=text_message)

        assert signer.address == Account.recover_message(
            encode_defunct(text=text_message), signature=res
        )


def test_web3_middleware_sign_typed_data(yield_dongle):
    """Test LedgerSignerMiddleware EIP-712 typed data signing"""

    signable = encode_typed_data(full_message=eip712_dict)
    provider = EthereumTesterProvider()
    web3 = Web3(provider)

    with yield_dongle() as dongle:
        # Inject our middlware
        web3.middleware_onion.add(LedgerSignerMiddleware, "ledgereth_middleware")
        ledgereth_middleware = web3.middleware_onion.get("ledgereth_middleware")

        # Set to the test dongle to make sure it's not using the default dongle
        ledgereth_middleware._dongle = dongle  # pyright: ignore

        # Get an account from the Ledger
        signer = get_accounts(dongle)[0]

        # Send a transaction using the dongle
        res = web3.eth.sign_typed_data(to_checksum_address(signer.address), eip712_dict)

        assert signer.address == Account.recover_message(signable, signature=res)
