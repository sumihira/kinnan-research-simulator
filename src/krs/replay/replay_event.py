from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReplayEvent:
    """
    Represents one immutable event recorded during a simulated game.

    turn identifies the game turn on which the event occurred.
    phase is a human-readable game phase or processing stage.
    action identifies the action or event type.
    description contains the human-readable event detail.
    """

    turn: int
    phase: str
    action: str
    description: str

    def __post_init__(self) -> None:
        if self.turn < 1:
            raise ValueError(
                "turn must be at least 1."
            )

        self._validate_text(
            self.phase,
            field_name="phase",
        )
        self._validate_text(
            self.action,
            field_name="action",
        )
        self._validate_text(
            self.description,
            field_name="description",
        )

    @staticmethod
    def _validate_text(
        value: str,
        *,
        field_name: str,
    ) -> None:
        if not value.strip():
            raise ValueError(
                f"{field_name} must not be empty."
            )