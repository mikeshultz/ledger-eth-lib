import re
import struct
from typing import Any

# 44'/60'/0'/0/x
BIP32_ETH_PATTERN = r"^44'/60'/[0-9]+'/[0-9]+/[0-9]+$"
BIP32_LEGACY_LEDGER_PATTERN = r"^44'/60'/[0-9]+'/[0-9]+$"


def is_bytes(v: Any) -> bool:
    return isinstance(v, bytes)


def is_hex_string(v: Any) -> bool:
    return isinstance(v, str) and v.startswith("0x")


def is_bip32_path(path: str) -> bool:
    """Detect if a string a bip32 path that can be given to a Ledger device"""
    return (
        re.match(BIP32_ETH_PATTERN, path) is not None
        or re.match(BIP32_LEGACY_LEDGER_PATTERN, path) is not None
    )


def parse_bip32_path(path: str) -> bytes:
    if not path:
        return b""
    result = b""
    elements = path.split("/")
    for pathElement in elements:
        element = pathElement.split("'")
        if len(element) == 1:
            result = result + struct.pack(">I", int(element[0]))
        else:
            result = result + struct.pack(">I", 0x80000000 | int(element[0]))
    return result


def get_int_from_dict(d: Any, k: Any, default: int = None):
    """Get an int from a dict-like object"""
    if not hasattr(d, "get"):
        raise ValueError("Object given to get_int_from_dict is not dict-like")
    return d.get(k) or default
