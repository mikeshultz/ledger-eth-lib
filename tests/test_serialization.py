"""
Test objects and serialization
"""
from eth_utils import decode_hex, is_checksum_address

from ledgereth.constants import DEFAULT_CHAIN_ID, DEFAULTS
from ledgereth.objects import (
    LedgerAccount,
    SignedTransaction,
    SignedType1Transaction,
    SignedType2Transaction,
    Transaction,
    Type1Transaction,
    Type2Transaction,
)
from ledgereth.transactions import create_transaction, sign_transaction


def test_account():
    """Test basic LedgerAccount behavior"""
    alice = LedgerAccount(
        "44'/60'/0'/0/0", "0x1D35202a64A06633A793D43cEB82C1D54fC89233"
    )
    bob = LedgerAccount("44'/60'/1'/0/0", "0x1d35202a64a06633a793d43ceb82c1d54fc89233")

    assert alice.address in repr(alice)
    assert alice.address == bob.address
    assert alice.path != bob.path
    assert alice.path_encoded != bob.path_encoded
    assert alice != bob
    assert hash(alice) != hash(bob)
    assert is_checksum_address(alice.address)
    assert is_checksum_address(bob.address)


def test_legacy_serialization(yield_dongle):
    """Test serialization of legacy Transaction objects"""
    destination = decode_hex("0xf0155486a14539f784739be1c02e93f28eb8e960")
    amount = int(1e17)
    gas_limit = int(1e6)
    gas_price = int(1e9)
    data = b"0xdeadbeef"
    nonce = 666

    tx = Transaction(
        destination=destination,
        amount=amount,
        gas_limit=gas_limit,
        gas_price=gas_price,
        data=data,
        nonce=nonce,
    )

    assert tx.nonce == nonce
    assert tx.gas_price == gas_price
    assert tx.gas_limit == gas_limit
    assert tx.destination == destination
    assert tx.amount == amount
    assert tx.data == data
    assert tx.chain_id == DEFAULT_CHAIN_ID
    assert tx.dummy1 == DEFAULTS[int]
    assert tx.dummy2 == DEFAULTS[int]


def test_signed_legacy_serialization(yield_dongle):
    """Test serialization of legacy SignedTransaction objects"""
    destination = decode_hex("0xf0155486a14539f784739be1c02e93f28eb8e960")
    amount = int(1e17)
    gas_limit = int(1e6)
    gas_price = int(1e9)
    data = b"0xdeadbeef"
    nonce = 666
    r = int.from_bytes(
        b"#\xdc\x11\x1d|:\xd1\xdf\x98\x06\xce\x1e\x8e\xb4\xf5_W\xdb\xa1\x173\x9cT^u\x93\xd1\xf6\xc3\xb0&b",
        "big",
    )
    s = int.from_bytes(
        b"3,9\xdc\xd3\x98\xea4\xa4\x8b\x87\x18\x98\xd5\x89\xf5_\xc4\xc7\xbc\xe0\x05b\xfbg\x0c\x97.~\x1b\x07 ",
        "big",
    )
    v = 1

    tx = SignedTransaction(
        destination=destination,
        amount=amount,
        gas_limit=gas_limit,
        gas_price=gas_price,
        data=data,
        nonce=nonce,
        v=v,
        r=r,
        s=s,
    )

    assert tx.nonce == nonce
    assert tx.gas_price == gas_price
    assert tx.gas_limit == gas_limit
    assert tx.destination == destination
    assert tx.amount == amount
    assert tx.data == data
    assert tx.r == r
    assert tx.s == s
    assert tx.v == v
    assert tx.raw_transaction()


def test_type1_serialization(yield_dongle):
    """Test serialization of Type1Transaction objects"""
    destination = decode_hex("0xf0155486a14539f784739be1c02e93f28eb8e960")
    amount = int(1e17)
    gas_limit = int(1e6)
    gas_price = int(1e9)
    data = b"0xdeadbeef"
    nonce = 666
    access_list = [[destination, [10, 200, 3000]]]

    tx = Type1Transaction(
        chain_id=DEFAULT_CHAIN_ID,
        destination=destination,
        amount=amount,
        gas_limit=gas_limit,
        gas_price=gas_price,
        data=data,
        nonce=nonce,
        access_list=access_list,
    )

    assert tx.nonce == nonce
    assert tx.gas_price == gas_price
    assert tx.gas_limit == gas_limit
    assert tx.destination == destination
    assert tx.amount == amount
    assert tx.data == data
    assert tx.chain_id == DEFAULT_CHAIN_ID
    assert type(tx.access_list) == tuple
    assert len(tx.access_list) == len(access_list)
    assert type(tx.access_list[0]) == tuple
    assert tx.access_list[0][0] == destination
    assert len(tx.access_list[0][1]) == len(access_list[0][1])


