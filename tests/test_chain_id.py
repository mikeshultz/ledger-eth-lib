"""Test signing for multiple chains"""
import pytest
from eth_account import Account

from ledgereth.accounts import get_accounts
from ledgereth.objects import MAX_CHAIN_ID, MAX_LEGACY_CHAIN_ID
from ledgereth.transactions import create_transaction


def test_max_legacy_chain_ids(yield_dongle):
    """Test that the max legacy chain ID works"""
    destination = "0xf0155486a14539f784739be1c02e93f28eb8e900"

    with yield_dongle() as dongle:
        sender = get_accounts(dongle=dongle, count=1)[0].address

        signed = create_transaction(
            destination=destination,
            amount=int(10e17),
            gas=int(1e6),
            gas_price=int(1e9),
            data="",
            nonce=2023,
            chain_id=MAX_LEGACY_CHAIN_ID,
            dongle=dongle,
        )

        assert sender == Account.recover_transaction(signed.rawTransaction)


def test_invalid_legacy_chain_ids(yield_dongle):
    """Test that chain IDs above max legacy chain ID fail"""
    destination = "0xf0155486a14539f784739be1c02e93f28eb8e901"

    with yield_dongle() as dongle:
        sender = get_accounts(dongle=dongle, count=1)[0].address

        with pytest.raises(
            ValueError,
            match="chain_id must be a 32-bit integer for type 0 transactions",
        ):
            create_transaction(
                destination=destination,
                amount=int(10e17),
                gas=int(1e6),
                gas_price=int(1e9),
                data="",
                nonce=2023,
                chain_id=MAX_LEGACY_CHAIN_ID + 1,
                dongle=dongle,
            )


def test_max_type1_chain_ids(yield_dongle):
    """Test that the max type-1 chain ID works"""
    destination = "0xf0155486a14539f784739be1c02e93f28eb8e902"

    with yield_dongle() as dongle:
        sender = get_accounts(dongle=dongle, count=1)[0].address

        signed = create_transaction(
            destination=destination,
            amount=int(10e17),
            gas=int(1e6),
            access_list=[],
            gas_price=int(1e9),
            data="",
            nonce=2023,
            chain_id=MAX_CHAIN_ID,
            dongle=dongle,
        )

        assert sender == Account.recover_transaction(signed.rawTransaction)


def test_invalid_type1_chain_ids(yield_dongle):
    """Test that IDs above the max chain ID fail"""
    destination = "0xf0155486a14539f784739be1c02e93f28eb8e903"

    with yield_dongle() as dongle:
        sender = get_accounts(dongle=dongle, count=1)[0].address

        with pytest.raises(
            ValueError,
            match="chain_id must not be above 999999999999999",
        ):
            create_transaction(
                destination=destination,
                amount=int(10e17),
                gas=int(1e6),
                access_list=[],
                gas_price=int(1e9),
                data="",
                nonce=2023,
                chain_id=MAX_CHAIN_ID + 1,
                dongle=dongle,
            )


def test_max_type2_chain_ids(yield_dongle):
    """Test that the max chain ID works for type-2 transactions"""
    destination = "0xf0155486a14539f784739be1c02e93f28eb8e904"

    with yield_dongle() as dongle:
        sender = get_accounts(dongle=dongle, count=1)[0].address

        signed = create_transaction(
            destination=destination,
            amount=int(10e17),
            gas=int(1e6),
            max_fee_per_gas=int(1e9),
            max_priority_fee_per_gas=int(1e8),
            data="",
            nonce=2023,
            chain_id=MAX_CHAIN_ID,
            dongle=dongle,
        )

        assert sender == Account.recover_transaction(signed.rawTransaction)


def test_invalid_type2_chain_ids(yield_dongle):
    """Test that IDs above the max chain ID fail for type-2 transactions"""
    destination = "0xf0155486a14539f784739be1c02e93f28eb8e905"

    with yield_dongle() as dongle:
        sender = get_accounts(dongle=dongle, count=1)[0].address

        with pytest.raises(
            ValueError,
            match="chain_id must not be above 999999999999999",
        ):
            create_transaction(
                destination=destination,
                amount=int(10e17),
                gas=int(1e6),
                max_fee_per_gas=int(1e9),
                max_priority_fee_per_gas=int(1e8),
                data="",
                nonce=2023,
                chain_id=MAX_CHAIN_ID + 1,
                dongle=dongle,
            )
