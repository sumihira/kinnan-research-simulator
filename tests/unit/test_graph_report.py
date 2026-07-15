from __future__ import annotations

import pytest

from krs.report.graph import (
    DistributionData,
    DistributionPoint,
    ExperimentGraphData,
    GraphDataReporter,
)
from krs.simulation.experiment import (
    ExperimentResult,
    SimulationSummary,
)
from krs.simulation.runner import GoldfishRunResult
from krs.simulation.simulation_config import SimulationConfig


def create_game_result(
    *,
    turns_started: int,
    kinnan_activations: int,
    reached_turn_limit: bool = False,
    game_over: bool = False,
    winner: str | None = None,
) -> GoldfishRunResult:
    return GoldfishRunResult(
        turns_started=turns_started,
        kinnan_activations=kinnan_activations,
        reached_turn_limit=reached_turn_limit,
        game_over=game_over,
        winner=winner,
    )


def create_experiment_result() -> ExperimentResult:
    config = SimulationConfig(
        games=5,
    )

    game_results = (
        create_game_result(
            turns_started=3,
            kinnan_activations=2,
            game_over=True,
            winner="Player",
        ),
        create_game_result(
            turns_started=3,
            kinnan_activations=1,
            game_over=True,
            winner="Player",
        ),
        create_game_result(
            turns_started=5,
            kinnan_activations=2,
            game_over=True,
            winner="Player",
        ),
        create_game_result(
            turns_started=6,
            kinnan_activations=0,
            reached_turn_limit=True,
        ),
        create_game_result(
            turns_started=6,
            kinnan_activations=0,
            game_over=True,
            winner=None,
        ),
    )

    return ExperimentResult(
        config=config,
        game_results=game_results,
        summary=SimulationSummary.from_results(
            games_requested=config.games,
            results=game_results,
        ),
    )


def test_build_creates_both_distributions() -> None:
    result = create_experiment_result()

    graph_data = GraphDataReporter().build(result)

    assert isinstance(
        graph_data,
        ExperimentGraphData,
    )
    assert (
        graph_data.win_turn_distribution.name
        == "win_turn"
    )
    assert (
        graph_data.kinnan_activation_distribution.name
        == "kinnan_activations"
    )


def test_win_turn_distribution_includes_only_wins() -> None:
    result = create_experiment_result()

    distribution = (
        GraphDataReporter()
        .build_win_turn_distribution(result)
    )

    assert distribution.total_observations == 3
    assert len(distribution.points) == 2

    first_point = distribution.points[0]
    second_point = distribution.points[1]

    assert first_point.value == 3
    assert first_point.count == 2
    assert first_point.percentage == pytest.approx(2 / 3)

    assert second_point.value == 5
    assert second_point.count == 1
    assert second_point.percentage == pytest.approx(1 / 3)


def test_game_over_without_winner_is_not_a_win() -> None:
    result = create_experiment_result()

    distribution = (
        GraphDataReporter()
        .build_win_turn_distribution(result)
    )

    assert distribution.count_for(6) == 0


def test_kinnan_distribution_includes_every_game() -> None:
    result = create_experiment_result()

    distribution = (
        GraphDataReporter()
        .build_kinnan_activation_distribution(result)
    )

    assert distribution.total_observations == 5
    assert len(distribution.points) == 3

    zero_point = distribution.points[0]
    one_point = distribution.points[1]
    two_point = distribution.points[2]

    assert zero_point.value == 0
    assert zero_point.count == 2
    assert zero_point.percentage == pytest.approx(0.4)

    assert one_point.value == 1
    assert one_point.count == 1
    assert one_point.percentage == pytest.approx(0.2)

    assert two_point.value == 2
    assert two_point.count == 2
    assert two_point.percentage == pytest.approx(0.4)


def test_distribution_points_are_ordered_by_value() -> None:
    result = create_experiment_result()

    distribution = (
        GraphDataReporter()
        .build_kinnan_activation_distribution(result)
    )

    assert tuple(
        point.value
        for point in distribution.points
    ) == (
        0,
        1,
        2,
    )


def test_count_for_returns_matching_count() -> None:
    result = create_experiment_result()

    distribution = (
        GraphDataReporter()
        .build_kinnan_activation_distribution(result)
    )

    assert distribution.count_for(0) == 2
    assert distribution.count_for(1) == 1
    assert distribution.count_for(2) == 2


def test_count_for_returns_zero_for_missing_value() -> None:
    result = create_experiment_result()

    distribution = (
        GraphDataReporter()
        .build_kinnan_activation_distribution(result)
    )

    assert distribution.count_for(99) == 0


