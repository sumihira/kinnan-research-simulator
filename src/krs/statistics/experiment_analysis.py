from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from krs.simulation.experiment import ExperimentResult
from krs.statistics.experiment_statistics import (
    ExperimentStatistics,
    ExperimentStatisticsCalculator,
)
from krs.statistics.win_turn_statistics import (
    WinTurnStatistics,
    WinTurnStatisticsCalculator,
)


@dataclass(frozen=True, slots=True)
class ExperimentAnalysis:
    """
    Stores all supported statistical analysis for one experiment.

    General experiment statistics and winning-turn statistics are retained
    separately so each result type keeps its own focused responsibility.
    """

    experiment_statistics: ExperimentStatistics
    win_turn_statistics: WinTurnStatistics

    def __post_init__(self) -> None:
        experiment_statistics = self.experiment_statistics
        win_turn_statistics = self.win_turn_statistics

        if (
            experiment_statistics.games_completed
            != win_turn_statistics.games_completed
        ):
            raise ValueError(
                "Analysis statistics must use the same "
                "games_completed value."
            )

        if experiment_statistics.wins != win_turn_statistics.wins:
            raise ValueError(
                "Analysis statistics must use the same wins value."
            )

        if (
            abs(
                experiment_statistics.win_rate
                - win_turn_statistics.win_rate
            )
            > 1e-12
        ):
            raise ValueError(
                "Analysis statistics must use the same win_rate value."
            )

        if (
            experiment_statistics.fastest_win_turn
            != win_turn_statistics.fastest_win_turn
        ):
            raise ValueError(
                "Analysis statistics must use the same "
                "fastest_win_turn value."
            )

    @property
    def games_completed(self) -> int:
        """Return the completed game count."""
        return self.experiment_statistics.games_completed

    @property
    def wins(self) -> int:
        """Return the winning game count."""
        return self.experiment_statistics.wins

    @property
    def non_wins(self) -> int:
        """Return the non-winning game count."""
        return self.experiment_statistics.non_wins

    @property
    def win_rate(self) -> float:
        """Return the observed win rate."""
        return self.experiment_statistics.win_rate

    @property
    def win_rate_percent(self) -> float:
        """Return the observed win rate as a percentage."""
        return self.experiment_statistics.win_rate_percent

    @property
    def has_wins(self) -> bool:
        """Return whether the experiment contains a winning game."""
        return self.win_turn_statistics.has_wins

    @property
    def confidence_lower_bound(self) -> float:
        """Return the lower win-rate confidence bound."""
        return (
            self.experiment_statistics
            .win_rate_confidence_interval
            .lower_bound
        )

    @property
    def confidence_upper_bound(self) -> float:
        """Return the upper win-rate confidence bound."""
        return (
            self.experiment_statistics
            .win_rate_confidence_interval
            .upper_bound
        )

    @property
    def confidence_level(self) -> float:
        """Return the configured confidence level."""
        return (
            self.experiment_statistics
            .win_rate_confidence_interval
            .confidence_level
        )


@dataclass(frozen=True, slots=True)
class ExperimentAnalysisCalculator:
    """
    Coordinates all supported statistical calculators.

    The calculator acts as the statistics composition root. It delegates
    individual calculations and verifies that the returned results describe
    the same experiment.
    """

    experiment_statistics_calculator: (
        ExperimentStatisticsCalculator
    ) = field(
        default_factory=ExperimentStatisticsCalculator,
    )
    win_turn_statistics_calculator: (
        WinTurnStatisticsCalculator
    ) = field(
        default_factory=WinTurnStatisticsCalculator,
    )

    def calculate(
        self,
        result: ExperimentResult,
    ) -> ExperimentAnalysis:
        """
        Calculate complete statistical analysis for one experiment.
        """
        experiment_statistics = (
            self.experiment_statistics_calculator.calculate(
                result
            )
        )
        win_turn_statistics = (
            self.win_turn_statistics_calculator.calculate(
                result
            )
        )

        return ExperimentAnalysis(
            experiment_statistics=experiment_statistics,
            win_turn_statistics=win_turn_statistics,
        )