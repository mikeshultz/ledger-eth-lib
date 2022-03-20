from enum import IntEnum

from ledgerblue.commException import CommException


class LedgerErrorCodes(IntEnum):
    TX_TYPE_UNSUPPORTED = 0x6501
    OUTPUT_BUFFER_TOO_SMALL = 0x6502
    PLUGIN_ERROR = 0x6503
    INT_CONVERSION_ERROR = 0x6504
    # TODO: Following was also seen as app not being opened?
    INCORRECT_LENGTH = 0x6700
    CANCELED_BY_USER = 0x6982
    DECLINED = 0x6985
    INVALID_DATA = 0x6A80
    APP_SLEEP = 0x6804
    APP_NOT_STARTED = 0x6D00
    DEVICE_LOCKED = 0x6B0C
    OK = 0x9000
    # ledgerblue default code
    UKNOWN = 0x6F00
    # Inferred errors found through discovery
    APP_NOT_FOUND = 0x6D02


class LedgerError(Exception):
    message = "Unexpected Ledger error"

    def __init__(self, message=None):
        super().__init__(message or self.message)

    @classmethod
    def transalate_comm_exception(cls, exp: CommException):
        return ERROR_CODE_EXCEPTIONS.get(
            exp.sw, LedgerError(f"Unexpected error: {hex(exp.sw)}")
        )


class LedgerNotFound(LedgerError):
    message = "Unable to find Ledger device"


class LedgerLocked(LedgerError):
    message = "Ledger appears to be locked"


class LedgerAppNotOpened(LedgerError):
    message = "Expected Ledger Ethereum app not open"


class LedgerCancel(LedgerError):
    message = "Action cancelled by the user"


class LedgerInvalid(LedgerError):
    message = 'Invalid date sent to ledger or "blind signing" is not enabled'


ERROR_CODE_EXCEPTIONS = {
    LedgerErrorCodes.UKNOWN: LedgerNotFound,
    LedgerErrorCodes.DEVICE_LOCKED: LedgerLocked,
    LedgerErrorCodes.APP_SLEEP: LedgerAppNotOpened,
    LedgerErrorCodes.APP_NOT_STARTED: LedgerAppNotOpened,
    LedgerErrorCodes.APP_NOT_FOUND: LedgerAppNotOpened,
    LedgerErrorCodes.CANCELED_BY_USER: LedgerCancel,
    LedgerErrorCodes.DECLINED: LedgerCancel,
    LedgerErrorCodes.INVALID_DATA: LedgerInvalid,
}
