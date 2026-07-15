from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from krs.simulation.experiment import ExperimentResult


@dataclass(frozen=True, slots=True)
class DistributionPoint:
    """
    Stores one value and its observed frequency.

    percentage is calculated against the total number of observations in
    the distribution, not against the number of requested games.
    """

    value: int
    count: int
    percentage: float

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("value must not be negative.")

        if self.count < 1:
            raise ValueError("count must be at least 1.")

        if not 0.0 < self.percentage <= 1.0:
            raise ValueError(
                "percentage must be greater than 0.0 and at most 1.0."
            )


@dataclass(frozen=True, slots=True)
class DistributionData:
    """
    Stores an ordered frequency distribution.

    Points must be ordered by ascending value and must not contain duplicate
    values.
    """

    name: str
    points: tuple[DistributionPoint, ...]
    total_observations: int

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name must not be empty.")

        if self.total_observations < 0:
            raise ValueError(
                "total_observations must not be negative."
            )

        if not self.points:
            if self.total_observations != 0:
                raise ValueError(
                    "Empty distribution must have zero observations."
                )
            return

        values = tuple(
            point.value
            for point in self.points
        )

        if values != tuple(sorted(values)):
            raise ValueError(
                "Distribution points must be ordered by value."
            )

        if len(set(values)) != len(values):
            raise ValueError(
                "Distribution points must have unique values."
            )

        total_count = sum(
            point.count
            for point in self.points
        )

        if total_count != self.total_observations:
            raise ValueError(
                "Point counts must equal total_observations."
            )

    def count_for(
        self,
        value: int,
    ) -> int:
        """Return the observed count for one value."""
        for point in self.points:
            if point.value == value:
                return point.count

        return 0

    def percentage_for(
        self,
        value: int,
    ) -> float:
        """Return the observed percentage for one value."""
        for point in self.points:
            if point.value == value:
                return point.percentage

        return 0.0


@dataclass(frozen=True, slots=True)
class ExperimentGraphData:
    """
    Stores graph-ready distributions for one experiment.
    """

    win_turn_distribution: DistributionData
    kinnan_activation_distribution: DistributionData

    def __post_init__(self) -> None:
        if (
            self.win_turn_distribution.name
            == self.kinnan_activation_distribution.name
        ):
            raise ValueError(
                "Graph distributions must have unique names."
            )


@dataclass(frozen=True, slots=True)
class GraphDataReporter:
    """
    Builds graph-ready distribution data from ExperimentResult.

    This class does not render images and does not modify simulation results.
    """

    def build(
        self,
        result: ExperimentResult,
    ) -> ExperimentGraphData:
        """
        Build all graph distributions for one experiment.
        """
        return ExperimentGraphData(
            win_turn_distribution=(
                self.build_win_turn_distribution(result)
            ),
            kinnan_activation_distribution=(
                self.build_kinnan_activation_distribution(result)
            ),
        )

    def build_win_turn_distribution(
        self,
        result: ExperimentResult,
    ) -> DistributionData:
        """
        Build the winning-turn frequency distribution.

        Only completed games with a non-None winner are included.
        """
        winning_turns = tuple(
            game_result.turns_started
            for game_result in result.game_results
            if (
                game_result.game_over
                and game_result.winner is not None
            )
        )

        return self._build_distribution(
            name="win_turn",
            values=winning_turns,
        )

    def build_kinnan_activation_distribution(
        self,
        result: ExperimentResult,
    ) -> DistributionData:
        """
        Build the Kinnan activation frequency distribution.

        Every completed game is included, including games with zero
        activations and games that did not end in a win.
        """
        activation_counts = tuple(
            game_result.kinnan_activations
            for game_result in result.game_results
        )

        return self._build_distribution(
            name="kinnan_activations",
            values=activation_counts,
        )

    @staticmethod
    def _build_distribution(
        *,
        name: str,
        values: tuple[int, ...],
    ) -> DistributionData:
        """
        Convert integer observations into an ordered distribution.
        """
        if not values:
            return DistributionData(
                name=name,
                points=(),
                total_observations=0,
            )

        frequencies = Counter(values)
        total_observations = len(values)

        points = tuple(
            DistributionPoint(
                value=value,
                count=frequencies[value],
                percentage=(
                    frequencies[value]
                    / total_observations
                ),
            )
            for value in sorted(frequencies)
        )

        return DistributionData(
            name=name,
            points=points,
            total_observations=total_observations,
        )