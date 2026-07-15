from __future__ import annotations

from dataclasses import dataclass
from math import inf

from krs.simulation.monte_carlo import MonteCarloDeckResult


@dataclass(frozen=True, slots=True)
class DeckComparisonEntry:
    """
    Stores one ranked deck simulation result.

    Values are copied from the completed simulation summary so comparison
    callers do not need to navigate ExperimentResult internals.
    """

    rank: int
    deck_name: str
    games_completed: int
    wins: int
    non_wins: int
    win_rate: float
    fastest_win_turn: int | None
    average_turns_started: float
    average_kinnan_activations: float
    turn_limit_games: int

    def __post_init__(self) -> None:
        if self.rank < 1:
            raise ValueError("rank must be at least 1.")

        if not self.deck_name.strip():
            raise ValueError("deck_name must not be empty.")

        if self.games_completed < 0:
            raise ValueError(
                "games_completed must not be negative."
            )

        if self.wins < 0:
            raise ValueError("wins must not be negative.")

        if self.non_wins < 0:
            raise ValueError("non_wins must not be negative.")

        if self.wins + self.non_wins != self.games_completed:
            raise ValueError(
                "wins and non_wins must equal games_completed."
            )

        if not 0.0 <= self.win_rate <= 1.0:
            raise ValueError(
                "win_rate must be between 0.0 and 1.0."
            )

        if (
            self.fastest_win_turn is not None
            and self.fastest_win_turn < 1
        ):
            raise ValueError(
                "fastest_win_turn must be at least 1."
            )

        if self.average_turns_started < 0.0:
            raise ValueError(
                "average_turns_started must not be negative."
            )

        if self.average_kinnan_activations < 0.0:
            raise ValueError(
                "average_kinnan_activations must not be negative."
            )

        if self.turn_limit_games < 0:
            raise ValueError(
                "turn_limit_games must not be negative."
            )

        if self.turn_limit_games > self.games_completed:
            raise ValueError(
                "turn_limit_games must not exceed games_completed."
            )


@dataclass(frozen=True, slots=True)
class DeckComparisonReport:
    """
    Stores a completed ranked deck comparison.

    Entries are ordered by rank and retained as an immutable tuple.
    """

    entries: tuple[DeckComparisonEntry, ...]

    def __post_init__(self) -> None:
        if len(self.entries) < 2:
            raise ValueError(
                "A deck comparison requires at least two entries."
            )

        expected_ranks = tuple(
            range(
                1,
                len(self.entries) + 1,
            )
        )
        actual_ranks = tuple(
            entry.rank
            for entry in self.entries
        )

        if actual_ranks != expected_ranks:
            raise ValueError(
                "Comparison entry ranks must be sequential."
            )

        deck_names = tuple(
            entry.deck_name.casefold()
            for entry in self.entries
        )

        if len(set(deck_names)) != len(deck_names):
            raise ValueError(
                "Comparison entries must have unique deck names."
            )

    @property
    def winner(self) -> DeckComparisonEntry:
        """Return the highest-ranked comparison entry."""
        return self.entries[0]


@dataclass(frozen=True, slots=True)
class DeckComparisonReporter:
    """
    Compares completed Monte Carlo results.

    Comparison does not rerun simulations or recalculate the underlying
    SimulationSummary values.
    """

    require_equal_game_counts: bool = True

    def compare(
        self,
        results: tuple[MonteCarloDeckResult, ...],
    ) -> DeckComparisonReport:
        """
        Rank two or more completed deck simulation results.
        """
        self._validate_results(results)

        ordered_results = sorted(
            results,
            key=self._ranking_key,
        )

        entries = tuple(
            self._create_entry(
                rank=rank,
                result=result,
            )
            for rank, result in enumerate(
                ordered_results,
                start=1,
            )
        )

        return DeckComparisonReport(
            entries=entries,
        )

    def _validate_results(
        self,
        results: tuple[MonteCarloDeckResult, ...],
    ) -> None:
        if len(results) < 2:
            raise ValueError(
                "At least two deck results are required for comparison."
            )

        deck_names = tuple(
            result.deck.name.strip().casefold()
            for result in results
        )

        if len(set(deck_names)) != len(deck_names):
            raise ValueError(
                "Deck names must be unique for comparison."
            )

        if not self.require_equal_game_counts:
            return

        game_counts = {
            result.experiment.summary.games_completed
            for result in results
        }

        if len(game_counts) != 1:
            raise ValueError(
                "Compared decks must have equal completed game counts."
            )

    @staticmethod
    def _ranking_key(
        result: MonteCarloDeckResult,
    ) -> tuple[
        float,
        float,
        float,
        float,
        str,
    ]:
        """
        Create an ascending sort key for comparison ranking.

        Higher win rate and Kinnan activation averages use negative values
        so they sort before lower values.
        """
        summary = result.experiment.summary

        fastest_win_turn = (
            float(summary.fastest_win_turn)
            if summary.fastest_win_turn is not None
            else inf
        )

        return (
            -summary.win_rate,
            fastest_win_turn,
            summary.average_turns_started,
            -summary.average_kinnan_activations,
            result.deck.name.casefold(),
        )

    @staticmethod
    def _create_entry(
        *,
        rank: int,
        result: MonteCarloDeckResult,
    ) -> DeckComparisonEntry:
        summary = result.experiment.summary

        return DeckComparisonEntry(
            rank=rank,
            deck_name=result.deck.name,
            games_completed=summary.games_completed,
            wins=summary.wins,
            non_wins=summary.non_wins,
            win_rate=summary.win_rate,
            fastest_win_turn=summary.fastest_win_turn,
            average_turns_started=(
                summary.average_turns_started
            ),
            average_kinnan_activations=(
                summary.average_kinnan_activations
            ),
            turn_limit_games=summary.turn_limit_games,
        )