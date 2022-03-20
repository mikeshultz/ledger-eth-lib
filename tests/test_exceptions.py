""" Test that exceptions are translated/rendered correctly """
from ledgerblue.commException import CommException

from ledgereth.comms import dongle_send
from ledgereth.exceptions import (
    LedgerAppNotOpened,
    LedgerCancel,
    LedgerError,
    LedgerInvalid,
    LedgerLocked,
    LedgerNotFound,
)


def test_comms_exception(yield_dongle):
    with yield_dongle(exception=CommException("TEST", 0xFFFF, 0x00)) as dongle:
        try:
            dongle_send(dongle, "GET_CONFIGURATION")
            assert False
        except Exception as err:
            assert isinstance(err, LedgerError), f"Unexpected exception: {type(err)}"


def test_comms_exception_invalid(yield_dongle):
    with yield_dongle(exception=CommException("TEST", 0x6A80, 0x00)) as dongle:
        try:
            dongle_send(dongle, "SIGN_TX_FIRST_DATA")
            assert False
        except Exception as err:
            assert isinstance(err, LedgerInvalid), f"Unexpected exception: {type(err)}"


def test_comms_not_found(yield_dongle):
    with yield_dongle(exception=CommException("TEST", 0x6F00, 0x00)) as dongle:
        try:
            dongle_send(dongle, "GET_DEFAULT_ADDRESS_NO_CONFIRM")
            assert False
        except Exception as err:
            assert isinstance(err, LedgerNotFound), f"Unexpected exception: {type(err)}"


def test_comms_exception_locked(yield_dongle):
    with yield_dongle(exception=CommException("TEST", 0x6B0C, 0x00)) as dongle:
        try:
            dongle_send(dongle, "SIGN_TX_FIRST_DATA")
            assert False
        except Exception as err:
            assert isinstance(err, LedgerLocked), f"Unexpected exception: {type(err)}"


def test_comms_app_not_open(yield_dongle):
    with yield_dongle(exception=CommException("TEST", 0x6804, 0x00)) as dongle:
        try:
            dongle_send(dongle, "SIGN_TX_FIRST_DATA")
            assert False
        except Exception as err:
            assert isinstance(
                err, LedgerAppNotOpened
            ), f"Unexpected exception: {type(err)}"

    with yield_dongle(exception=CommException("TEST", 0x6D00, 0x00)) as dongle:
        try:
            dongle_send(dongle, "SIGN_TX_FIRST_DATA")
            assert False
        except Exception as err:
            assert isinstance(
                err, LedgerAppNotOpened
            ), f"Unexpected exception: {type(err)}"

    with yield_dongle(exception=CommException("TEST", 0x6D02, 0x00)) as dongle:
        try:
            dongle_send(dongle, "SIGN_TX_FIRST_DATA")
            assert False
        except Exception as err:
            assert isinstance(
                err, LedgerAppNotOpened
            ), f"Unexpected exception: {type(err)}"


def test_comms_user_cancel(yield_dongle):
    with yield_dongle(exception=CommException("TEST", 0x6982, 0x00)) as dongle:
        try:
            dongle_send(dongle, "SIGN_TX_FIRST_DATA")
            assert False
        except Exception as err:
            assert isinstance(err, LedgerCancel), f"Unexpected exception: {type(err)}"

    with yield_dongle(exception=CommException("TEST", 0x6985, 0x00)) as dongle:
        try:
            dongle_send(dongle, "SIGN_TX_FIRST_DATA")
            assert False
        except Exception as err:
            assert isinstance(err, LedgerCancel), f"Unexpected exception: {type(err)}"
