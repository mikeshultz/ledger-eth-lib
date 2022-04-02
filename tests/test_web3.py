from eth_account import Account
from eth_account.messages import encode_defunct, encode_structured_data
from eth_utils import encode_hex
from web3 import Web3
from web3.datastructures import AttributeDict
from web3.providers.eth_tester import EthereumTesterProvider
from web3.types import TxReceipt, Wei

from ledgereth.accounts import get_accounts
from ledgereth.constants import DEFAULT_PATH_ENCODED, DEFAULT_PATH_STRING
from ledgereth.utils import (
    decode_bip32_path,
    is_bip32_path,
    is_bytes,
    is_hex_string,
    parse_bip32_path,
)
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
            "gasPrice": int(5e9),
        }
    )

    return web3.eth.wait_for_transaction_receipt(tx_hash)


def test_web3_middleware_legacy(yield_dongle):
    """Test LedgerSignerMiddleware with a legacy transaction"""
    provider = EthereumTesterProvider()
    web3 = Web3(provider)
    clean_web3 = Web3(provider)
    alice_address = web3.eth.accounts[0]

    with yield_dongle() as dongle:
        # Inject our middlware
        web3.middleware_onion.add(LedgerSignerMiddleware, "ledgereth_middleware")
        ledgereth_middleware = web3.middleware_onion.get("ledgereth_middleware")

        # Set to the test dongle to make sure it's not using the default dongle
        ledgereth_middleware._dongle = dongle

        # Get an account from the Ledger
        bob = get_accounts(dongle)[0]

        # Make sure our Ledger account has funds
        fund_account(clean_web3, bob.address)

        bob_balance = web3.eth.get_balance(bob.address)
        assert bob_balance > 0

        amount = int(0.25e18)

        # Send a transaction using the dongle
        tx = web3.eth.send_transaction(
            {
                "from": bob.address,
                "to": alice_address,
                "value": amount,
                "gas": 21000,
                "gasPrice": int(5e9),
            }
        )
        receipt = web3.eth.wait_for_transaction_receipt(tx)

        assert receipt.blockNumber
        assert receipt.status == 1
        assert receipt["from"] == bob.address
        assert receipt.to == alice_address


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
        ledgereth_middleware._dongle = dongle

        # Get an account from the Ledger
        bob = get_accounts(dongle)[0]

        # Make sure our Ledger account has funds
        fund_account(clean_web3, bob.address)

        bob_balance = web3.eth.get_balance(bob.address)
        assert bob_balance > 0

        amount = int(0.25e18)

        # Send a transaction using the dongle
        tx = web3.eth.send_transaction(
            {
                "from": bob.address,
                "to": alice_address,
                "value": amount,
                "gas": 30000,
                "gasPrice": int(5e9),
                "accessList": [
                    {
                        "address": alice_address,
                        "storageKeys": [
                            "0x0000000000000000000000000000000000000000000000000000000000000001",
                            "0x0000000000000000000000000000000000000000000000000000000000000002",
                            "0x0000000000000000000000000000000000000000000000000000000000000003",
                        ],
                    }
                ],
            }
        )
        receipt = web3.eth.wait_for_transaction_receipt(tx)

        assert receipt.blockNumber
        assert receipt.status == 1
        assert receipt["from"] == bob.address
        assert receipt.to == alice_address


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
        ledgereth_middleware._dongle = dongle

        # Get an account from the Ledger
        bob = get_accounts(dongle)[0]

        # Make sure our Ledger account has funds
        fund_account(clean_web3, bob.address)

        bob_balance = web3.eth.get_balance(bob.address)
        assert bob_balance > 0

        amount = int(0.25e18)

        # Send a transaction using the dongle
        tx = web3.eth.send_transaction(
            {
                "from": bob.address,
                "to": alice_address,
                "value": amount,
                "gas": 30000,
                "maxFeePerGas": int(5e9),
                "maxPriorityFeePerGas": int(1e8),
                "accessList": [
                    {
                        "address": alice_address,
                        "storageKeys": [
                            "0x0000000000000000000000000000000000000000000000000000000000000001",
                            "0x0000000000000000000000000000000000000000000000000000000000000002",
                            "0x0000000000000000000000000000000000000000000000000000000000000003",
                        ],
                    }
                ],
            }
        )
        receipt = web3.eth.wait_for_transaction_receipt(tx)

        assert receipt.blockNumber
        assert receipt.status == 1
        assert receipt["from"] == bob.address
        assert receipt.to == alice_address


def test_web3_middleware_sign_data(yield_dongle):
    """Test LedgerSignerMiddleware EIP-191 message signing"""
    text_message = b"LedgerSignerMiddleware"
    provider = EthereumTesterProvider()
    web3 = Web3(provider)
    clean_web3 = Web3(provider)
    alice_address = web3.eth.accounts[0]

    with yield_dongle() as dongle:
        # Inject our middlware
        web3.middleware_onion.add(LedgerSignerMiddleware, "ledgereth_middleware")
        ledgereth_middleware = web3.middleware_onion.get("ledgereth_middleware")

        # Set to the test dongle to make sure it's not using the default dongle
        ledgereth_middleware._dongle = dongle

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
    clean_web3 = Web3(provider)
    alice_address = web3.eth.accounts[0]

    with yield_dongle() as dongle:
        # Inject our middlware
        web3.middleware_onion.add(LedgerSignerMiddleware, "ledgereth_middleware")
        ledgereth_middleware = web3.middleware_onion.get("ledgereth_middleware")

        # Set to the test dongle to make sure it's not using the default dongle
        ledgereth_middleware._dongle = dongle

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
    clean_web3 = Web3(provider)
    alice_address = web3.eth.accounts[0]

    with yield_dongle() as dongle:
        # Inject our middlware
        web3.middleware_onion.add(LedgerSignerMiddleware, "ledgereth_middleware")
        ledgereth_middleware = web3.middleware_onion.get("ledgereth_middleware")

        # Set to the test dongle to make sure it's not using the default dongle
        ledgereth_middleware._dongle = dongle

        # Get an account from the Ledger
        signer = get_accounts(dongle)[0]

        # Send a transaction using the dongle
        res = web3.eth.sign(signer.address, text=text_message)

        assert signer.address == Account.recover_message(
            encode_defunct(text=text_message), signature=res
        )


def test_web3_middleware_sign_typed_data(yield_dongle):
    """Test LedgerSignerMiddleware EIP-712 typed data signing"""

    signable = encode_structured_data(eip712_dict)
    provider = EthereumTesterProvider()
    web3 = Web3(provider)
    clean_web3 = Web3(provider)
    alice_address = web3.eth.accounts[0]

    with yield_dongle() as dongle:
        # Inject our middlware
        web3.middleware_onion.add(LedgerSignerMiddleware, "ledgereth_middleware")
        ledgereth_middleware = web3.middleware_onion.get("ledgereth_middleware")

        # Set to the test dongle to make sure it's not using the default dongle
        ledgereth_middleware._dongle = dongle

        # Get an account from the Ledger
        signer = get_accounts(dongle)[0]

        # Send a transaction using the dongle
        res = web3.eth.sign_typed_data(signer.address, eip712_dict)

        assert signer.address == Account.recover_message(signable, signature=res)
