"""
Test higher level message signing functionality
"""

from eth_account import Account
from eth_account.messages import encode_defunct, encode_typed_data

from ledgereth.accounts import get_accounts
from ledgereth.messages import sign_message, sign_typed_data_draft

from .fixtures import eip712_dict, large_message


def test_sign_message(yield_dongle):
    """Test signing an EIP-191 v0 style message"""
    message = b"I'm a little teapot"

    with yield_dongle() as dongle:
        sender = get_accounts(dongle=dongle, count=1)[0].address

        # Signs a message according to EIP-191
        signed = sign_message(message, dongle=dongle)

        assert signed.v in [27, 28]
        assert signed.r
        assert signed.s

        # encode_defunct packs the message with the "Ethereum Signed Message"
        # prefix and into an object that eth_account's recover_message expects
        signable = encode_defunct(message)
        vrs = (signed.v, signed.r, signed.s)
        assert sender == Account.recover_message(signable, vrs)


def test_sign_large_message(yield_dongle):
    """Test signing an EIP-191 v0 style message"""

    with yield_dongle() as dongle:
        sender = get_accounts(dongle=dongle, count=1)[0].address

        # Signs a message according to EIP-191
        signed = sign_message(large_message, dongle=dongle)

        assert signed.v in [27, 28]
        assert signed.r
        assert signed.s

        # encode_defunct packs the message with the "Ethereum Signed Message"
        # prefix and into an object that eth_account's recover_message expects
        signable = encode_defunct(text=large_message)
        vrs = (signed.v, signed.r, signed.s)
        assert sender == Account.recover_message(signable, vrs)


def test_sign_typed_data(yield_dongle):
    """Test signing an EIP-712 typed data"""
    signable = encode_typed_data(full_message=eip712_dict)

    # header/body is eth_account naming, presumably to be generic
    domain_hash = signable.header
    message_hash = signable.body

    with yield_dongle() as dongle:
        sender = get_accounts(dongle=dongle, count=1)[0].address

        # Signs a message according to EIP-712.
        signed = sign_typed_data_draft(domain_hash, message_hash, dongle=dongle)

        assert signed.v in [27, 28]
        assert signed.r
        assert signed.s

        vrs = (signed.v, signed.r, signed.s)
        assert sender == Account.recover_message(signable, vrs)
