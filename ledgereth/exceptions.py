"""Exceptions for the ledgereth package."""

from collections.abc import Mapping
from enum import IntEnum

from ledgerblue.commException import CommException


class LedgerErrorCodes(IntEnum):
    """Known hex error codes returned by the Ledger device."""

    OK = 0x9000

    ##
    # User/input errors
    ##

    TX_TYPE_UNSUPPORTED = 0x6501
    INCORRECT_LENGTH = 0x6700
    # This may happen if first/secondary data is invalid or out of order or
    # unexpected p1/p2 values
    INVALID_TX_CHUNKS = 0x6B00
    # This can also mean ADPU empty, apparently
    CANCELED_BY_USER = 0x6982
    APDU_SIZE_MISMATCH = 0x6983
    # Invalid data, transaction, or HD path, and a bit of a catch-all
    INVALID_DATA = 0x6A80
    APP_SLEEP = 0x6804
    APP_NOT_STARTED = 0x6D00
    DEVICE_LOCKED = 0x6B0C
    # "Plugins" allow resolution of function selectors and args for various
    # smart contracts.  Ref: https://blog.ledger.com/ethereum-plugins/
    PLUGIN_NOT_PRESENT = 0x6984

    ##
    # Internal errors
    ##

    INT_CONVERSION_ERROR = 0x6504
    OUTPUT_BUFFER_TOO_SMALL = 0x6502
    PLUGIN_ERROR = 0x6503
    # "Signsture/parser not initialized" in source
    DECLINED = 0x6985

    ##
    # Inferred errors found through discovery
    ##

    # ledgerblue default code
    UKNOWN = 0x6F00
    APP_NOT_FOUND = 0x6D02

    @classmethod
    def get_by_value(cls, val):
        """Get the enum member by its value."""
        try:
            return cls(val)
        except ValueError:
            return None


class LedgerError(Exception):
    """An exception raised from a Ledger device error."""

    message = "Unexpected Ledger error"

    def __init__(self, message=None):
        super().__init__(message or self.message)

    @classmethod
    def transalate_comm_exception(cls, exp: CommException):
        """Translate a Ledger CommException to a LedgerError."""
        return ERROR_CODE_EXCEPTIONS.get(
            exp.sw,  # type: ignore
            LedgerError(
                f"Unexpected error: {hex(exp.sw)}"
                f" {LedgerErrorCodes.get_by_value(exp.sw) or 'UNKNOWN'}"
            ),
        )


class LedgerNotFound(LedgerError):  # noqa: D101, N818
    message = "Unable to find Ledger device"


class LedgerLocked(LedgerError):  # noqa: D101, N818
    message = "Ledger appears to be locked"


class LedgerAppNotOpened(LedgerError):  # noqa: D101, N818
    message = "Expected Ledger Ethereum app not open"


class LedgerCancel(LedgerError):  # noqa: D101, N818
    message = "Action cancelled by the user"


class LedgerInvalidADPU(LedgerError):  # noqa: D101, N818
    message = "Internal error.  Invalid data unit sent to ledger."


class LedgerInvalid(LedgerError):  # noqa: D101, N818
    message = 'Invalid data sent to ledger or "blind signing" is not enabled'


ERROR_CODE_EXCEPTIONS: Mapping[LedgerErrorCodes, type[LedgerError]] = {
    LedgerErrorCodes.UKNOWN: LedgerNotFound,
    LedgerErrorCodes.DEVICE_LOCKED: LedgerLocked,
    LedgerErrorCodes.APP_SLEEP: LedgerAppNotOpened,
    LedgerErrorCodes.APP_NOT_STARTED: LedgerAppNotOpened,
    LedgerErrorCodes.APP_NOT_FOUND: LedgerAppNotOpened,
    LedgerErrorCodes.CANCELED_BY_USER: LedgerCancel,
    LedgerErrorCodes.APDU_SIZE_MISMATCH: LedgerInvalidADPU,
    LedgerErrorCodes.DECLINED: LedgerCancel,
    LedgerErrorCodes.INVALID_DATA: LedgerInvalid,
}
