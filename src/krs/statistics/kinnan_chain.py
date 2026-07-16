from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Self


@dataclass(slots=True)
class KinnanChainStatistics:
    """
    Tracks Kinnan activation results within one game.

    A chain is established by at least two consecutive successful Kinnan
    activations. It continues until a miss or an explicit reset occurs.
    """

    activation_count: int = 0
    hit_count: int = 0
    miss_count: int = 0
    current_chain_length: int = 0
    longest_chain_length: int = 0
    chain_activation_count: int = 0
    first_chain_turn: int | None = None
    hit_card_ids: list[str] = field(default_factory=list)

    def record_hit(
        self,
        card_id: str,
        *,
        turn: int | None = None,
    ) -> None:
        if not card_id.strip():
            raise ValueError(
                "Hit card ID must not be empty."
            )

        self._validate_turn(turn)

        previous_chain_length = self.current_chain_length

        self.activation_count += 1
        self.hit_count += 1
        self.current_chain_length += 1
        self.hit_card_ids.append(card_id)

        if previous_chain_length == 1:
            self.chain_activation_count += 2

            if self.first_chain_turn is None:
                self.first_chain_turn = turn
        elif previous_chain_length >= 2:
            self.chain_activation_count += 1

        self.longest_chain_length = max(
            self.longest_chain_length,
            self.current_chain_length,
        )

    def record_miss(self) -> None:
        self.activation_count += 1
        self.miss_count += 1
        self.current_chain_length = 0

    def reset_current_chain(self) -> None:
        self.current_chain_length = 0

    @property
    def hit_rate(self) -> float:
        if self.activation_count == 0:
            return 0.0

        return self.hit_count / self.activation_count

    @property
    def has_activation(self) -> bool:
        return self.activation_count > 0

    @property
    def has_chain(self) -> bool:
        return self.longest_chain_length >= 2

    def snapshot(self) -> KinnanChainSnapshot:
        """
        Return an immutable copy of the current game statistics.

        The returned snapshot can safely be retained by simulation results
        without depending on later GameState mutations.
        """
        return KinnanChainSnapshot.from_statistics(self)

    @staticmethod
    def _validate_turn(turn: int | None) -> None:
        if turn is not None and turn < 1:
            raise ValueError(
                "Turn must be at least 1."
            )


@dataclass(frozen=True, slots=True)
class KinnanChainSnapshot:
    """Immutable per-game Kinnan chain statistics."""

    activation_count: int
    hit_count: int
    miss_count: int
    current_chain_length: int
    longest_chain_length: int
    chain_activation_count: int
    first_chain_turn: int | None
    hit_card_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        counts = (
            self.activation_count,
            self.hit_count,
            self.miss_count,
            self.current_chain_length,
            self.longest_chain_length,
            self.chain_activation_count,
        )

        if any(value < 0 for value in counts):
            raise ValueError(
                "Kinnan chain counts must not be negative."
            )

        if (
            self.hit_count + self.miss_count
            != self.activation_count
        ):
            raise ValueError(
                "hit_count and miss_count must equal "
                "activation_count."
            )

        if (
            self.current_chain_length
            > self.longest_chain_length
        ):
            raise ValueError(
                "current_chain_length must not exceed "
                "longest_chain_length."
            )

        if self.longest_chain_length > self.hit_count:
            raise ValueError(
                "longest_chain_length must not exceed hit_count."
            )

        if self.chain_activation_count > self.hit_count:
            raise ValueError(
                "chain_activation_count must not exceed "
                "hit_count."
            )

        if len(self.hit_card_ids) != self.hit_count:
            raise ValueError(
                "hit_card_ids count must equal hit_count."
            )

        if any(
            not card_id.strip()
            for card_id in self.hit_card_ids
        ):
            raise ValueError(
                "Hit card IDs must not be empty."
            )

        if (
            self.first_chain_turn is not None
            and self.first_chain_turn < 1
        ):
            raise ValueError(
                "first_chain_turn must be at least 1."
            )

        if (
            self.first_chain_turn is not None
            and not self.has_chain
        ):
            raise ValueError(
                "first_chain_turn requires an established chain."
            )

    @classmethod
    def from_statistics(
        cls,
        statistics: KinnanChainStatistics,
    ) -> Self:
        """Create an immutable snapshot from mutable game statistics."""
        return cls(
            activation_count=statistics.activation_count,
            hit_count=statistics.hit_count,
            miss_count=statistics.miss_count,
            current_chain_length=(
                statistics.current_chain_length
            ),
            longest_chain_length=(
                statistics.longest_chain_length
            ),
            chain_activation_count=(
                statistics.chain_activation_count
            ),
            first_chain_turn=statistics.first_chain_turn,
            hit_card_ids=tuple(statistics.hit_card_ids),
        )

    @classmethod
    def empty(cls) -> Self:
        """Return an empty per-game snapshot."""
        return cls(
            activation_count=0,
            hit_count=0,
            miss_count=0,
            current_chain_length=0,
            longest_chain_length=0,
            chain_activation_count=0,
            first_chain_turn=None,
            hit_card_ids=(),
        )

    @property
    def hit_rate(self) -> float:
        if self.activation_count == 0:
            return 0.0

        return self.hit_count / self.activation_count

    @property
    def has_activation(self) -> bool:
        return self.activation_count > 0

    @property
    def has_chain(self) -> bool:
        return self.longest_chain_length >= 2


