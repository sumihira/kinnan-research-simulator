from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True, kw_only=True)
class StaticAbility:
    """Defines an immutable static ability."""

    ability_type: str
    parameters: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        normalized_ability_type = self.ability_type.strip()

        if not normalized_ability_type:
            raise ValueError(
                "Static ability type must not be empty."
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
            "parameters",
            immutable_parameters,
        )