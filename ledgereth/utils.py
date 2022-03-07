import re
import struct
from typing import Any, Callable, Dict, List, Optional, Type

from ledgereth.constants import DEFAULTS

# 44'/60'/0'/0/x
BIP32_ETH_PATTERN = r"^44'/60'/[0-9]+'/[0-9]+/[0-9]+$"
BIP32_LEGACY_LEDGER_PATTERN = r"^44'/60'/[0-9]+'/[0-9]+$"

COERCERS: Dict[Type, Callable] = {int: lambda v: int.from_bytes(v, "big")}


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

        # Wihout tick (') == 1
        if len(element) == 1:
            # "public" BIP-44 derivation
            result = result + struct.pack(">I", int(element[0]))
        else:
            # "private" BIP-44 derivation
            result = result + struct.pack(">I", 0x80000000 | int(element[0]))

    return result


def decode_bip32_path(path: bytes) -> str:
    """Decode a BIP-32/44 path from bytes"""
    parts = []

    for i in range(0, len(path) // 4):
        idx = i * 4
        chunk = path[idx : idx + 4]
        result = struct.unpack(">I", chunk)

        if result[0] < 256:
            # "public" BIP-44 derivation
            parts.append(f"{result[0]}")
        else:
            # "private" BIP-44 derivation
            part = result[0] - (0x80000000 & result[0])
            parts.append(f"{part}'")

    return "/".join(parts)


def coerce_list_types(types: List[Type], to_coerce: List[Any]) -> List[Any]:
    """Coerce types of a list to given types in order"""

    for i, v in enumerate(to_coerce):
        # SKIP!
        if types[i] is None:
            continue

        # Some things don't transalate, like b'' being 0
        if not v:
            to_coerce[i] = DEFAULTS[types[i]]
        else:
            if types[i] in COERCERS:
                to_coerce[i] = COERCERS[types[i]](v)
            else:
                to_coerce[i] = types[i](v)

    return to_coerce
