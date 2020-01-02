from eth_utils import remove_0x_prefix

from ledgereth.utils import parse_bip32_path

DEFAULT_PATH_ENCODED = parse_bip32_path("44'/60'/0'/0/0")
DEFAULT_PATH = remove_0x_prefix(DEFAULT_PATH_ENCODED.hex())
VRS_RETURN_LENGTH = int(65).to_bytes(1, 'big')
CHAIN_ID = 0
