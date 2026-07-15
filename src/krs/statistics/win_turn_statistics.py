from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from statistics import fmean
from statistics import median
from statistics import pstdev

from krs.simulation.experiment import ExperimentResult


@dataclass(frozen=True, slots=True)
class WinTurnStatistics:
    """
    Stores descriptive statistics for winning game turns.

    Games that did not finish with a winner are excluded from all turn
    measurements. Percentiles use the nearest-rank method.
    """

    games_completed: int
    wins: int
    win_rate: float
    fastest_win_turn: int | None
    slowest_win_turn: int | None
    average_win_turn: float | None
    median_win_turn: float | None
    percentile_90_win_turn: int | None
    percentile_95_win_turn: int | None
    win_turn_standard_deviation: float | None

    def __post_init__(self) -> None:
        if self.games_completed < 1:
            raise ValueError(
                "games_completed must be at least 1."
            )

        if self.wins < 0:
            raise ValueError(
                "wins must not be negative."
            )

        if self.wins > self.games_completed:
            raise ValueError(
                "wins must not exceed games_completed."
            )

        if not 0.0 <= self.win_rate <= 1.0:
            raise ValueError(
                "win_rate must be between 0.0 and 1.0."
            )

        expected_win_rate = self.wins / self.games_completed

        if abs(self.win_rate - expected_win_rate) > 1e-12:
            raise ValueError(
                "win_rate must equal wins divided by "
                "games_completed."
            )

        if self.wins == 0:
            self._validate_empty_statistics()
            return

        self._validate_populated_statistics()

    @property
    def has_wins(self) -> bool:
        """Return whether at least one winning game was observed."""
        return self.wins > 0

    @property
    def win_rate_percent(self) -> float:
        """Return the observed win rate as a percentage."""
        return self.win_rate * 100.0

    def _validate_empty_statistics(self) -> None:
        values = (
            self.fastest_win_turn,
            self.slowest_win_turn,
            self.average_win_turn,
            self.median_win_turn,
            self.percentile_90_win_turn,
            self.percentile_95_win_turn,
            self.win_turn_standard_deviation,
        )

        if any(value is not None for value in values):
            raise ValueError(
                "Win-turn statistics must be None when wins is zero."
            )

    def _validate_populated_statistics(self) -> None:
        integer_turns = (
            self.fastest_win_turn,
            self.slowest_win_turn,
            self.percentile_90_win_turn,
            self.percentile_95_win_turn,
        )

        if any(value is None for value in integer_turns):
            raise ValueError(
                "Win-turn values must be present when wins is positive."
            )

        float_values = (
            self.average_win_turn,
            self.median_win_turn,
            self.win_turn_standard_deviation,
        )

        if any(value is None for value in float_values):
            raise ValueError(
                "Win-turn measurements must be present when wins "
                "is positive."
            )

        if self.fastest_win_turn is None:
            raise RuntimeError(
                "fastest_win_turn validation failed."
            )

        if self.slowest_win_turn is None:
            raise RuntimeError(
                "slowest_win_turn validation failed."
            )

        if self.percentile_90_win_turn is None:
            raise RuntimeError(
                "percentile_90_win_turn validation failed."
            )

        if self.percentile_95_win_turn is None:
            raise RuntimeError(
                "percentile_95_win_turn validation failed."
            )

        if self.average_win_turn is None:
            raise RuntimeError(
                "average_win_turn validation failed."
            )

        if self.median_win_turn is None:
            raise RuntimeError(
                "median_win_turn validation failed."
            )

        if self.win_turn_standard_deviation is None:
            raise RuntimeError(
                "win_turn_standard_deviation validation failed."
            )

        if self.fastest_win_turn < 1:
            raise ValueError(
                "fastest_win_turn must be at least 1."
            )

        if self.slowest_win_turn < self.fastest_win_turn:
            raise ValueError(
                "slowest_win_turn must not be earlier than "
                "fastest_win_turn."
            )

        if not (
            self.fastest_win_turn
            <= self.average_win_turn
            <= self.slowest_win_turn
        ):
            raise ValueError(
                "average_win_turn must be within the observed "
                "turn range."
            )

        if not (
            self.fastest_win_turn
            <= self.median_win_turn
            <= self.slowest_win_turn
        ):
            raise ValueError(
                "median_win_turn must be within the observed "
                "turn range."
            )

        for field_name, value in (
            (
                "percentile_90_win_turn",
                self.percentile_90_win_turn,
            ),
            (
                "percentile_95_win_turn",
                self.percentile_95_win_turn,
            ),
        ):
            if not (
                self.fastest_win_turn
                <= value
                <= self.slowest_win_turn
            ):
                raise ValueError(
                    f"{field_name} must be within the observed "
                    "turn range."
                )

        if (
            self.percentile_90_win_turn
            > self.percentile_95_win_turn
        ):
            raise ValueError(
                "percentile_90_win_turn must not exceed "
                "percentile_95_win_turn."
            )

        if self.win_turn_standard_deviation < 0.0:
            raise ValueError(
                "win_turn_standard_deviation must not be negative."
            )


