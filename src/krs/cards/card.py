from __future__ import annotations

from dataclasses import dataclass

from krs.abilities.activated import ActivatedAbility
from krs.abilities.mana_ability import ManaAbility
from krs.abilities.replacement import ReplacementAbility
from krs.abilities.static import StaticAbility
from krs.abilities.triggered import TriggeredAbility


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
    activated_abilities: tuple[ActivatedAbility, ...] = ()
    static_abilities: tuple[StaticAbility, ...] = ()
    triggered_abilities: tuple[TriggeredAbility, ...] = ()
    replacement_abilities: tuple[ReplacementAbility, ...] = ()
    keywords: tuple[str, ...] = ()