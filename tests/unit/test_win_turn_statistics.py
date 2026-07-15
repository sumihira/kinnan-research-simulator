from __future__ import annotations

import pytest

from krs.simulation.experiment import (
    ExperimentResult,
    SimulationSummary,
)
from krs.simulation.runner import GoldfishRunResult
from krs.simulation.simulation_config import SimulationConfig
from krs.statistics.win_turn_statistics import (
    WinTurnStatistics,
    WinTurnStatisticsCalculator,
)


def create_game_result(
    *,
    turns_started: int,
    win: bool = False,
    game_over: bool | None = None,
) -> GoldfishRunResult:
    resolved_game_over = (
        win
        if game_over is None
        else game_over
    )

    return GoldfishRunResult(
        turns_started=turns_started,
        kinnan_activations=0,
        reached_turn_limit=not win,
        game_over=resolved_game_over,
        winner="Player" if win else None,
    )


def create_experiment_result() -> ExperimentResult:
    config = SimulationConfig(
        games=10,
    )

    game_results = (
        create_game_result(
            turns_started=2,
            win=True,
        ),
        create_game_result(
            turns_started=3,
            win=True,
        ),
        create_game_result(
            turns_started=3,
            win=True,
        ),
        create_game_result(
            turns_started=4,
            win=True,
        ),
        create_game_result(
            turns_started=4,
            win=True,
        ),
        create_game_result(
            turns_started=5,
            win=True,
        ),
        create_game_result(
            turns_started=6,
        ),
        create_game_result(
            turns_started=6,
        ),
        create_game_result(
            turns_started=6,
            game_over=True,
        ),
        create_game_result(
            turns_started=6,
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


def create_no_win_result() -> ExperimentResult:
    config = SimulationConfig(
        games=2,
    )

    game_results = (
        create_game_result(
            turns_started=6,
        ),
        create_game_result(
            turns_started=6,
            game_over=True,
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


def test_calculate_returns_win_counts_and_rate() -> None:
    statistics = WinTurnStatisticsCalculator().calculate(
        create_experiment_result()
    )

    assert statistics.games_completed == 10
    assert statistics.wins == 6
    assert statistics.win_rate == pytest.approx(
        0.6
    )
    assert statistics.win_rate_percent == pytest.approx(
        60.0
    )
    assert statistics.has_wins is True


def test_calculate_returns_observed_turn_range() -> None:
    statistics = WinTurnStatisticsCalculator().calculate(
        create_experiment_result()
    )

    assert statistics.fastest_win_turn == 2
    assert statistics.slowest_win_turn == 5


def test_calculate_returns_average_and_median() -> None:
    statistics = WinTurnStatisticsCalculator().calculate(
        create_experiment_result()
    )

    assert statistics.average_win_turn == pytest.approx(
        3.5
    )
    assert statistics.median_win_turn == pytest.approx(
        3.5
    )


def test_calculate_returns_nearest_rank_percentiles() -> None:
    statistics = WinTurnStatisticsCalculator().calculate(
        create_experiment_result()
    )

    assert statistics.percentile_90_win_turn == 5
    assert statistics.percentile_95_win_turn == 5


def test_calculate_returns_population_standard_deviation() -> None:
    statistics = WinTurnStatisticsCalculator().calculate(
        create_experiment_result()
    )

    assert (
        statistics.win_turn_standard_deviation
        == pytest.approx(0.9574271077563381)
    )


def test_game_over_without_winner_is_excluded() -> None:
    statistics = WinTurnStatisticsCalculator().calculate(
        create_experiment_result()
    )

    assert statistics.wins == 6
    assert statistics.slowest_win_turn == 5


def test_no_wins_returns_empty_statistics() -> None:
    statistics = WinTurnStatisticsCalculator().calculate(
        create_no_win_result()
    )

    assert statistics.games_completed == 2
    assert statistics.wins == 0
    assert statistics.win_rate == 0.0
    assert statistics.has_wins is False
    assert statistics.fastest_win_turn is None
    assert statistics.slowest_win_turn is None
    assert statistics.average_win_turn is None
    assert statistics.median_win_turn is None
    assert statistics.percentile_90_win_turn is None
    assert statistics.percentile_95_win_turn is None
    assert statistics.win_turn_standard_deviation is None


def test_single_win_returns_zero_standard_deviation() -> None:
    config = SimulationConfig(
        games=1,
    )
    game_results = (
        create_game_result(
            turns_started=3,
            win=True,
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

    statistics = WinTurnStatisticsCalculator().calculate(
        result
    )

    assert statistics.fastest_win_turn == 3
    assert statistics.slowest_win_turn == 3
    assert statistics.average_win_turn == 3.0
    assert statistics.median_win_turn == 3.0
    assert statistics.percentile_90_win_turn == 3
    assert statistics.percentile_95_win_turn == 3
    assert statistics.win_turn_standard_deviation == 0.0


@pytest.mark.parametrize(
    ("percentile", "expected"),
    (
        (0.01, 1),
        (0.25, 1),
        (0.50, 2),
        (0.75, 3),
        (0.90, 4),
        (0.95, 4),
        (1.00, 4),
    ),
)
def test_nearest_rank_returns_expected_value(
    percentile: float,
    expected: int,
) -> None:
    result = WinTurnStatisticsCalculator._nearest_rank(
        (
            1,
            2,
            3,
            4,
        ),
        percentile=percentile,
    )

    assert result == expected


@pytest.mark.parametrize(
    "percentile",
    (
        0.0,
        -0.1,
        1.1,
    ),
)
def test_nearest_rank_rejects_invalid_percentile(
    percentile: float,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "percentile must be greater than 0.0 "
            "and at most 1.0."
        ),
    ):
        WinTurnStatisticsCalculator._nearest_rank(
            (
                1,
                2,
                3,
            ),
            percentile=percentile,
        )


def test_nearest_rank_rejects_empty_values() -> None:
    with pytest.raises(
        ValueError,
        match="sorted_values must not be empty.",
    ):
        WinTurnStatisticsCalculator._nearest_rank(
            (),
            percentile=0.5,
        )


def test_nearest_rank_rejects_unordered_values() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "sorted_values must be ordered ascending."
        ),
    ):
        WinTurnStatisticsCalculator._nearest_rank(
            (
                3,
                1,
                2,
            ),
            percentile=0.5,
        )


def test_statistics_is_immutable() -> None:
    statistics = WinTurnStatisticsCalculator().calculate(
        create_experiment_result()
    )

    with pytest.raises(AttributeError):
        statistics.wins = 0  # type: ignore[misc]


def test_statistics_rejects_inconsistent_win_rate() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "win_rate must equal wins divided by "
            "games_completed."
        ),
    ):
        WinTurnStatistics(
            games_completed=10,
            wins=5,
            win_rate=0.6,
            fastest_win_turn=2,
            slowest_win_turn=5,
            average_win_turn=3.0,
            median_win_turn=3.0,
            percentile_90_win_turn=5,
            percentile_95_win_turn=5,
            win_turn_standard_deviation=1.0,
        )


def test_statistics_rejects_values_when_no_wins() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Win-turn statistics must be None "
            "when wins is zero."
        ),
    ):
        WinTurnStatistics(
            games_completed=10,
            wins=0,
            win_rate=0.0,
            fastest_win_turn=3,
            slowest_win_turn=None,
            average_win_turn=None,
            median_win_turn=None,
            percentile_90_win_turn=None,
            percentile_95_win_turn=None,
            win_turn_standard_deviation=None,
        )


def test_calculation_does_not_modify_experiment() -> None:
    result = create_experiment_result()

    original_config = result.config
    original_summary = result.summary
    original_results = result.game_results

    WinTurnStatisticsCalculator().calculate(result)

    assert result.config is original_config
    assert result.summary is original_summary
    assert result.game_results is original_results