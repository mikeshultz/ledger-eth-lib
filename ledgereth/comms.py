from typing import Optional

from eth_utils import add_0x_prefix
from ledgerblue.comm import getDongle
from ledgerblue.commException import CommException
from ledgerblue.Dongle import Dongle

from ledgereth.constants import DEFAULT_PATH_ENCODED
from ledgereth.exceptions import LedgerError
from ledgereth.objects import ISO7816Command

DONGLE_CACHE: Optional[Dongle] = None
DONGLE_CONFIG_CACHE: Optional[bytes] = None


class LedgerCommands:
    """APDU commands for communication with ledger-app-eth.  Tested only on a Ledger Nano S.

    See `ledger-app-eth<https://github.com/LedgerHQ/ledger-app-eth/blob/master/doc/ethapp.asc>`_
    documentation.
    """

    GET_CONFIGURATION = ISO7816Command(
        CLA=b"\xe0",
        INS=b"\x06",
        P1=b"\x00",
        P2=b"\x00",
    )

    GET_DEFAULT_ADDRESS_NO_CONFIRM = ISO7816Command(
        CLA=b"\xe0",
        INS=b"\x02",
        P1=b"\x00",  # 0x00 - Return addres | 0x01 - Confirm befor ereturning
        P2=b"\x00",  # 0x00 - No chain code | 0x01 - With chain code
        data=(len(DEFAULT_PATH_ENCODED) // 4).to_bytes(1, "big") + DEFAULT_PATH_ENCODED,
    )

    GET_ADDRESS_NO_CONFIRM = ISO7816Command(
        CLA=b"\xe0",
        INS=b"\x02",
        P1=b"\x00",  # 0x00 - Return addres | 0x01 - Confirm befor ereturning
        P2=b"\x00",  # 0x00 - No chain code | 0x01 - With chain code
    )

    SIGN_TX_FIRST_DATA = ISO7816Command(
        CLA=b"\xe0",
        INS=b"\x04",
        P1=b"\x00",  # 0x00 - First TX data block | 0x80 - Secondary data block
        P2=b"\x00",
    )

    SIGN_TX_SECONDARY_DATA = ISO7816Command(
        CLA=b"\xe0",
        INS=b"\x04",
        P1=b"\x80",  # 0x00 - First TX data block | 0x80 - Secondary data block
        P2=b"\x00",
    )

    SIGN_MESSAGE_FIRST_DATA = ISO7816Command(
        CLA=b"\xe0",
        INS=b"\x08",
        P1=b"\x00",  # 0x00 - First TX data block | 0x80 - Secondary data block
        P2=b"\x00",
    )

    SIGN_MESSAGE_SECONDARY_DATA = ISO7816Command(
        CLA=b"\xe0",
        INS=b"\x08",
        P1=b"\x80",  # 0x00 - First TX data block | 0x80 - Secondary data block
        P2=b"\x00",
    )

    SIGN_TYPED_DATA = ISO7816Command(
        CLA=b"\xe0",
        INS=b"\x0c",
        P1=b"\x00",
        P2=b"\x00",
    )

    @staticmethod
    def get(name: str) -> bytes:
        if not hasattr(LedgerCommands, name):
            raise ValueError("Command not available")
        cmd = getattr(LedgerCommands, name)
        return cmd.encode()

    @staticmethod
    def get_with_data(
        name: str, data: bytes, Lc: bytes = None, Le: bytes = None
    ) -> bytes:
        if not hasattr(LedgerCommands, name):
            raise ValueError("Command not available")
        cmd = getattr(LedgerCommands, name)
        cmd.set_data(data)
        if Lc is not None:
            cmd.Lc = Lc
        if Le is not None:
            cmd.Le = Le
        return cmd.encode()


def dongle_send(dongle: Dongle, command_string: str) -> bytes:
    """Send a command to the dongle"""
    hex_command = LedgerCommands.get(command_string)
    try:
        return dongle.exchange(hex_command)
    except CommException as err:
        raise LedgerError.transalate_comm_exception(err) from err


def dongle_send_data(
    dongle: Dongle, command_string: str, data: bytes, Lc: bytes = None, Le: bytes = None
) -> bytes:
    """Send a command with data to the dongle"""
    hex_command = LedgerCommands.get_with_data(command_string, data, Lc=Lc, Le=Le)
    try:
        return dongle.exchange(hex_command)
    except CommException as err:
        raise LedgerError.transalate_comm_exception(err) from err


def decode_response_version_from_config(confbytes: bytes) -> str:
    """Decode the string version from the bytearray response from Ledger device"""
    return "{}.{}.{}".format(
        confbytes[1],
        confbytes[2],
        confbytes[3],
    )


def decode_response_address(response):
    """Decode an address response from the dongle"""
    offset = 1 + response[0]
    address_encoded = response[offset + 1 : offset + 1 + response[offset]]
    return add_0x_prefix(address_encoded.decode("ascii"))


def is_usable_version(confbytes: bytes) -> bool:
    """Only tested since 1.2.4 up to 1.10.0"""
    version = decode_response_version_from_config(confbytes)
    v_parts = version.split(".")
    ver = [int(s) for s in v_parts]

    # v9.9.9 is MockLedger
    if ver[0] == 9:
        return True

    # Major must be v1
    if ver[0] != 1:
        return False

    # Minor must not be below 2 because untested
    if ver[1] < 2:
        return False

    # Patch must not be below 4 if v1.2
    if ver[1] == 2 and ver[2] < 4:
        return False

    return True


def init_dongle(dongle: Dongle = None, debug: bool = False) -> Dongle:
    """Initialize the dongle and sanity check the connection"""
    global DONGLE_CACHE, DONGLE_CONFIG_CACHE

    # If not given, use cache if available
    if dongle is None and DONGLE_CACHE is None:
        try:
            DONGLE_CACHE = getDongle(debug)
        except CommException as err:
            raise LedgerError.transalate_comm_exception(err) from err

        # Sanity check the version
        if DONGLE_CONFIG_CACHE is None or dongle is not None:
            DONGLE_CONFIG_CACHE = dongle_send(DONGLE_CACHE, "GET_CONFIGURATION")

        if not is_usable_version(DONGLE_CONFIG_CACHE):
            raise NotImplementedError("Unsupported firmware version")

    return dongle or DONGLE_CACHE
