from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class CardConfig:
    """Immutable card configuration."""

    card_name: str
    abilities: Mapping[str, tuple[Mapping[str, object], ...]]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "card_name",
            self.card_name.strip(),
        )

        immutable = {
            key: tuple(value)
            for key, value in self.abilities.items()
        }

        object.__setattr__(
            self,
            "abilities",
            MappingProxyType(immutable),
        )