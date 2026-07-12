from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True, kw_only=True)
class ActivatedAbility:
    """Defines an immutable activated ability."""

    ability_type: str
    mana_cost: str = ""
    requires_tap: bool = False
    parameters: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        normalized_ability_type = self.ability_type.strip()
        normalized_mana_cost = self.mana_cost.strip()

        if not normalized_ability_type:
            raise ValueError(
                "Activated ability type must not be empty."
            )

        immutable_parameters = MappingProxyType(
            dict(self.parameters or {})
        )

        object.__setattr__(
            self,
            "ability_type",
            normalized_ability_type,
        )
        object.__setattr__(
            self,
            "mana_cost",
            normalized_mana_cost,
        )
        object.__setattr__(
            self,
            "parameters",
            immutable_parameters,
        )