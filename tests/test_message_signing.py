"""
Test higher level transaction functionality
"""
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import decode_hex

from ledgereth.accounts import get_accounts
from ledgereth.messages import sign_message

large_message = """
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


def test_sign_message(yield_dongle):
    """Test signing an EIP-191 style message"""
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
    """Test signing an EIP-191 style message"""

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
