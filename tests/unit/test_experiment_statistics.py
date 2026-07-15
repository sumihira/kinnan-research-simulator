from __future__ import annotations

from unittest.mock import Mock

import pytest

from krs.simulation.experiment import (
    ExperimentResult,
    SimulationSummary,
)
from krs.simulation.runner import GoldfishRunResult
from krs.simulation.simulation_config import SimulationConfig
from krs.statistics.confidence_interval import (
    WinRateConfidenceInterval,
    WinRateConfidenceIntervalCalculator,
)
from krs.statistics.experiment_statistics import (
    ExperimentStatistics,
    ExperimentStatisticsCalculator,
)


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
        games=4,
    )

    game_results = (
        create_game_result(
            turns_started=2,
            kinnan_activations=0,
            game_over=True,
            winner="Player",
        ),
        create_game_result(
            turns_started=4,
            kinnan_activations=1,
            game_over=True,
            winner="Player",
        ),
        create_game_result(
            turns_started=6,
            kinnan_activations=2,
            reached_turn_limit=True,
        ),
        create_game_result(
            turns_started=8,
            kinnan_activations=3,
            reached_turn_limit=True,
        ),
    )

    summary = SimulationSummary.from_results(
        games_requested=config.games,
        results=game_results,
    )

    return ExperimentResult(
        config=config,
        game_results=game_results,
        summary=summary,
    )


def create_interval(
    *,
    wins: int = 2,
    games: int = 4,
) -> WinRateConfidenceInterval:
    return WinRateConfidenceInterval(
        wins=wins,
        games=games,
        observed_rate=wins / games,
        lower_bound=0.15,
        upper_bound=0.85,
        confidence_level=0.95,
    )


def test_calculate_returns_summary_values() -> None:
    result = create_experiment_result()

    statistics = (
        ExperimentStatisticsCalculator()
        .calculate(result)
    )

    assert statistics.games_completed == 4
    assert statistics.wins == 2
    assert statistics.non_wins == 2
    assert statistics.win_rate == pytest.approx(0.5)
    assert statistics.turn_limit_games == 2
    assert statistics.turn_limit_rate == pytest.approx(
        0.5
    )
    assert statistics.average_turns_started == pytest.approx(
        5.0
    )
    assert (
        statistics.average_kinnan_activations
        == pytest.approx(1.5)
    )
    assert statistics.fastest_win_turn == 2


def test_calculate_returns_population_turn_deviation() -> None:
    result = create_experiment_result()

    statistics = (
        ExperimentStatisticsCalculator()
        .calculate(result)
    )

    assert statistics.turn_standard_deviation == pytest.approx(
        2.23606797749979
    )


def test_calculate_returns_population_activation_deviation() -> None:
    result = create_experiment_result()

    statistics = (
        ExperimentStatisticsCalculator()
        .calculate(result)
    )

    assert (
        statistics.kinnan_activation_standard_deviation
        == pytest.approx(1.118033988749895)
    )


def test_calculate_uses_confidence_interval_calculator() -> None:
    result = create_experiment_result()
    expected_interval = create_interval()

    interval_calculator = Mock(
        spec=WinRateConfidenceIntervalCalculator,
    )
    interval_calculator.from_summary.return_value = (
        expected_interval
    )

    calculator = ExperimentStatisticsCalculator(
        confidence_interval_calculator=interval_calculator,
    )

    statistics = calculator.calculate(result)

    interval_calculator.from_summary.assert_called_once_with(
        result.summary
    )
    assert (
        statistics.win_rate_confidence_interval
        is expected_interval
    )


def test_calculate_supports_single_game() -> None:
    config = SimulationConfig(
        games=1,
    )
    game_results = (
        create_game_result(
            turns_started=3,
            kinnan_activations=2,
            game_over=True,
            winner="Player",
        ),
    )
    result = ExperimentResult(
        config=config,
        game_results=game_results,
        summary=SimulationSummary.from_results(
            games_requested=1,
            results=game_results,
        ),
    )

    statistics = (
        ExperimentStatisticsCalculator()
        .calculate(result)
    )

    assert statistics.turn_standard_deviation == 0.0
    assert (
        statistics.kinnan_activation_standard_deviation
        == 0.0
    )


def test_percentage_properties() -> None:
    statistics = (
        ExperimentStatisticsCalculator()
        .calculate(create_experiment_result())
    )

    assert statistics.win_rate_percent == pytest.approx(
        50.0
    )
    assert statistics.turn_limit_percent == pytest.approx(
        50.0
    )


def test_statistics_is_immutable() -> None:
    statistics = (
        ExperimentStatisticsCalculator()
        .calculate(create_experiment_result())
    )

    with pytest.raises(AttributeError):
        statistics.win_rate = 0.0  # type: ignore[misc]


def test_statistics_rejects_inconsistent_counts() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "wins and non_wins must equal "
            "games_completed."
        ),
    ):
        ExperimentStatistics(
            games_completed=4,
            wins=2,
            non_wins=1,
            win_rate=0.5,
            win_rate_confidence_interval=create_interval(),
            turn_limit_games=1,
            turn_limit_rate=0.25,
            average_turns_started=4.0,
            turn_standard_deviation=1.0,
            average_kinnan_activations=1.0,
            kinnan_activation_standard_deviation=0.5,
            fastest_win_turn=2,
        )


def test_statistics_rejects_mismatched_interval_games() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Confidence interval games must equal "
            "games_completed."
        ),
    ):
        ExperimentStatistics(
            games_completed=4,
            wins=2,
            non_wins=2,
            win_rate=0.5,
            win_rate_confidence_interval=create_interval(
                wins=2,
                games=5,
            ),
            turn_limit_games=1,
            turn_limit_rate=0.25,
            average_turns_started=4.0,
            turn_standard_deviation=1.0,
            average_kinnan_activations=1.0,
            kinnan_activation_standard_deviation=0.5,
            fastest_win_turn=2,
        )


def test_statistics_rejects_negative_deviation() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "turn_standard_deviation must not "
            "be negative."
        ),
    ):
        ExperimentStatistics(
            games_completed=4,
            wins=2,
            non_wins=2,
            win_rate=0.5,
            win_rate_confidence_interval=create_interval(),
            turn_limit_games=1,
            turn_limit_rate=0.25,
            average_turns_started=4.0,
            turn_standard_deviation=-1.0,
            average_kinnan_activations=1.0,
            kinnan_activation_standard_deviation=0.5,
            fastest_win_turn=2,
        )


def test_calculation_does_not_modify_experiment() -> None:
    result = create_experiment_result()

    original_config = result.config
    original_summary = result.summary
    original_results = result.game_results

    ExperimentStatisticsCalculator().calculate(result)

    assert result.config is original_config
    assert result.summary is original_summary
    assert result.game_results is original_results