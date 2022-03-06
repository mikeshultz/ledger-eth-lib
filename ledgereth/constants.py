import os
from typing import Any, Dict, Type

from eth_utils import remove_0x_prefix


def getenvint(key, default=0):
    """Get an int from en env var or use default"""
    try:
        return int(os.environ.get("MAX_ACCOUNTS_FETCH"))
    except TypeError:
        return default


# Chain ID to use if not given by user
DEFAULT_CHAIN_ID = 1

# Default accounts to fetch with get_accounts
DEFAULT_ACCOUNTS_FETCH = 1

# Number of accounts to fetch when looking up an account by address
MAX_ACCOUNTS_FETCH = getenvint("MAX_ACCOUNTS_FETCH", 5)

# Whether to use the legacy bip32 path derivation used by Ledger Chrome app
LEGACY_ACCOUNTS = os.getenv("LEDGER_LEGACY_ACCOUNTS") is not None

DEFAULT_PATH_STRING = "44'/60'/0'/0/0"
DEFAULT_PATH_ENCODED = (
    b"\x80\x00\x00,\x80\x00\x00<\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
)
if LEGACY_ACCOUNTS:
    DEFAULT_PATH_STRING = "44'/60'/0'/0"
    DEFAULT_PATH_ENCODED = b"\x80\x00\x00,\x80\x00\x00<\x80\x00\x00\x00\x00\x00\x00\x00"
DEFAULT_PATH = remove_0x_prefix(DEFAULT_PATH_ENCODED.hex())
VRS_RETURN_LENGTH = int(65).to_bytes(1, "big")

# Data size expected from Ledger
DATA_CHUNK_SIZE = 255

# Ethereum magic number
MAGIC_NUMBER = 27

# Default "zero" values in EVM/Solidity
DEFAULTS: Dict[Type, Any] = {
    int: 0,
    bytes: b"",
}
