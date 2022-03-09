import re
import struct
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

from eth_utils import decode_hex

from ledgereth.constants import DEFAULTS

# 44'/60'/0'/0/x
BIP32_ETH_PATTERN = r"^44'/60'/[0-9]+'/[0-9]+/[0-9]+$"
BIP32_LEGACY_LEDGER_PATTERN = r"^44'/60'/[0-9]+'/[0-9]+$"

COERCERS: Dict[Type, Callable] = {int: lambda v: int.from_bytes(v, "big")}


def is_bytes(v: Any) -> bool:
    return isinstance(v, bytes)


def is_optional_bytes(v: Optional[Any]) -> bool:
    return v is None or is_bytes(v)


def is_hex_string(v: Any) -> bool:
    return isinstance(v, str) and v.startswith("0x")


def is_bip32_path(path: str) -> bool:
    """Detect if a string a bip32 path that can be given to a Ledger device"""
    return (
        re.match(BIP32_ETH_PATTERN, path) is not None
        or re.match(BIP32_LEGACY_LEDGER_PATTERN, path) is not None
    )


def chunks(it: bytes, chunk_size: int) -> Generator[bytes, None, None]:
    """Iterate bytes(it) into chunks of chunk_size"""

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


def decode_access_list(
    access_list: Collection[Tuple[bytes, Collection[bytes]]]
) -> List[Tuple[bytes, Tuple[int, ...]]]:
    """Decode an access list into friendly Python types"""
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
    access_list: Collection[Dict[str, Union[str, Collection[str]]]]
) -> List[Tuple[bytes, Tuple[int, ...]]]:
    work_list = []

    if not access_list or len(access_list) < 1:
        return []

    for idx, item in enumerate(access_list):
        if "address" not in item:
            raise ValueError(f"Access list item at position {idx} missing address")

        if "storageKeys" not in item:
            raise ValueError(f"Access list item at position {idx} missing storageKeys")

        assert type(item["address"]) == str

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


def coerce_access_list(access_list):
    """Validate and type coerce an access list from Python friendly values to
    values for RLP encoding"""
    if access_list is None:
        return []

    if type(access_list) != list:
        raise ValueError("Expected access_list to be a list")

    for i, rule in enumerate(access_list):
        if type(rule) not in (list, tuple):
            raise ValueError("Expected access_list rules to be a list or tuple")

        if type(rule) == tuple:
            access_list[i] = list(rule)

        target, slots = rule

        if is_hex_string(target):
            access_list[i][0] = decode_hex(target)
        elif type(target) != bytes:
            raise ValueError(
                f"Unexpected type ({type(target)}) for access_list address at index {i}"
            )

        for j, slot in enumerate(slots):
            if is_hex_string(slot):
                access_list[i][1][j] = int(slot, 16)
            elif type(slot) != int:
                raise ValueError(
                    f"Unexpected type ({type(slot)}) for access_list slot at index {j}"
                )

    return access_list


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
