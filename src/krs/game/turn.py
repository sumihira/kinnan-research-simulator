from __future__ import annotations

from dataclasses import dataclass

from krs.game.phase import Phase


@dataclass(frozen=True, slots=True)
class Turn:
    """
    Defines the phase order used by Version 1.

    Combat phases are intentionally omitted.
    """

    PHASE_ORDER = (
        Phase.UNTAP,
        Phase.UPKEEP,
        Phase.DRAW,
        Phase.MAIN,
        Phase.END,
    )

    @classmethod
    def next_phase(cls, current_phase: Phase) -> Phase:
        """
        Return the next phase in the current turn.

        END has no next phase. The GameEngine must start a new turn.
        """
        try:
            current_index = cls.PHASE_ORDER.index(current_phase)
        except ValueError as error:
            raise ValueError(
                f"Unsupported phase: {current_phase}"
            ) from error

        if current_phase is Phase.END:
            raise ValueError(
                "END phase has no next phase in the same turn."
            )

        return cls.PHASE_ORDER[current_index + 1]