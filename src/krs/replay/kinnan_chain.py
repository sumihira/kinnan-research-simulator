from __future__ import annotations

from dataclasses import dataclass, field

from krs.replay.replay import Replay
from krs.replay.replay_event import ReplayEvent


@dataclass(frozen=True, slots=True)
class KinnanActivationStreak:
    """
    Represents one maximal consecutive run of Kinnan activations.

    Event indexes are zero-based and inclusive. A streak may contain only
    one activation; whether it qualifies as a chain is determined by
    KinnanChainTracker.minimum_chain_length.
    """

    start_event_index: int
    end_event_index: int
    start_turn: int
    end_turn: int
    activation_count: int

    def __post_init__(self) -> None:
        if self.start_event_index < 0:
            raise ValueError(
                "start_event_index must not be negative."
            )

        if self.end_event_index < self.start_event_index:
            raise ValueError(
                "end_event_index must not be before "
                "start_event_index."
            )

        if self.start_turn < 1:
            raise ValueError(
                "start_turn must be at least 1."
            )

        if self.end_turn < self.start_turn:
            raise ValueError(
                "end_turn must not be before start_turn."
            )

        if self.activation_count < 1:
            raise ValueError(
                "activation_count must be at least 1."
            )

        expected_count = (
            self.end_event_index
            - self.start_event_index
            + 1
        )

        if self.activation_count != expected_count:
            raise ValueError(
                "activation_count must match the inclusive "
                "event index range."
            )

    @property
    def spans_multiple_turns(self) -> bool:
        """
        Return whether the streak crosses a turn boundary.
        """
        return self.start_turn != self.end_turn

    def qualifies(
        self,
        minimum_chain_length: int,
    ) -> bool:
        """
        Return whether this streak meets a chain threshold.
        """
        if minimum_chain_length < 1:
            raise ValueError(
                "minimum_chain_length must be at least 1."
            )

        return (
            self.activation_count
            >= minimum_chain_length
        )


@dataclass(frozen=True, slots=True)
class KinnanChainResult:
    """
    Stores Kinnan chain analysis for one Replay.

    streaks contains every maximal consecutive Kinnan activation run,
    including single-activation runs.
    """

    minimum_chain_length: int
    total_event_count: int
    total_activation_count: int
    activation_turn_count: int
    streaks: tuple[KinnanActivationStreak, ...]

    def __post_init__(self) -> None:
        if self.minimum_chain_length < 1:
            raise ValueError(
                "minimum_chain_length must be at least 1."
            )

        if self.total_event_count < 0:
            raise ValueError(
                "total_event_count must not be negative."
            )

        if self.total_activation_count < 0:
            raise ValueError(
                "total_activation_count must not be negative."
            )

        if self.activation_turn_count < 0:
            raise ValueError(
                "activation_turn_count must not be negative."
            )

        if self.total_activation_count > self.total_event_count:
            raise ValueError(
                "total_activation_count must not exceed "
                "total_event_count."
            )

        if self.activation_turn_count > self.total_activation_count:
            raise ValueError(
                "activation_turn_count must not exceed "
                "total_activation_count."
            )

        streak_activation_total = sum(
            streak.activation_count
            for streak in self.streaks
        )

        if (
            streak_activation_total
            != self.total_activation_count
        ):
            raise ValueError(
                "Streak activation total must equal "
                "total_activation_count."
            )

        previous_end_index: int | None = None

        for streak in self.streaks:
            if (
                previous_end_index is not None
                and streak.start_event_index
                <= previous_end_index
            ):
                raise ValueError(
                    "streaks must be ordered and "
                    "must not overlap."
                )

            previous_end_index = (
                streak.end_event_index
            )

        if self.total_activation_count == 0:
            if self.activation_turn_count != 0:
                raise ValueError(
                    "A result without activations must have "
                    "activation_turn_count equal to 0."
                )

            if self.streaks:
                raise ValueError(
                    "A result without activations must not "
                    "contain streaks."
                )

    @property
    def qualifying_chains(
        self,
    ) -> tuple[KinnanActivationStreak, ...]:
        """
        Return streaks meeting the configured chain threshold.
        """
        return tuple(
            streak
            for streak in self.streaks
            if streak.qualifies(
                self.minimum_chain_length
            )
        )

    @property
    def streak_count(self) -> int:
        """
        Return the total number of activation streaks.
        """
        return len(self.streaks)

    @property
    def chain_count(self) -> int:
        """
        Return the number of qualifying chains.
        """
        return len(self.qualifying_chains)

    @property
    def has_activation(self) -> bool:
        """
        Return whether Kinnan was activated at least once.
        """
        return self.total_activation_count > 0

    @property
    def has_chain(self) -> bool:
        """
        Return whether at least one qualifying chain occurred.
        """
        return self.chain_count > 0

    @property
    def max_chain_length(self) -> int:
        """
        Return the largest activation streak length.

        Returns 0 when no Kinnan activation was recorded.
        """
        return max(
            (
                streak.activation_count
                for streak in self.streaks
            ),
            default=0,
        )

    @property
    def chained_activation_count(self) -> int:
        """
        Return activations belonging to qualifying chains.
        """
        return sum(
            streak.activation_count
            for streak in self.qualifying_chains
        )

    @property
    def unchained_activation_count(self) -> int:
        """
        Return activations not belonging to qualifying chains.
        """
        return (
            self.total_activation_count
            - self.chained_activation_count
        )

    @property
    def first_chain_turn(self) -> int | None:
        """
        Return the starting turn of the first qualifying chain.
        """
        chains = self.qualifying_chains

        if not chains:
            return None

        return chains[0].start_turn

    @property
    def chain_activation_ratio(self) -> float:
        """
        Return the share of activations belonging to chains.

        Returns 0.0 when no Kinnan activation occurred.
        """
        if self.total_activation_count == 0:
            return 0.0

        return (
            self.chained_activation_count
            / self.total_activation_count
        )


