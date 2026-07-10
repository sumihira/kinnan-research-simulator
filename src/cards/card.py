from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class Card:
    """
    Immutable card definition.

    A Card represents printed card information only.
    Runtime state belongs to Permanent.
    """

    id: str

    name: str

    mana_cost: str

    mana_value: int

    oracle_text: str

    type_line: str

    power: Optional[int] = None

    toughness: Optional[int] = None