from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from krs.replay.replay import Replay


@dataclass(frozen=True, slots=True)
class ReplayCount:
    """
    Stores one immutable Replay statistics count.

    name identifies an Action or Phase.
    count is the number of matching ReplayEvent instances.
    """

    name: str
    count: int

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError(
                "name must not be empty."
            )

        if self.count < 1:
            raise ValueError(
                "count must be at least 1."
            )


@dataclass(frozen=True, slots=True)
class ReplayStatistics:
    """
    Stores aggregate statistics calculated from one Replay.

    action_counts and phase_counts are sorted by name so output remains
    deterministic regardless of the order in which a Counter is populated.
    """

    event_count: int
    turn_count: int
    max_turn: int | None
    game_start_count: int
    game_end_count: int
    action_counts: tuple[ReplayCount, ...]
    phase_counts: tuple[ReplayCount, ...]

    def __post_init__(self) -> None:
        if self.event_count < 0:
            raise ValueError(
                "event_count must not be negative."
            )

        if self.turn_count < 0:
            raise ValueError(
                "turn_count must not be negative."
            )

        if self.max_turn is not None and self.max_turn < 1:
            raise ValueError(
                "max_turn must be at least 1."
            )

        if self.game_start_count < 0:
            raise ValueError(
                "game_start_count must not be negative."
            )

        if self.game_end_count < 0:
            raise ValueError(
                "game_end_count must not be negative."
            )

        if self.turn_count > self.event_count:
            raise ValueError(
                "turn_count must not exceed event_count."
            )

        if self.game_start_count > self.event_count:
            raise ValueError(
                "game_start_count must not exceed event_count."
            )

        if self.game_end_count > self.event_count:
            raise ValueError(
                "game_end_count must not exceed event_count."
            )

        self._validate_counts(
            self.action_counts,
            field_name="action_counts",
        )
        self._validate_counts(
            self.phase_counts,
            field_name="phase_counts",
        )

        action_total = sum(
            item.count
            for item in self.action_counts
        )
        phase_total = sum(
            item.count
            for item in self.phase_counts
        )

        if action_total != self.event_count:
            raise ValueError(
                "action_counts total must equal event_count."
            )

        if phase_total != self.event_count:
            raise ValueError(
                "phase_counts total must equal event_count."
            )

        if (
            self.game_start_count
            != self.action_count("game_start")
        ):
            raise ValueError(
                "game_start_count must match "
                "the game_start Action count."
            )

        if (
            self.game_end_count
            != self.action_count("game_end")
        ):
            raise ValueError(
                "game_end_count must match "
                "the game_end Action count."
            )

        if self.event_count == 0:
            if self.turn_count != 0:
                raise ValueError(
                    "Empty Replay statistics must have "
                    "turn_count equal to 0."
                )

            if self.max_turn is not None:
                raise ValueError(
                    "Empty Replay statistics must have "
                    "max_turn equal to None."
                )
        else:
            if self.turn_count < 1:
                raise ValueError(
                    "Non-empty Replay statistics must have "
                    "turn_count of at least 1."
                )

            if self.max_turn is None:
                raise ValueError(
                    "Non-empty Replay statistics must define "
                    "max_turn."
                )

    @classmethod
    def from_replay(
        cls,
        replay: Replay,
    ) -> ReplayStatistics:
        """
        Calculate immutable statistics from one Replay.

        Replay and its ReplayEvent values are never modified.
        """
        events = replay.events

        action_counter = Counter(
            event.action
            for event in events
        )
        phase_counter = Counter(
            event.phase
            for event in events
        )
        turns = {
            event.turn
            for event in events
        }

        action_counts = cls._create_counts(
            action_counter
        )
        phase_counts = cls._create_counts(
            phase_counter
        )

        return cls(
            event_count=len(events),
            turn_count=len(turns),
            max_turn=(
                max(turns)
                if turns
                else None
            ),
            game_start_count=action_counter.get(
                "game_start",
                0,
            ),
            game_end_count=action_counter.get(
                "game_end",
                0,
            ),
            action_counts=action_counts,
            phase_counts=phase_counts,
        )

    def action_count(
        self,
        action: str,
    ) -> int:
        """
        Return the number of events matching an Action name.

        Unknown Action names return 0.
        """
        normalized_action = self._normalize_lookup_name(
            action,
            field_name="action",
        )

        return self._find_count(
            self.action_counts,
            normalized_action,
        )

    def phase_count(
        self,
        phase: str,
    ) -> int:
        """
        Return the number of events matching a Phase name.

        Unknown Phase names return 0.
        """
        normalized_phase = self._normalize_lookup_name(
            phase,
            field_name="phase",
        )

        return self._find_count(
            self.phase_counts,
            normalized_phase,
        )

    @staticmethod
    def _create_counts(
        counter: Counter[str],
    ) -> tuple[ReplayCount, ...]:
        """
        Convert a Counter into stable immutable ReplayCount values.
        """
        return tuple(
            ReplayCount(
                name=name,
                count=count,
            )
            for name, count in sorted(
                counter.items()
            )
        )

    @staticmethod
    def _find_count(
        counts: tuple[ReplayCount, ...],
        name: str,
    ) -> int:
        for item in counts:
            if item.name == name:
                return item.count

        return 0

    @staticmethod
    def _normalize_lookup_name(
        value: str,
        *,
        field_name: str,
    ) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError(
                f"{field_name} must not be empty."
            )

        return normalized_value

    @staticmethod
    def _validate_counts(
        counts: tuple[ReplayCount, ...],
        *,
        field_name: str,
    ) -> None:
        names = tuple(
            item.name
            for item in counts
        )

        if len(names) != len(set(names)):
            raise ValueError(
                f"{field_name} must not contain "
                "duplicate names."
            )

        if names != tuple(sorted(names)):
            raise ValueError(
                f"{field_name} must be sorted by name."
            )