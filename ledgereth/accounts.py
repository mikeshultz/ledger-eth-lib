from typing import Any, List, Optional

from eth_utils import to_checksum_address

from ledgereth.comms import decode_response_address, dongle_send_data, init_dongle
from ledgereth.constants import (
    DEFAULT_ACCOUNTS_FETCH,
    LEGACY_ACCOUNTS,
    MAX_ACCOUNTS_FETCH,
)
from ledgereth.objects import LedgerAccount
from ledgereth.utils import parse_bip32_path


def get_account_by_path(path_string: str, dongle: Any = None) -> LedgerAccount:
    """Return an account for a specific BIP32 derivation path"""
    dongle = init_dongle(dongle)
    path = parse_bip32_path(path_string)
    lc = len(path).to_bytes(1, "big")
    data = (len(path) // 4).to_bytes(1, "big") + path
    response = dongle_send_data(dongle, "GET_ADDRESS_NO_CONFIRM", data, Lc=lc)
    return LedgerAccount(path_string, decode_response_address(response))


def get_accounts(
    dongle: Any = None, count: int = DEFAULT_ACCOUNTS_FETCH
) -> List[LedgerAccount]:
    """Return available accounts"""
    accounts = []
    dongle = init_dongle(dongle)

    for i in range(count):
        if LEGACY_ACCOUNTS:
            path_string = f"44'/60'/0'/{i}"
        else:
            path_string = f"44'/60'/{i}'/0/0"
        account = get_account_by_path(path_string, dongle)
        accounts.append(account)

    return accounts


def find_account(
    address: str, dongle: Any = None, count: int = MAX_ACCOUNTS_FETCH
) -> Optional[LedgerAccount]:
    """Find an account by address"""

    address = to_checksum_address(address)

    for account in get_accounts(dongle, count):
        if account.address == address:
            return account

    return None
