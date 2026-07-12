from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True, kw_only=True)
class StrategyConfig:
    """
    Immutable AI strategy configuration.

    Values are loaded from config/strategies/*.yaml.
    """

    name: str

    mana_value_weight: float = 1.0
    mana_ability_bonus: float = 2.0
    untap_bonus: float = 5.0
    copy_bonus: float = 4.0
    combo_bonus: float = 3.0

    custom_scores: Mapping[str, float] = field(
        default_factory=dict
    )
    combo_card_ids: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError(
                "Strategy name must not be empty."
            )

        numeric_values = {
            "mana_value_weight": self.mana_value_weight,
            "mana_ability_bonus": self.mana_ability_bonus,
            "untap_bonus": self.untap_bonus,
            "copy_bonus": self.copy_bonus,
            "combo_bonus": self.combo_bonus,
        }

        for field_name, value in numeric_values.items():
            if not isinstance(value, int | float):
                raise TypeError(
                    f"{field_name} must be numeric."
                )

        normalized_custom_scores: dict[str, float] = {}

        for card_id, score in self.custom_scores.items():
            if not card_id.strip():
                raise ValueError(
                    "Custom score card IDs must not be empty."
                )

            if not isinstance(score, int | float):
                raise TypeError(
                    "Custom score values must be numeric."
                )

            normalized_custom_scores[card_id] = float(score)

        normalized_combo_ids = frozenset(
            card_id
            for card_id in self.combo_card_ids
            if card_id.strip()
        )

        if len(normalized_combo_ids) != len(
            self.combo_card_ids
        ):
            raise ValueError(
                "Combo card IDs must not be empty."
            )

        object.__setattr__(
            self,
            "custom_scores",
            MappingProxyType(normalized_custom_scores),
        )
        object.__setattr__(
            self,
            "combo_card_ids",
            normalized_combo_ids,
        )