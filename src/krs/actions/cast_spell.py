from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from krs.actions.action import Action
from krs.cards.card import Card
from krs.mana.mana_cost import ManaCost


@dataclass(slots=True, frozen=True, kw_only=True)
class CastSpellAction(Action):
    """
    Cast a spell from the player's hand.

    Version 1 supports permanent spells only.
    """

    card: Card
    cost: ManaCost
    chosen_values: Mapping[str, str] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        normalized_values: dict[str, str] = {}

        for raw_key, raw_value in self.chosen_values.items():
            if not isinstance(raw_key, str) or not raw_key.strip():
                raise ValueError(
                    "Chosen value key must be a non-empty string."
                )

            if not isinstance(raw_value, str) or not raw_value.strip():
                raise ValueError(
                    "Chosen value must be a non-empty string."
                )

            normalized_values[raw_key.strip()] = raw_value.strip()

        object.__setattr__(
            self,
            "chosen_values",
            MappingProxyType(normalized_values),
        )