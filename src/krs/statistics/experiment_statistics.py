from __future__ import annotations

from dataclasses import dataclass
from statistics import pstdev

from krs.simulation.experiment import ExperimentResult
from krs.statistics.confidence_interval import (
    WinRateConfidenceInterval,
    WinRateConfidenceIntervalCalculator,
)


@dataclass(frozen=True, slots=True)
class ExperimentStatistics:
    """
    Stores analysis-ready statistics for one completed experiment.

    The statistics object contains both values already available from
    SimulationSummary and additional dispersion and confidence measurements.
    """

    games_completed: int
    wins: int
    non_wins: int
    win_rate: float
    win_rate_confidence_interval: WinRateConfidenceInterval
    turn_limit_games: int
    turn_limit_rate: float
    average_turns_started: float
    turn_standard_deviation: float
    average_kinnan_activations: float
    kinnan_activation_standard_deviation: float
    fastest_win_turn: int | None

    def __post_init__(self) -> None:
        if self.games_completed < 1:
            raise ValueError(
                "games_completed must be at least 1."
            )

        if self.wins < 0:
            raise ValueError(
                "wins must not be negative."
            )

        if self.non_wins < 0:
            raise ValueError(
                "non_wins must not be negative."
            )

        if self.wins + self.non_wins != self.games_completed:
            raise ValueError(
                "wins and non_wins must equal games_completed."
            )

        self._validate_rate(
            self.win_rate,
            field_name="win_rate",
        )
        self._validate_rate(
            self.turn_limit_rate,
            field_name="turn_limit_rate",
        )

        if self.turn_limit_games < 0:
            raise ValueError(
                "turn_limit_games must not be negative."
            )

        if self.turn_limit_games > self.games_completed:
            raise ValueError(
                "turn_limit_games must not exceed games_completed."
            )

        if self.average_turns_started < 0.0:
            raise ValueError(
                "average_turns_started must not be negative."
            )

        if self.turn_standard_deviation < 0.0:
            raise ValueError(
                "turn_standard_deviation must not be negative."
            )

        if self.average_kinnan_activations < 0.0:
            raise ValueError(
                "average_kinnan_activations must not be negative."
            )

        if self.kinnan_activation_standard_deviation < 0.0:
            raise ValueError(
                "kinnan_activation_standard_deviation "
                "must not be negative."
            )

        if (
            self.fastest_win_turn is not None
            and self.fastest_win_turn < 1
        ):
            raise ValueError(
                "fastest_win_turn must be at least 1."
            )

        interval = self.win_rate_confidence_interval

        if interval.games != self.games_completed:
            raise ValueError(
                "Confidence interval games must equal "
                "games_completed."
            )

        if interval.wins != self.wins:
            raise ValueError(
                "Confidence interval wins must equal wins."
            )

    @property
    def win_rate_percent(self) -> float:
        """Return the observed win rate as a percentage."""
        return self.win_rate * 100.0

    @property
    def turn_limit_percent(self) -> float:
        """Return the turn-limit rate as a percentage."""
        return self.turn_limit_rate * 100.0

    @staticmethod
    def _validate_rate(
        value: float,
        *,
        field_name: str,
    ) -> None:
        if not 0.0 <= value <= 1.0:
            raise ValueError(
                f"{field_name} must be between 0.0 and 1.0."
            )


@dataclass(frozen=True, slots=True)
class ExperimentStatisticsCalculator:
    """
    Calculates analysis-ready statistics from ExperimentResult.

    Existing aggregate values are read from SimulationSummary. Population
    standard deviations are calculated from the retained individual game
    results.
    """

    confidence_interval_calculator: (
        WinRateConfidenceIntervalCalculator
    ) = WinRateConfidenceIntervalCalculator()

    def calculate(
        self,
        result: ExperimentResult,
    ) -> ExperimentStatistics:
        """
        Calculate all supported statistics for one completed experiment.
        """
        summary = result.summary

        if summary.games_completed < 1:
            raise ValueError(
                "Cannot calculate statistics without completed games."
            )

        if len(result.game_results) != summary.games_completed:
            raise ValueError(
                "game_results count must equal games_completed."
            )

        turns_started = tuple(
            game_result.turns_started
            for game_result in result.game_results
        )
        kinnan_activations = tuple(
            game_result.kinnan_activations
            for game_result in result.game_results
        )

        confidence_interval = (
            self.confidence_interval_calculator.from_summary(
                summary
            )
        )

        return ExperimentStatistics(
            games_completed=summary.games_completed,
            wins=summary.wins,
            non_wins=summary.non_wins,
            win_rate=summary.win_rate,
            win_rate_confidence_interval=confidence_interval,
            turn_limit_games=summary.turn_limit_games,
            turn_limit_rate=(
                summary.turn_limit_games
                / summary.games_completed
            ),
            average_turns_started=(
                summary.average_turns_started
            ),
            turn_standard_deviation=pstdev(
                turns_started
            ),
            average_kinnan_activations=(
                summary.average_kinnan_activations
            ),
            kinnan_activation_standard_deviation=pstdev(
                kinnan_activations
            ),
            fastest_win_turn=summary.fastest_win_turn,
        )