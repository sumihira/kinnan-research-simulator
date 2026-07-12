from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True, kw_only=True)
class ReplacementAbility:
    """Immutable replacement ability definition."""

    ability_type: str
    event: str
    parameters: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        normalized_type = self.ability_type.strip()
        normalized_event = self.event.strip()

        if not normalized_type:
            raise ValueError(
                "Replacement ability type must not be empty."
            )

        if not normalized_event:
            raise ValueError(
                "Replacement ability event must not be empty."
            )

        object.__setattr__(
            self,
            "ability_type",
            normalized_type,
        )
        object.__setattr__(
            self,
            "event",
            normalized_event,
        )

        immutable_parameters = MappingProxyType(
            dict(self.parameters or {})
        )

        object.__setattr__(
            self,
            "parameters",
            immutable_parameters,
        )