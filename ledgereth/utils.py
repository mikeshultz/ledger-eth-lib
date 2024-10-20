"""Utility functions for ledgereth."""

import re
import struct
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    Generator,
    List,
    Tuple,
    Type,
    Union,
)

from eth_utils.hexadecimal import decode_hex

from ledgereth.constants import DEFAULTS
from ledgereth.types import AccessList, AccessListInput

# 44'/60'/0'/0/x
BIP32_ETH_PATTERN = r"^44'/60'/[0-9]+'/[0-9]+/[0-9]+$"
BIP32_LEGACY_LEDGER_PATTERN = r"^44'/60'/[0-9]+'/[0-9]+$"

COERCERS: Dict[Type, Callable] = {int: lambda v: int.from_bytes(v, "big")}


def is_bytes(v: Any) -> bool:
    """Detect if a string is a byte string."""
    return isinstance(v, bytes)


def is_optional_bytes(v: Any | None) -> bool:
    """Detect if a string is a byte string or None."""
    return v is None or is_bytes(v)


def is_hex_string(v: Any) -> bool:
    """Detect if a string is a hex string."""
    return isinstance(v, str) and v.startswith("0x")


def is_bip32_path(path: str) -> bool:
    """Detect if a string a bip32 path that can be given to a Ledger device."""
    return (
        re.match(BIP32_ETH_PATTERN, path) is not None
        or re.match(BIP32_LEGACY_LEDGER_PATTERN, path) is not None
    )


def chunks(it: bytes, chunk_size: int) -> Generator[bytes, None, None]:
    """Iterate bytes(it) into chunks of chunk_size."""
    if not isinstance(it, bytes):
        raise TypeError("iterable argument must be type bytes")

    it_size = len(it)

    if it_size <= chunk_size:
        yield it
    else:
        chunk_count, remainder = divmod(it_size, chunk_size)
        for i in range(0, chunk_count * chunk_size, chunk_size):
            yield it[i : i + chunk_size]
        final_offset = chunk_count * chunk_size
        yield it[final_offset : final_offset + remainder]


def parse_bip32_path(path: str) -> bytes:
    """Parse a BIP-32/44 string path into bytes."""
    if not path:
        return b""

    result = b""
    elements = path.split("/")

    for path_element in elements:
        element = path_element.split("'")

        # Wihout tick (') == 1
        if len(element) == 1:
            # "public" BIP-44 derivation
            result = result + struct.pack(">I", int(element[0]))
        else:
            # "private" BIP-44 derivation
            result = result + struct.pack(">I", 0x80000000 | int(element[0]))

    return result


def decode_bip32_path(path: bytes) -> str:
    """Decode a BIP-32/44 path from bytes."""
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


def decode_access_list(
    access_list: Collection[Tuple[bytes, Collection[bytes]]],
) -> List[Tuple[bytes, Tuple[int, ...]]]:
    """Decode an access list into friendly Python types."""
    work_list = []

    if not access_list or len(access_list) < 1:
        return []

    for item in access_list:
        work_slot_list = []

        for slot in item[1]:
            work_slot_list.append(int.from_bytes(slot, "big"))

        work_list.append((item[0], tuple(work_slot_list)))

    return work_list


def decode_web3_access_list(
    access_list: Collection[dict[str, str | Collection[str]]],
) -> AccessList:
    """Decode a web3.py access list into friendly Python types."""
    work_list = []

    if not access_list or len(access_list) < 1:
        return []

    for idx, item in enumerate(access_list):
        if "address" not in item:
            raise ValueError(f"Access list item at position {idx} missing address")

        if "storageKeys" not in item:
            raise ValueError(f"Access list item at position {idx} missing storageKeys")

        assert isinstance(item["address"], str)

        work_list.append(
            (
                decode_hex(item["address"]),
                tuple(
                    map(
                        lambda v: int.from_bytes(decode_hex(v), "big"),
                        tuple(item.get("storageKeys", [])),
                    )
                ),
            )
        )

    return work_list


def coerce_access_list(access_list: AccessList | AccessListInput) -> AccessList:
    """Create RLP access list.

    Validates and type coerce an access list from Python friendly values to values for
    RLP encoding.
    """
    if access_list is None:
        return list()

    if not isinstance(access_list, list):
        raise ValueError("Expected access_list to be a list")

    acl: AccessList = []

    for i, rule in enumerate(access_list):
        if type(rule) not in (list, tuple):
            raise ValueError("Expected access_list rules to be a list or tuple")

        if not isinstance(rule, tuple):
            raise ValueError("Expected access_list rule to be a tuple")

        target, slots = rule

        if is_hex_string(target):
            # Above acts as a TypeGuard
            assert isinstance(target, str)
            target = decode_hex(target)
        elif not isinstance(target, bytes):
            raise ValueError(
                f"Unexpected type ({type(target)}) for access_list address at index {i}"
            )

        acl.append((target, list()))

        for j, slot in enumerate(slots):
            if is_hex_string(slot):
                # Above acts as a TypeGuard
                assert isinstance(slot, str)
                acl[i][1].append(int(slot, 16))
            elif not isinstance(slot, int):
                raise ValueError(
                    f"Unexpected type ({type(slot)}) for access_list slot at index {j}"
                )

    return acl


def coerce_list_types(
    types: List[type | None], to_coerce: List[Union[Any, None]]
) -> List[Any]:
    """Coerce types of a list to given types in order."""
    for i, v in enumerate(to_coerce):
        # SKIP!
        if types[i] is None:
            continue

        # Only way to get mypy to chill was to assign to its own var
        this_type = types[i]
        assert this_type is not None

        # Some things don't transalate, like b'' being 0
        if not v:
            to_coerce[i] = DEFAULTS[this_type]
        else:
            if types[i] in COERCERS:
                to_coerce[i] = COERCERS[this_type](v)
            else:
                to_coerce[i] = this_type(v)

    return to_coerce
