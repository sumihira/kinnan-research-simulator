from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import NormalDist

from krs.simulation.experiment import ExperimentResult
from krs.simulation.experiment import SimulationSummary


@dataclass(frozen=True, slots=True)
class WinRateConfidenceInterval:
    """
    Stores a confidence interval for an observed simulation win rate.

    All rates and bounds are represented as values from 0.0 through 1.0.
    """

    wins: int
    games: int
    observed_rate: float
    lower_bound: float
    upper_bound: float
    confidence_level: float

    def __post_init__(self) -> None:
        if self.games < 1:
            raise ValueError("games must be at least 1.")

        if self.wins < 0:
            raise ValueError("wins must not be negative.")

        if self.wins > self.games:
            raise ValueError("wins must not exceed games.")

        self._validate_probability(
            self.observed_rate,
            field_name="observed_rate",
        )
        self._validate_probability(
            self.lower_bound,
            field_name="lower_bound",
        )
        self._validate_probability(
            self.upper_bound,
            field_name="upper_bound",
        )

        if not 0.0 < self.confidence_level < 1.0:
            raise ValueError(
                "confidence_level must be greater than 0.0 "
                "and less than 1.0."
            )

        if self.lower_bound > self.observed_rate:
            raise ValueError(
                "lower_bound must not exceed observed_rate."
            )

        if self.observed_rate > self.upper_bound:
            raise ValueError(
                "observed_rate must not exceed upper_bound."
            )

    @property
    def width(self) -> float:
        """Return the total confidence interval width."""
        return self.upper_bound - self.lower_bound

    @property
    def margin_below(self) -> float:
        """Return the distance from the observed rate to the lower bound."""
        return self.observed_rate - self.lower_bound

    @property
    def margin_above(self) -> float:
        """Return the distance from the observed rate to the upper bound."""
        return self.upper_bound - self.observed_rate

    @property
    def observed_percent(self) -> float:
        """Return the observed rate as a percentage."""
        return self.observed_rate * 100.0

    @property
    def lower_percent(self) -> float:
        """Return the lower bound as a percentage."""
        return self.lower_bound * 100.0

    @property
    def upper_percent(self) -> float:
        """Return the upper bound as a percentage."""
        return self.upper_bound * 100.0

    @staticmethod
    def _validate_probability(
        value: float,
        *,
        field_name: str,
    ) -> None:
        if not 0.0 <= value <= 1.0:
            raise ValueError(
                f"{field_name} must be between 0.0 and 1.0."
            )


@dataclass(frozen=True, slots=True)
class WinRateConfidenceIntervalCalculator:
    """
    Calculates Wilson score confidence intervals for simulation win rates.

    Wilson intervals are used instead of a normal approximation because
    they remain bounded between 0.0 and 1.0 and behave better near zero or
    one observed win rate.
    """

    confidence_level: float = 0.95

    def __post_init__(self) -> None:
        if not 0.0 < self.confidence_level < 1.0:
            raise ValueError(
                "confidence_level must be greater than 0.0 "
                "and less than 1.0."
            )

    def calculate(
        self,
        *,
        wins: int,
        games: int,
    ) -> WinRateConfidenceInterval:
        """
        Calculate a Wilson score interval from wins and completed games.

        Floating-point rounding can place the calculated lower bound
        slightly above an observed rate of 0.0, or the upper bound slightly
        below an observed rate of 1.0. The final bounds are therefore
        clamped so the interval always contains the observed rate.
        """
        self._validate_counts(
            wins=wins,
            games=games,
        )

        observed_rate = wins / games
        z_score = self._z_score()

        z_squared = z_score**2
        denominator = 1.0 + (z_squared / games)

        center = (
            observed_rate
            + (z_squared / (2.0 * games))
        ) / denominator

        spread = (
            z_score
            * sqrt(
                (
                    observed_rate
                    * (1.0 - observed_rate)
                    / games
                )
                + (
                    z_squared
                    / (4.0 * games**2)
                )
            )
        ) / denominator

        calculated_lower_bound = center - spread
        calculated_upper_bound = center + spread

        lower_bound = max(
            0.0,
            min(
                calculated_lower_bound,
                observed_rate,
            ),
        )
        upper_bound = min(
            1.0,
            max(
                calculated_upper_bound,
                observed_rate,
            ),
        )

        return WinRateConfidenceInterval(
            wins=wins,
            games=games,
            observed_rate=observed_rate,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            confidence_level=self.confidence_level,
        )

    def from_summary(
        self,
        summary: SimulationSummary,
    ) -> WinRateConfidenceInterval:
        """
        Calculate an interval from an existing SimulationSummary.
        """
        return self.calculate(
            wins=summary.wins,
            games=summary.games_completed,
        )

    def from_experiment(
        self,
        result: ExperimentResult,
    ) -> WinRateConfidenceInterval:
        """
        Calculate an interval from an existing ExperimentResult.
        """
        return self.from_summary(result.summary)

    def _z_score(self) -> float:
        """
        Return the two-sided standard normal critical value.
        """
        tail_probability = (
            1.0 + self.confidence_level
        ) / 2.0

        return NormalDist().inv_cdf(
            tail_probability
        )

    @staticmethod
    def _validate_counts(
        *,
        wins: int,
        games: int,
    ) -> None:
        if games < 1:
            raise ValueError("games must be at least 1.")

        if wins < 0:
            raise ValueError("wins must not be negative.")

        if wins > games:
            raise ValueError("wins must not exceed games.")