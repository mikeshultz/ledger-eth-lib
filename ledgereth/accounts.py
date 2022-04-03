from typing import List, Optional

from eth_utils import to_checksum_address

from ledgereth.comms import (
    Dongle,
    decode_response_address,
    dongle_send_data,
    init_dongle,
)
from ledgereth.constants import (
    DEFAULT_ACCOUNTS_FETCH,
    LEGACY_ACCOUNTS,
    MAX_ACCOUNTS_FETCH,
)
from ledgereth.objects import LedgerAccount
from ledgereth.utils import parse_bip32_path


def get_account_by_path(
    path_string: str, dongle: Optional[Dongle] = None
) -> LedgerAccount:
    """Return an account for a specific `BIP-44`_ derivation path

    :param path_string: (:code:`str`) - HID derivation path for the account to
        sign with.
    :param dongle: (:class:`ledgerblue.Dongle.Dongle`) -  The Dongle instance to
        use to communicate with the Ledger device
    :return: :class:`ledgereth.objects.LedgerAccount` instance for the given
        account

    .. _`BIP-44`: https://en.bitcoin.it/wiki/BIP_0044
    """
    dongle = init_dongle(dongle)
    path = parse_bip32_path(path_string)
    lc = len(path).to_bytes(1, "big")
    data = (len(path) // 4).to_bytes(1, "big") + path
    response = dongle_send_data(dongle, "GET_ADDRESS_NO_CONFIRM", data, Lc=lc)
    return LedgerAccount(path_string, decode_response_address(response))


def get_accounts(
    dongle: Optional[Dongle] = None, count: int = DEFAULT_ACCOUNTS_FETCH
) -> List[LedgerAccount]:
    """Return available accounts

    :param dongle: (:class:`ledgerblue.Dongle.Dongle`) -  The Dongle instance to
        use to communicate with the Ledger device
    :param count: (:code:`int`) - Amount of accounts to return
    :return: list of :class:`ledgereth.objects.LedgerAccount` instances found on
        the ledger
    """
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
    address: str, dongle: Optional[Dongle] = None, count: int = MAX_ACCOUNTS_FETCH
) -> Optional[LedgerAccount]:
    """Find an account by address

    :param address: (:class:`str`) - An address to look up
    :param dongle: (:class:`ledgerblue.Dongle.Dongle`) - The Dongle instance to
        use to communicate with the Ledger device
    :param count: (:code:`int`) - How deep in the derivation sequence to look
    :return: :class:`ledgereth.objects.LedgerAccount` instance if found on the
        Ledger
    """

    address = to_checksum_address(address)

    for account in get_accounts(dongle, count):
        if account.address == address:
            return account

    return None
