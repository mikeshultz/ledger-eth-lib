import re
import rlp
import binascii
from eth_utils import encode_hex, decode_hex

from ledgereth.constants import DEFAULT_PATH_ENCODED
from ledgereth.objects import Transaction, SignedTransaction
from ledgereth.comms import (
    chunks,
    dongle_send,
    dongle_send_data,
    decode_response_address,
    decode_response_version_from_config,
)
from ledgereth.utils import parse_bip32_path

GET_CONFIGURATION = 'GET_CONFIGURATION'
GET_DEFAULT_ADDRESS_NO_CONFIRM = 'GET_DEFAULT_ADDRESS_NO_CONFIRM'
GET_ADDRESS_NO_CONFIRM = 'GET_ADDRESS_NO_CONFIRM'
SIGN_TX_FIRST_DATA = 'SIGN_TX_FIRST_DATA'


def test_comms_config(yield_dongle):
    with yield_dongle() as dongle:
        resp = dongle_send(dongle, GET_CONFIGURATION)

        assert type(resp) == bytearray

        version = decode_response_version_from_config(resp)

        assert type(version) == str
        assert len(version) >= 5
        assert re.match(r'^([0-9]+)\.([0-9]+)\.([0-9]+)$', version) is not None


def test_comms_account(yield_dongle):
    with yield_dongle() as dongle:
        resp = dongle_send(dongle, GET_DEFAULT_ADDRESS_NO_CONFIRM)

        assert type(resp) == bytearray

        address = decode_response_address(resp)

        assert type(address) == str
        assert len(address) == 42
        assert address.startswith('0x')


def test_comms_multiple_accounts(yield_dongle):
    with yield_dongle() as dongle:
        for i in range(5):
            path = parse_bip32_path("44'/60'/0'/0/{}".format(i))
            lc = len(path).to_bytes(1, 'big')
            data = (len(path) // 4).to_bytes(1, 'big') + path
            resp = dongle_send_data(
                dongle,
                GET_ADDRESS_NO_CONFIRM,
                data,
                Lc=lc
            )

            assert type(resp) == bytearray

            address = decode_response_address(resp)

            assert type(address) == str
            assert len(address) == 42
            assert address.startswith('0x')


def test_comms_sign_small_tx(yield_dongle):
    CHAIN_ID = 0  # eh?

    with yield_dongle() as dongle:
        tx = Transaction(
            to=decode_hex('0xf0155486a14539f784739be1c02e93f28eb8e960'),
            value=int(1e17),
            startgas=int(1e6),
            gasprice=int(1e9),
            data=b"",
            nonce=0,
        )
        encoded_tx = rlp.encode(tx, Transaction)
        # TODO: Never did figure out what the path count prefix was about
        payload = (
            len(DEFAULT_PATH_ENCODED) // 4
        ).to_bytes(1, 'big') + DEFAULT_PATH_ENCODED + encoded_tx
        vrsbytes = dongle_send_data(
            dongle,
            SIGN_TX_FIRST_DATA,
            payload,
            Lc=int(len(payload)).to_bytes(1, 'big')
        )

        assert type(vrsbytes) == bytearray

        if (CHAIN_ID*2 + 35) + 1 > 255:
            ecc_parity = vrsbytes[0] - ((CHAIN_ID*2 + 35) % 256)
            v = (CHAIN_ID*2 + 35) + ecc_parity
        else:
            v = vrsbytes[0]

        r = binascii.hexlify(vrsbytes[1:33])
        s = binascii.hexlify(vrsbytes[33:65])

        assert v in (27, 28)  # 0, 1 okay?
        assert r  # TODO: What's an invalid value here?
        assert s  # TODO: What's an invalid value here?


def test_comms_sign_large_tx(yield_dongle):
    CHAIN_ID = 0  # eh?
    chunk_count = 0
    retval = None
    txdata = '0x29589f61000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000001628c8b11e853c40000000000000000000000000f5d2fb29fb7d3cfee444a200298f468908cc9420000000000000000000000009283099a29556fcf8fff5b2cea2d4f67cb7a7a8b8000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000107345af81329fe1a05000000000000000000000000440bbd6a888a36de6e2f6a25f65bc4e16874faa9000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000045045524d00000000000000000000000000000000000000000000000000000000'

    with yield_dongle() as dongle:
        tx = Transaction(
            to=decode_hex('0xf0155486a14539f784739be1c02e93f28eb8e960'),
            value=int(1e17),
            startgas=int(1e6),
            gasprice=int(1e9),
            data=decode_hex(txdata),
            nonce=1,
        )
        encoded_tx = rlp.encode(tx, Transaction)
        payload = (
            len(DEFAULT_PATH_ENCODED) // 4
        ).to_bytes(1, 'big') + DEFAULT_PATH_ENCODED + encoded_tx

        for chunk in chunks(payload):
            chunk_size = len(chunk)
            if chunk_count == 0:
                retval = dongle_send_data(
                    dongle,
                    'SIGN_TX_FIRST_DATA',
                    chunk,
                    Lc=chunk_size.to_bytes(1, 'big')
                )
            else:
                retval = dongle_send_data(
                    dongle,
                    'SIGN_TX_SECONDARY_DATA',
                    chunk,
                    Lc=chunk_size.to_bytes(1, 'big')
                )
            chunk_count += 1

        if (CHAIN_ID*2 + 35) + 1 > 255:
            ecc_parity = retval[0] - ((CHAIN_ID*2 + 35) % 256)
            v = (CHAIN_ID*2 + 35) + ecc_parity
        else:
            v = retval[0]

        r = binascii.hexlify(retval[1:33])
        s = binascii.hexlify(retval[33:65])

        assert v in (27, 28)  # 0, 1 okay?
        assert r  # TODO: What's an invalid value here?
        assert s  # TODO: What's an invalid value here?

        signed_tx_obj = SignedTransaction(
            to=decode_hex('0x818e6fecd516ecc3849daf6845e3ec868087b755'),
            value=int(1e17),
            startgas=int(4e6),
            gasprice=int(3e9),
            data=decode_hex(txdata),
            nonce=1,
            v=v,
            r=int(r, 16),
            s=int(s, 16)
        )

        raw_tx = encode_hex(rlp.encode(signed_tx_obj))

        assert raw_tx.startswith('0x')
        assert len(raw_tx) > 32  # TODO: Shrug


# def test_comms_sign_small_message(yield_dongle): pass


# def test_comms_sign_large_message(yield_dongle): pass
