""" Test that exceptions are translated/rendered correctly """
import pytest

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
        with pytest.raises(LedgerError) as err:
            dongle_send(dongle, "GET_CONFIGURATION")

        assert "Unexpected error" in str(err.value)


def test_comms_exception_invalid(yield_dongle):
    with yield_dongle(exception=CommException("TEST", 0x6A80, 0x00)) as dongle:
        with pytest.raises(LedgerInvalid) as err:
            dongle_send(dongle, "SIGN_TX_FIRST_DATA")

        assert "Invalid data" in str(err.value)


def test_comms_not_found(yield_dongle):
    with yield_dongle(exception=CommException("TEST", 0x6F00, 0x00)) as dongle:
        with pytest.raises(LedgerNotFound) as err:
            dongle_send(dongle, "GET_DEFAULT_ADDRESS_NO_CONFIRM")

        assert "Unable to find Ledger" in str(err.value)


def test_comms_exception_locked(yield_dongle):
    with yield_dongle(exception=CommException("TEST", 0x6B0C, 0x00)) as dongle:
        with pytest.raises(LedgerLocked) as err:
            dongle_send(dongle, "SIGN_TX_FIRST_DATA")

        assert "locked" in str(err.value)


def test_comms_app_not_open(yield_dongle):
    with yield_dongle(exception=CommException("TEST", 0x6804, 0x00)) as dongle:
        with pytest.raises(LedgerAppNotOpened) as err:
            dongle_send(dongle, "SIGN_TX_FIRST_DATA")

        assert "Ethereum app" in str(err.value)

    with yield_dongle(exception=CommException("TEST", 0x6D00, 0x00)) as dongle:
        with pytest.raises(LedgerAppNotOpened) as err:
            dongle_send(dongle, "SIGN_TX_FIRST_DATA")

        assert "Ethereum app" in str(err.value)

    with yield_dongle(exception=CommException("TEST", 0x6D02, 0x00)) as dongle:
        with pytest.raises(LedgerAppNotOpened) as err:
            dongle_send(dongle, "SIGN_TX_FIRST_DATA")

        assert "Ethereum app" in str(err.value)


def test_comms_user_cancel(yield_dongle):
    with yield_dongle(exception=CommException("TEST", 0x6982, 0x00)) as dongle:
        with pytest.raises(LedgerCancel) as err:
            dongle_send(dongle, "SIGN_TX_FIRST_DATA")

        assert "cancelled" in str(err.value)

    with yield_dongle(exception=CommException("TEST", 0x6985, 0x00)) as dongle:
        with pytest.raises(LedgerCancel) as err:
            dongle_send(dongle, "SIGN_TX_FIRST_DATA")

        assert "cancelled" in str(err.value)


def test_comms_unknown_error(yield_dongle):
    with yield_dongle(exception=CommException("TEST", 0xEEEE, 0x00)) as dongle:
        with pytest.raises(LedgerError) as err:
            dongle_send(dongle, "SIGN_TX_FIRST_DATA")

        assert "UNKNOWN" in str(err.value)