@dataclass(frozen=True, slots=True)
class WinTurnStatisticsCalculator:
    """
    Calculates descriptive statistics for winning turns.

    A game is treated as a win only when game_over is true and winner is
    not None, matching SimulationSummary win counting.
    """

    def calculate(
        self,
        result: ExperimentResult,
    ) -> WinTurnStatistics:
        """Calculate win-turn statistics from one ExperimentResult."""
        summary = result.summary

        if summary.games_completed < 1:
            raise ValueError(
                "Cannot calculate win-turn statistics without "
                "completed games."
            )

        if len(result.game_results) != summary.games_completed:
            raise ValueError(
                "game_results count must equal games_completed."
            )

        winning_turns = tuple(
            sorted(
                game_result.turns_started
                for game_result in result.game_results
                if (
                    game_result.game_over
                    and game_result.winner is not None
                )
            )
        )

        if len(winning_turns) != summary.wins:
            raise ValueError(
                "Winning game result count must equal summary.wins."
            )

        if not winning_turns:
            return WinTurnStatistics(
                games_completed=summary.games_completed,
                wins=0,
                win_rate=0.0,
                fastest_win_turn=None,
                slowest_win_turn=None,
                average_win_turn=None,
                median_win_turn=None,
                percentile_90_win_turn=None,
                percentile_95_win_turn=None,
                win_turn_standard_deviation=None,
            )

        return WinTurnStatistics(
            games_completed=summary.games_completed,
            wins=summary.wins,
            win_rate=summary.win_rate,
            fastest_win_turn=winning_turns[0],
            slowest_win_turn=winning_turns[-1],
            average_win_turn=fmean(winning_turns),
            median_win_turn=float(median(winning_turns)),
            percentile_90_win_turn=self._nearest_rank(
                winning_turns,
                percentile=0.90,
            ),
            percentile_95_win_turn=self._nearest_rank(
                winning_turns,
                percentile=0.95,
            ),
            win_turn_standard_deviation=pstdev(
                winning_turns
            ),
        )

    @staticmethod
    def _nearest_rank(
        sorted_values: tuple[int, ...],
        *,
        percentile: float,
    ) -> int:
        """
        Return a nearest-rank percentile from ascending integer values.
        """
        if not sorted_values:
            raise ValueError(
                "sorted_values must not be empty."
            )

        if not 0.0 < percentile <= 1.0:
            raise ValueError(
                "percentile must be greater than 0.0 and at most 1.0."
            )

        if sorted_values != tuple(sorted(sorted_values)):
            raise ValueError(
                "sorted_values must be ordered ascending."
            )

        rank = ceil(
            percentile * len(sorted_values)
        )
        index = max(
            0,
            rank - 1,
        )

        return sorted_values[index]