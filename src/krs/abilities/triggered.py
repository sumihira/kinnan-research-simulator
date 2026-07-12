from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True, kw_only=True)
class TriggeredAbility:
    """Defines an immutable triggered ability."""

    ability_type: str
    event: str
    parameters: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        normalized_ability_type = self.ability_type.strip()
        normalized_event = self.event.strip()

        if not normalized_ability_type:
            raise ValueError(
                "Triggered ability type must not be empty."
            )

        if not normalized_event:
            raise ValueError(
                "Triggered ability event must not be empty."
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
            "event",
            normalized_event,
        )
        object.__setattr__(
            self,
            "parameters",
            immutable_parameters,
        )