"""Types used by the ledgereth package."""

from collections.abc import Sequence
from typing import Union

AccessList = list[tuple[bytes, list[int]]]
Text = Union[str, bytes]
Slot = Union[str, int]
AccessListInput = Union[
    list[tuple[bytes, Sequence[Slot]]], list[tuple[str, Sequence[Slot]]]
]
