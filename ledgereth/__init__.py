"""ledgereth, a library to interface with ledger-app-eth on Ledger hardware wallets."""
from importlib.metadata import metadata
from ledgereth.accounts import find_account, get_account_by_path, get_accounts
from ledgereth.messages import sign_message, sign_typed_data_draft
from ledgereth.objects import (
    SignedTransaction,
    SignedType1Transaction,
    SignedType2Transaction,
    Transaction,
    Type1Transaction,
    Type2Transaction,
)
from ledgereth.transactions import create_transaction, sign_transaction

meta = metadata("ledgereth")

__all__ = [
    "Transaction",
    "Type1Transaction",
    "Type2Transaction",
    "SignedTransaction",
    "SignedType1Transaction",
    "SignedType2Transaction",
    "create_transaction",
    "find_account",
    "get_account_by_path",
    "get_accounts",
    "sign_message",
    "sign_transaction",
    "sign_typed_data_draft",
]
__version__ = meta["Version"]
__author__ = meta["Author-email"].split("<")[0].strip()
__email__ = meta["Author-email"]