def test_signed_type1_serialization(yield_dongle):
    """Test serialization of SignedType1Transaction objects"""
    destination = decode_hex("0xf0155486a14539f784739be1c02e93f28eb8e960")
    amount = int(1e17)
    gas_limit = int(1e6)
    gas_price = int(1e9)
    data = b"0xdeadbeef"
    nonce = 666
    access_list = [[destination, [10, 200, 3000]]]
    r = int.from_bytes(
        b"#\xdc\x11\x1d|:\xd1\xdf\x98\x06\xce\x1e\x8e\xb4\xf5_W\xdb\xa1\x173\x9cT^u\x93\xd1\xf6\xc3\xb0&b",
        "big",
    )
    s = int.from_bytes(
        b"3,9\xdc\xd3\x98\xea4\xa4\x8b\x87\x18\x98\xd5\x89\xf5_\xc4\xc7\xbc\xe0\x05b\xfbg\x0c\x97.~\x1b\x07 ",
        "big",
    )
    v = 1

    tx = SignedType1Transaction(
        chain_id=DEFAULT_CHAIN_ID,
        destination=destination,
        amount=amount,
        gas_limit=gas_limit,
        gas_price=gas_price,
        data=data,
        nonce=nonce,
        access_list=access_list,
        sender_r=r,
        sender_s=s,
        y_parity=v,
    )

    assert tx.nonce == nonce
    assert tx.gas_price == gas_price
    assert tx.gas_limit == gas_limit
    assert tx.destination == destination
    assert tx.amount == amount
    assert tx.data == data
    assert tx.chain_id == DEFAULT_CHAIN_ID
    assert tx.sender_r == r
    assert tx.sender_s == s
    assert tx.y_parity == v
    assert type(tx.access_list) == tuple
    assert len(tx.access_list) == len(access_list)
    assert type(tx.access_list[0]) == tuple
    assert tx.access_list[0][0] == destination
    assert len(tx.access_list[0][1]) == len(access_list[0][1])
    assert tx.raw_transaction()


def test_type2_serialization(yield_dongle):
    """Test serialization of Type2Transaction objects"""
    destination = decode_hex("0xf0155486a14539f784739be1c02e93f28eb8e960")
    amount = int(1e17)
    gas_limit = int(1e6)
    max_fee_per_gas = int(10e9)
    max_priority_fee_per_gas = int(1e9)
    data = b"0xdeadbeef"
    nonce = 666
    access_list = [[destination, [10, 200, 3000]]]

    tx = Type2Transaction(
        chain_id=DEFAULT_CHAIN_ID,
        destination=destination,
        amount=amount,
        gas_limit=gas_limit,
        max_fee_per_gas=max_fee_per_gas,
        max_priority_fee_per_gas=max_priority_fee_per_gas,
        data=data,
        nonce=nonce,
        access_list=access_list,
    )

    assert tx.nonce == nonce
    assert tx.max_fee_per_gas == max_fee_per_gas
    assert tx.max_priority_fee_per_gas == max_priority_fee_per_gas
    assert tx.gas_limit == gas_limit
    assert tx.destination == destination
    assert tx.amount == amount
    assert tx.data == data
    assert tx.chain_id == DEFAULT_CHAIN_ID
    assert type(tx.access_list) == tuple
    assert len(tx.access_list) == len(access_list)
    assert type(tx.access_list[0]) == tuple
    assert tx.access_list[0][0] == destination
    assert len(tx.access_list[0][1]) == len(access_list[0][1])


def test_signed_type2_serialization(yield_dongle):
    """Test serialization of SignedType2Transaction objects"""
    destination = decode_hex("0xf0155486a14539f784739be1c02e93f28eb8e960")
    amount = int(1e17)
    gas_limit = int(1e6)
    max_fee_per_gas = int(10e9)
    max_priority_fee_per_gas = int(1e9)
    data = b"0xdeadbeef"
    nonce = 666
    access_list = [[destination, [10, 200, 3000]]]
    r = int.from_bytes(
        b"#\xdc\x11\x1d|:\xd1\xdf\x98\x06\xce\x1e\x8e\xb4\xf5_W\xdb\xa1\x173\x9cT^u\x93\xd1\xf6\xc3\xb0&b",
        "big",
    )
    s = int.from_bytes(
        b"3,9\xdc\xd3\x98\xea4\xa4\x8b\x87\x18\x98\xd5\x89\xf5_\xc4\xc7\xbc\xe0\x05b\xfbg\x0c\x97.~\x1b\x07 ",
        "big",
    )
    v = 1

    tx = SignedType2Transaction(
        chain_id=DEFAULT_CHAIN_ID,
        destination=destination,
        amount=amount,
        gas_limit=gas_limit,
        max_fee_per_gas=max_fee_per_gas,
        max_priority_fee_per_gas=max_priority_fee_per_gas,
        data=data,
        nonce=nonce,
        access_list=access_list,
        sender_r=r,
        sender_s=s,
        y_parity=v,
    )

    assert tx.nonce == nonce
    assert tx.max_fee_per_gas == max_fee_per_gas
    assert tx.max_priority_fee_per_gas == max_priority_fee_per_gas
    assert tx.gas_limit == gas_limit
    assert tx.destination == destination
    assert tx.amount == amount
    assert tx.data == data
    assert tx.chain_id == DEFAULT_CHAIN_ID
    assert tx.sender_r == r
    assert tx.sender_s == s
    assert tx.y_parity == v
    assert type(tx.access_list) == tuple
    assert len(tx.access_list) == len(access_list)
    assert type(tx.access_list[0]) == tuple
    assert tx.access_list[0][0] == destination
    assert len(tx.access_list[0][1]) == len(access_list[0][1])
    assert tx.raw_transaction()