def test_percentage_for_returns_matching_percentage() -> None:
    result = create_experiment_result()

    distribution = (
        GraphDataReporter()
        .build_kinnan_activation_distribution(result)
    )

    assert distribution.percentage_for(0) == pytest.approx(
        0.4
    )
    assert distribution.percentage_for(2) == pytest.approx(
        0.4
    )


def test_percentage_for_returns_zero_for_missing_value() -> None:
    result = create_experiment_result()

    distribution = (
        GraphDataReporter()
        .build_kinnan_activation_distribution(result)
    )

    assert distribution.percentage_for(99) == 0.0


def test_win_distribution_is_empty_without_wins() -> None:
    config = SimulationConfig(
        games=2,
    )
    game_results = (
        create_game_result(
            turns_started=6,
            kinnan_activations=0,
            reached_turn_limit=True,
        ),
        create_game_result(
            turns_started=6,
            kinnan_activations=1,
            game_over=True,
            winner=None,
        ),
    )
    result = ExperimentResult(
        config=config,
        game_results=game_results,
        summary=SimulationSummary.from_results(
            games_requested=config.games,
            results=game_results,
        ),
    )

    distribution = (
        GraphDataReporter()
        .build_win_turn_distribution(result)
    )

    assert distribution == DistributionData(
        name="win_turn",
        points=(),
        total_observations=0,
    )


def test_kinnan_distribution_supports_zero_activations() -> None:
    config = SimulationConfig(
        games=1,
    )
    game_results = (
        create_game_result(
            turns_started=6,
            kinnan_activations=0,
            reached_turn_limit=True,
        ),
    )
    result = ExperimentResult(
        config=config,
        game_results=game_results,
        summary=SimulationSummary.from_results(
            games_requested=config.games,
            results=game_results,
        ),
    )

    distribution = (
        GraphDataReporter()
        .build_kinnan_activation_distribution(result)
    )

    assert distribution == DistributionData(
        name="kinnan_activations",
        points=(
            DistributionPoint(
                value=0,
                count=1,
                percentage=1.0,
            ),
        ),
        total_observations=1,
    )


def test_distribution_point_rejects_negative_value() -> None:
    with pytest.raises(
        ValueError,
        match="value must not be negative.",
    ):
        DistributionPoint(
            value=-1,
            count=1,
            percentage=1.0,
        )


def test_distribution_point_rejects_zero_count() -> None:
    with pytest.raises(
        ValueError,
        match="count must be at least 1.",
    ):
        DistributionPoint(
            value=1,
            count=0,
            percentage=1.0,
        )


@pytest.mark.parametrize(
    "percentage",
    (
        0.0,
        -0.1,
        1.1,
    ),
)
def test_distribution_point_rejects_invalid_percentage(
    percentage: float,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "percentage must be greater than 0.0 "
            "and at most 1.0."
        ),
    ):
        DistributionPoint(
            value=1,
            count=1,
            percentage=percentage,
        )


def test_distribution_rejects_unordered_points() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Distribution points must be "
            "ordered by value."
        ),
    ):
        DistributionData(
            name="test",
            points=(
                DistributionPoint(
                    value=2,
                    count=1,
                    percentage=0.5,
                ),
                DistributionPoint(
                    value=1,
                    count=1,
                    percentage=0.5,
                ),
            ),
            total_observations=2,
        )


def test_distribution_rejects_duplicate_values() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Distribution points must have "
            "unique values."
        ),
    ):
        DistributionData(
            name="test",
            points=(
                DistributionPoint(
                    value=1,
                    count=1,
                    percentage=0.5,
                ),
                DistributionPoint(
                    value=1,
                    count=1,
                    percentage=0.5,
                ),
            ),
            total_observations=2,
        )


def test_distribution_rejects_inconsistent_total() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Point counts must equal "
            "total_observations."
        ),
    ):
        DistributionData(
            name="test",
            points=(
                DistributionPoint(
                    value=1,
                    count=1,
                    percentage=1.0,
                ),
            ),
            total_observations=2,
        )


def test_graph_data_is_immutable() -> None:
    graph_data = GraphDataReporter().build(
        create_experiment_result()
    )

    with pytest.raises(AttributeError):
        graph_data.win_turn_distribution = (  # type: ignore[misc]
            graph_data.kinnan_activation_distribution
        )


def test_graph_report_does_not_modify_experiment_result() -> None:
    result = create_experiment_result()
    original_results = result.game_results
    original_summary = result.summary
    original_config = result.config

    GraphDataReporter().build(result)

    assert result.game_results is original_results
    assert result.summary is original_summary
    assert result.config is original_config