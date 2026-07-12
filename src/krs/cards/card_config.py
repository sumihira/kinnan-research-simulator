from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True)
class CardConfig:
    """Immutable card-specific configuration."""

    card_name: str
    abilities: Mapping[str, tuple[Mapping[str, object], ...]]

    def __post_init__(self) -> None:
        normalized_name = self.card_name.strip()

        if not normalized_name:
            raise ValueError(
                "Card config name must not be empty."
            )

        immutable_abilities = MappingProxyType(
            {
                ability_kind: tuple(definitions)
                for ability_kind, definitions
                in self.abilities.items()
            }
        )

        object.__setattr__(
            self,
            "card_name",
            normalized_name,
        )
        object.__setattr__(
            self,
            "abilities",
            immutable_abilities,
        )