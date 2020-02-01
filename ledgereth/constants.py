import os
from eth_utils import remove_0x_prefix

from ledgereth.utils import parse_bip32_path

LEGACY_ACCOUNTS = os.environ.get('LEDGER_LEGACY_ACCOUNTS') is not None
DEFAULT_PATH_STRING = "44'/60'/0'/0/0"
DEFAULT_PATH_ENCODED = parse_bip32_path(DEFAULT_PATH_STRING)
if LEGACY_ACCOUNTS:
    DEFAULT_PATH_STRING = "44'/60'/0'/0"
    DEFAULT_PATH_ENCODED = parse_bip32_path(DEFAULT_PATH_STRING)
DEFAULT_PATH = remove_0x_prefix(DEFAULT_PATH_ENCODED.hex())
VRS_RETURN_LENGTH = int(65).to_bytes(1, 'big')
CHAIN_ID = 0