@dataclass(frozen=True, slots=True)
class KinnanChainTracker:
    """
    Analyzes consecutive Kinnan activation events in one Replay.

    By default, two or more consecutive activate_kinnan events constitute
    a chain. Any event with another action name ends the current streak.
    """

    minimum_chain_length: int = 2
    activation_action: str = "activate_kinnan"
    ignored_actions: frozenset[str] = field(
        default_factory=frozenset,
    )

    def __post_init__(self) -> None:
        if self.minimum_chain_length < 1:
            raise ValueError(
                "minimum_chain_length must be at least 1."
            )

        if not self.activation_action.strip():
            raise ValueError(
                "activation_action must not be empty."
            )

        if (
            self.activation_action
            in self.ignored_actions
        ):
            raise ValueError(
                "activation_action must not be ignored."
            )

        for ignored_action in self.ignored_actions:
            if not ignored_action.strip():
                raise ValueError(
                    "ignored_actions must not contain "
                    "empty names."
                )

    def analyze(
        self,
        replay: Replay,
    ) -> KinnanChainResult:
        """
        Analyze Kinnan activation streaks without modifying Replay.
        """
        events = replay.events
        streaks = self._create_streaks(events)

        activation_turns = {
            event.turn
            for event in events
            if event.action == self.activation_action
        }

        total_activation_count = sum(
            streak.activation_count
            for streak in streaks
        )

        return KinnanChainResult(
            minimum_chain_length=(
                self.minimum_chain_length
            ),
            total_event_count=len(events),
            total_activation_count=(
                total_activation_count
            ),
            activation_turn_count=len(
                activation_turns
            ),
            streaks=streaks,
        )

    def _create_streaks(
        self,
        events: tuple[ReplayEvent, ...],
    ) -> tuple[KinnanActivationStreak, ...]:
        """
        Create maximal consecutive activation streaks.
        """
        streaks: list[KinnanActivationStreak] = []

        start_event_index: int | None = None
        end_event_index: int | None = None
        start_turn: int | None = None
        end_turn: int | None = None
        activation_count = 0

        for event_index, event in enumerate(events):
            if event.action == self.activation_action:
                if start_event_index is None:
                    start_event_index = event_index
                    start_turn = event.turn

                end_event_index = event_index
                end_turn = event.turn
                activation_count += 1
                continue

            if event.action in self.ignored_actions:
                continue

            if start_event_index is not None:
                streaks.append(
                    self._build_streak(
                        start_event_index=(
                            start_event_index
                        ),
                        end_event_index=(
                            end_event_index
                        ),
                        start_turn=start_turn,
                        end_turn=end_turn,
                        activation_count=(
                            activation_count
                        ),
                    )
                )

                start_event_index = None
                end_event_index = None
                start_turn = None
                end_turn = None
                activation_count = 0

        if start_event_index is not None:
            streaks.append(
                self._build_streak(
                    start_event_index=(
                        start_event_index
                    ),
                    end_event_index=end_event_index,
                    start_turn=start_turn,
                    end_turn=end_turn,
                    activation_count=(
                        activation_count
                    ),
                )
            )

        return tuple(streaks)

    @staticmethod
    def _build_streak(
        *,
        start_event_index: int,
        end_event_index: int | None,
        start_turn: int | None,
        end_turn: int | None,
        activation_count: int,
    ) -> KinnanActivationStreak:
        """
        Build one validated activation streak.
        """
        if end_event_index is None:
            raise ValueError(
                "end_event_index must be defined."
            )

        if start_turn is None:
            raise ValueError(
                "start_turn must be defined."
            )

        if end_turn is None:
            raise ValueError(
                "end_turn must be defined."
            )

        return KinnanActivationStreak(
            start_event_index=start_event_index,
            end_event_index=end_event_index,
            start_turn=start_turn,
            end_turn=end_turn,
            activation_count=activation_count,
        )