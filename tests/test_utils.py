from ledgereth.constants import DEFAULT_PATH_ENCODED, DEFAULT_PATH_STRING
from ledgereth.utils import (
    decode_bip32_path,
    is_bip32_path,
    is_bytes,
    is_hex_string,
    parse_bip32_path,
)


def test_is_bytes():
    """Test is_bytes()"""
    assert is_bytes(b"0xdeadbeef")


def test_is_hex_string():
    """Test is_hex_string()"""
    assert is_hex_string("0xdeadbeef")


def test_is_bip32_path():
    """Test is_bip32_path() against a known constant"""
    assert is_bip32_path(DEFAULT_PATH_STRING)


def test_path_encoding():
    """Test that encode/decode of BIP-32 paths work"""
    encoded = parse_bip32_path(DEFAULT_PATH_STRING)
    assert encoded == DEFAULT_PATH_ENCODED
    decoded = decode_bip32_path(encoded)
    assert decoded == DEFAULT_PATH_STRING
