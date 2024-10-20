"""Types used by the ledgereth package."""

from collections.abc import Sequence

AccessList = list[tuple[bytes, list[int]]]
Text = str | bytes
Slot = str | int
AccessListInput = list[tuple[bytes, Sequence[Slot]]] | list[tuple[str, Sequence[Slot]]]
