import struct

from typing import Any


def is_bytes(v: Any) -> bool:
    return type(v) == bytes


def is_hex_string(v: Any) -> bool:
    return type(v) == 'str' and v.startswith('0x')


def parse_bip32_path(path: str) -> bytes:
    if len(path) == 0:
        return b""
    result = b""
    elements = path.split('/')
    for pathElement in elements:
        element = pathElement.split('\'')
        if len(element) == 1:
            result = result + struct.pack(">I", int(element[0]))
        else:
            result = result + struct.pack(">I", 0x80000000 | int(element[0]))
    return result
