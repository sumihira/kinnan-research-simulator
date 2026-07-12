from __future__ import annotations

from dataclasses import dataclass

from krs.abilities.mana_ability import ManaAbility


@dataclass(frozen=True, slots=True)
class Card:
    """
    Immutable card definition.

    Runtime state belongs to Permanent.
    """

    id: str
    name: str
    mana_cost: str
    mana_value: int
    oracle_text: str
    type_line: str

    power: str | None = None
    toughness: str | None = None

    mana_abilities: tuple[ManaAbility, ...] = ()
    keywords: tuple[str, ...] = ()