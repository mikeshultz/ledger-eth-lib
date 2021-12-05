"""
Test higher level transaction functionality
"""
from eth_utils import decode_hex
from ledgereth.objects import Transaction
from ledgereth.transactions import create_transaction, sign_transaction


def test_pre_155_send(yield_dongle):
    """Test sending a transaction without EIP-155 (old style), without a chain
    ID"""
    # One can also use create_transaction(), this is ust to add some coverage
    tx = Transaction(
        to=decode_hex("0xf0155486a14539f784739be1c02e93f28eb8e960"),
        value=int(1e17),
        startgas=int(1e6),
        gasprice=int(1e9),
        data=b"",
        nonce=0,
    )
    signed = sign_transaction(tx)

    assert signed.v in (37, 38)
    assert signed.r
    assert signed.s


def test_mainnet_send(yield_dongle):
    """Test a mainnet transaction"""
    CHAIN_ID = 1

    signed = create_transaction(
        to="0xf0155486a14539f784739be1c02e93f28eb8e960",
        value=int(1e17),
        gas=int(1e6),
        gas_price=int(1e9),
        data="",
        nonce=0,
        chain_id=CHAIN_ID,
    )

    assert signed.v in [(CHAIN_ID * 2 + 35) + x for x in (0, 1)]
    assert signed.r
    assert signed.s


def test_rinkeby_send(yield_dongle):
    """Test a rinkeby transaction"""
    CHAIN_ID = 4

    signed = create_transaction(
        to="0xf0155486a14539f784739be1c02e93f28eb8e960",
        value=int(1e17),
        gas=int(1e6),
        gas_price=int(1e9),
        data="",
        nonce=0,
        chain_id=CHAIN_ID,
    )

    assert signed.v in [(CHAIN_ID * 2 + 35) + x for x in (0, 1)]
    assert signed.r
    assert signed.s