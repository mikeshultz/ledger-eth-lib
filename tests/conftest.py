import os
from contextlib import contextmanager

import pytest
from ledgerblue.comm import getDongle

USE_REAL_DONGLE = os.environ.get("USE_REAL_DONGLE") is not None


class MockDongle:
    """Attempts to act like an actual ledger dongle for the sake of not requiring user-intervention
    for every single test with a real ledger attached.
    """
    def __init__(self): pass

    def exchange(self, apdu, timeout=20000):
        raise NotImplementedError('LOL')


def getMockDongle():
    return MockDongle()


@pytest.fixture
def yield_dongle():
    @contextmanager
    def yield_yield_dongle():
        if USE_REAL_DONGLE:
            dongle = getDongle(True)
            yield dongle
            dongle.close()
        else:
            yield getMockDongle()

    return yield_yield_dongle
