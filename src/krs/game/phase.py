from __future__ import annotations

from enum import Enum, auto


class Phase(Enum):
    """
    Turn phase.

    Version 1 supports Goldfish simulation only.
    Combat phases are intentionally omitted.
    """

    UNTAP = auto()
    UPKEEP = auto()
    DRAW = auto()
    MAIN = auto()
    END = auto()

    def __str__(self) -> str:
        return self.name