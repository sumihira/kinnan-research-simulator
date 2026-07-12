from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True, kw_only=True)
class StaticAbility:
    """Immutable static ability definition."""

    ability_type: str
    parameters: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        normalized_type = self.ability_type.strip()

        if not normalized_type:
            raise ValueError(
                "Static ability type must not be empty."
            )

        object.__setattr__(
            self,
            "ability_type",
            normalized_type,
        )

        immutable_parameters = MappingProxyType(
            dict(self.parameters or {})
        )

        object.__setattr__(
            self,
            "parameters",
            immutable_parameters,
        )