@dataclass(frozen=True, slots=True)
class KinnanChainSummary:
    """Stores aggregate Kinnan-chain statistics for multiple games."""

    games: int
    games_with_activation: int
    games_with_chain: int
    total_activations: int
    chain_activations: int
    average_longest_chain: float
    max_chain: int
    max_chain_distribution: tuple[tuple[int, int], ...]
    first_chain_turns: tuple[int, ...]
    turn_chain_counts: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        self._validate_counts()
        self._validate_distributions()

    @classmethod
    def from_games(
        cls,
        games: Iterable[
            KinnanChainStatistics | KinnanChainSnapshot
        ],
    ) -> Self:
        game_statistics = tuple(games)
        game_count = len(game_statistics)

        if game_count == 0:
            return cls.empty()

        longest_chains = tuple(
            statistics.longest_chain_length
            for statistics in game_statistics
        )
        first_chain_turns = tuple(
            statistics.first_chain_turn
            for statistics in game_statistics
            if statistics.first_chain_turn is not None
        )

        return cls(
            games=game_count,
            games_with_activation=sum(
                statistics.has_activation
                for statistics in game_statistics
            ),
            games_with_chain=sum(
                statistics.has_chain
                for statistics in game_statistics
            ),
            total_activations=sum(
                statistics.activation_count
                for statistics in game_statistics
            ),
            chain_activations=sum(
                statistics.chain_activation_count
                for statistics in game_statistics
            ),
            average_longest_chain=(
                sum(longest_chains) / game_count
            ),
            max_chain=max(longest_chains),
            max_chain_distribution=cls._counter_items(
                longest_chains
            ),
            first_chain_turns=first_chain_turns,
            turn_chain_counts=cls._counter_items(
                first_chain_turns
            ),
        )

    @classmethod
    def empty(cls) -> Self:
        return cls(
            games=0,
            games_with_activation=0,
            games_with_chain=0,
            total_activations=0,
            chain_activations=0,
            average_longest_chain=0.0,
            max_chain=0,
            max_chain_distribution=(),
            first_chain_turns=(),
            turn_chain_counts=(),
        )

    @property
    def overall_chain_rate(self) -> float:
        if self.games == 0:
            return 0.0

        return self.games_with_chain / self.games

    @property
    def activation_game_chain_rate(self) -> float:
        if self.games_with_activation == 0:
            return 0.0

        return (
            self.games_with_chain
            / self.games_with_activation
        )

    @property
    def activation_chain_rate(self) -> float:
        if self.total_activations == 0:
            return 0.0

        return (
            self.chain_activations
            / self.total_activations
        )

    def chain_count_through_turn(self, turn: int) -> int:
        self._validate_turn(turn)

        return sum(
            count
            for chain_turn, count in self.turn_chain_counts
            if chain_turn <= turn
        )

    def chain_rate_through_turn(self, turn: int) -> float:
        self._validate_turn(turn)

        if self.games == 0:
            return 0.0

        return (
            self.chain_count_through_turn(turn)
            / self.games
        )

    def _validate_counts(self) -> None:
        count_fields = (
            self.games,
            self.games_with_activation,
            self.games_with_chain,
            self.total_activations,
            self.chain_activations,
            self.max_chain,
        )

        if any(value < 0 for value in count_fields):
            raise ValueError(
                "Kinnan chain summary counts must not be negative."
            )

        if self.games_with_activation > self.games:
            raise ValueError(
                "games_with_activation must not exceed games."
            )

        if (
            self.games_with_chain
            > self.games_with_activation
        ):
            raise ValueError(
                "games_with_chain must not exceed "
                "games_with_activation."
            )

        if (
            self.chain_activations
            > self.total_activations
        ):
            raise ValueError(
                "chain_activations must not exceed "
                "total_activations."
            )

        if self.average_longest_chain < 0.0:
            raise ValueError(
                "average_longest_chain must not be negative."
            )

    def _validate_distributions(self) -> None:
        self._validate_distribution(
            self.max_chain_distribution,
            field_name="max_chain_distribution",
            allow_zero_key=True,
        )
        self._validate_distribution(
            self.turn_chain_counts,
            field_name="turn_chain_counts",
            allow_zero_key=False,
        )

        if sum(
            count
            for _, count in self.max_chain_distribution
        ) != self.games:
            raise ValueError(
                "max_chain_distribution must contain one "
                "entry per game."
            )

        if sum(
            count
            for _, count in self.turn_chain_counts
        ) != len(self.first_chain_turns):
            raise ValueError(
                "turn_chain_counts must match "
                "first_chain_turns."
            )

        if (
            len(self.first_chain_turns)
            > self.games_with_chain
        ):
            raise ValueError(
                "first_chain_turns must not exceed "
                "games_with_chain."
            )

        if any(
            turn < 1
            for turn in self.first_chain_turns
        ):
            raise ValueError(
                "First chain turns must be at least 1."
            )

    @staticmethod
    def _validate_distribution(
        distribution: tuple[tuple[int, int], ...],
        *,
        field_name: str,
        allow_zero_key: bool,
    ) -> None:
        keys = tuple(
            key
            for key, _ in distribution
        )

        if keys != tuple(sorted(set(keys))):
            raise ValueError(
                f"{field_name} keys must be unique and sorted."
            )

        minimum_key = 0 if allow_zero_key else 1

        if any(key < minimum_key for key in keys):
            raise ValueError(
                f"{field_name} contains an invalid key."
            )

        if any(
            count < 1
            for _, count in distribution
        ):
            raise ValueError(
                f"{field_name} counts must be at least 1."
            )

    @staticmethod
    def _counter_items(
        values: Iterable[int],
    ) -> tuple[tuple[int, int], ...]:
        return tuple(
            sorted(Counter(values).items())
        )

    @staticmethod
    def _validate_turn(turn: int) -> None:
        if turn < 1:
            raise ValueError(
                "Turn must be at least 1."
            )