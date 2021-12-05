import os

from eth_utils import remove_0x_prefix

from ledgereth.utils import get_int_from_dict, parse_bip32_path

# Chain ID to use if not given by user
DEFAULT_CHAIN_ID = 1

# Default accounts to fetch with get_accounts
DEFAULT_ACCOUNTS_FETCH = 1

# Number of accounts to fetch when looking up an account by address
MAX_ACCOUNTS_FETCH = get_int_from_dict(os.environ, "MAX_ACCOUNTS_FETCH", 5)

# Whether to use the legacy bip32 path derivation used by Ledger Chrome app
LEGACY_ACCOUNTS = os.getenv("LEDGER_LEGACY_ACCOUNTS") is not None

DEFAULT_PATH_STRING = "44'/60'/0'/0/0"
DEFAULT_PATH_ENCODED = parse_bip32_path(DEFAULT_PATH_STRING)
if LEGACY_ACCOUNTS:
    DEFAULT_PATH_STRING = "44'/60'/0'/0"
    DEFAULT_PATH_ENCODED = parse_bip32_path(DEFAULT_PATH_STRING)
DEFAULT_PATH = remove_0x_prefix(DEFAULT_PATH_ENCODED.hex())
VRS_RETURN_LENGTH = int(65).to_bytes(1, "big")
