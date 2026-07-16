from __future__ import annotations

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


def create_game_result(
    *,
    win: bool,
    turns_started: int = 3,
) -> GoldfishRunResult:
    return GoldfishRunResult(
        turns_started=turns_started,
        kinnan_activations=0,
        reached_turn_limit=not win,
        game_over=win,
        winner="Player" if win else None,
    )


def create_experiment_result(
    *,
    wins: int,
    games: int,
) -> ExperimentResult:
    config = SimulationConfig(
        games=games,
    )

    game_results = tuple(
        create_game_result(
            win=game_id < wins,
        )
        for game_id in range(games)
    )

    summary = SimulationSummary.from_results(
        games_requested=games,
        results=game_results,
    )

    return ExperimentResult(
        config=config,
        game_results=game_results,
        summary=summary,
    )


def test_calculate_returns_expected_observed_rate() -> None:
    interval = (
        WinRateConfidenceIntervalCalculator()
        .calculate(
            wins=70,
            games=100,
        )
    )

    assert interval.wins == 70
    assert interval.games == 100
    assert interval.observed_rate == pytest.approx(
        0.7
    )
    assert interval.confidence_level == pytest.approx(
        0.95
    )


def test_calculate_returns_known_wilson_interval() -> None:
    interval = (
        WinRateConfidenceIntervalCalculator()
        .calculate(
            wins=70,
            games=100,
        )
    )

    assert interval.lower_bound == pytest.approx(
        0.604151,
        abs=0.000001,
    )
    assert interval.upper_bound == pytest.approx(
        0.781052,
        abs=0.000001,
    )


def test_interval_contains_observed_rate() -> None:
    interval = (
        WinRateConfidenceIntervalCalculator()
        .calculate(
            wins=42,
            games=100,
        )
    )

    assert (
        interval.lower_bound
        <= interval.observed_rate
        <= interval.upper_bound
    )


def test_zero_wins_remains_bounded() -> None:
    interval = (
        WinRateConfidenceIntervalCalculator()
        .calculate(
            wins=0,
            games=100,
        )
    )

    assert interval.observed_rate == 0.0
    assert interval.lower_bound == 0.0
    assert 0.0 < interval.upper_bound < 1.0


def test_all_wins_remains_bounded() -> None:
    interval = (
        WinRateConfidenceIntervalCalculator()
        .calculate(
            wins=100,
            games=100,
        )
    )

    assert interval.observed_rate == 1.0
    assert 0.0 < interval.lower_bound < 1.0
    assert interval.upper_bound == 1.0


def test_larger_sample_produces_narrower_interval() -> None:
    calculator = WinRateConfidenceIntervalCalculator()

    small_sample = calculator.calculate(
        wins=7,
        games=10,
    )
    large_sample = calculator.calculate(
        wins=700,
        games=1_000,
    )

    assert large_sample.width < small_sample.width


def test_higher_confidence_produces_wider_interval() -> None:
    ninety_percent = (
        WinRateConfidenceIntervalCalculator(
            confidence_level=0.90,
        ).calculate(
            wins=70,
            games=100,
        )
    )
    ninety_nine_percent = (
        WinRateConfidenceIntervalCalculator(
            confidence_level=0.99,
        ).calculate(
            wins=70,
            games=100,
        )
    )

    assert (
        ninety_nine_percent.width
        > ninety_percent.width
    )


def test_from_summary_uses_existing_summary_values() -> None:
    result = create_experiment_result(
        wins=3,
        games=5,
    )

    interval = (
        WinRateConfidenceIntervalCalculator()
        .from_summary(result.summary)
    )

    assert interval.wins == 3
    assert interval.games == 5
    assert interval.observed_rate == pytest.approx(
        0.6
    )


def test_from_experiment_uses_experiment_summary() -> None:
    result = create_experiment_result(
        wins=4,
        games=10,
    )

    interval = (
        WinRateConfidenceIntervalCalculator()
        .from_experiment(result)
    )

    assert interval.wins == 4
    assert interval.games == 10
    assert interval.observed_rate == pytest.approx(
        result.summary.win_rate
    )


def test_interval_percentage_properties() -> None:
    interval = (
        WinRateConfidenceIntervalCalculator()
        .calculate(
            wins=70,
            games=100,
        )
    )

    assert interval.observed_percent == pytest.approx(
        interval.observed_rate * 100.0
    )
    assert interval.lower_percent == pytest.approx(
        interval.lower_bound * 100.0
    )
    assert interval.upper_percent == pytest.approx(
        interval.upper_bound * 100.0
    )


def test_interval_margin_properties() -> None:
    interval = (
        WinRateConfidenceIntervalCalculator()
        .calculate(
            wins=70,
            games=100,
        )
    )

    assert interval.width == pytest.approx(
        interval.upper_bound
        - interval.lower_bound
    )
    assert interval.margin_below == pytest.approx(
        interval.observed_rate
        - interval.lower_bound
    )
    assert interval.margin_above == pytest.approx(
        interval.upper_bound
        - interval.observed_rate
    )


@pytest.mark.parametrize(
    "games",
    (
        0,
        -1,
        -100,
    ),
)
def test_calculator_rejects_non_positive_games(
    games: int,
) -> None:
    calculator = WinRateConfidenceIntervalCalculator()

    with pytest.raises(
        ValueError,
        match="games must be at least 1.",
    ):
        calculator.calculate(
            wins=0,
            games=games,
        )


@pytest.mark.parametrize(
    "wins",
    (
        -1,
        -10,
    ),
)
def test_calculator_rejects_negative_wins(
    wins: int,
) -> None:
    calculator = WinRateConfidenceIntervalCalculator()

    with pytest.raises(
        ValueError,
        match="wins must not be negative.",
    ):
        calculator.calculate(
            wins=wins,
            games=100,
        )


def test_calculator_rejects_wins_above_games() -> None:
    calculator = WinRateConfidenceIntervalCalculator()

    with pytest.raises(
        ValueError,
        match="wins must not exceed games.",
    ):
        calculator.calculate(
            wins=101,
            games=100,
        )


@pytest.mark.parametrize(
    "confidence_level",
    (
        0.0,
        -0.1,
        1.0,
        1.1,
    ),
)
def test_calculator_rejects_invalid_confidence_level(
    confidence_level: float,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "confidence_level must be greater than 0.0 "
            "and less than 1.0."
        ),
    ):
        WinRateConfidenceIntervalCalculator(
            confidence_level=confidence_level,
        )


def test_confidence_interval_is_immutable() -> None:
    interval = (
        WinRateConfidenceIntervalCalculator()
        .calculate(
            wins=70,
            games=100,
        )
    )

    with pytest.raises(AttributeError):
        interval.lower_bound = 0.0  # type: ignore[misc]


def test_interval_rejects_invalid_bounds() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "lower_bound must not exceed "
            "observed_rate."
        ),
    ):
        WinRateConfidenceInterval(
            wins=50,
            games=100,
            observed_rate=0.5,
            lower_bound=0.6,
            upper_bound=0.8,
            confidence_level=0.95,
        )


def test_calculation_does_not_modify_experiment() -> None:
    result = create_experiment_result(
        wins=3,
        games=5,
    )

    original_summary = result.summary
    original_results = result.game_results
    original_config = result.config

    WinRateConfidenceIntervalCalculator().from_experiment(
        result
    )

    assert result.summary is original_summary
    assert result.game_results is original_results
    assert result.config is original_config

def test_zero_wins_in_ten_games_contains_observed_rate() -> None:
    interval = WinRateConfidenceIntervalCalculator().calculate(
        wins=0,
        games=10,
    )

    assert interval.observed_rate == 0.0
    assert interval.lower_bound == 0.0
    assert interval.upper_bound > 0.0
    assert (
        interval.lower_bound
        <= interval.observed_rate
        <= interval.upper_bound
    )


def test_ten_wins_in_ten_games_contains_observed_rate() -> None:
    interval = WinRateConfidenceIntervalCalculator().calculate(
        wins=10,
        games=10,
    )

    assert interval.observed_rate == 1.0
    assert interval.lower_bound < 1.0
    assert interval.upper_bound == 1.0
    assert (
        interval.lower_bound
        <= interval.observed_rate
        <= interval.upper_bound
    )

@pytest.mark.parametrize(
    "games",
    (
        1,
        2,
        3,
        10,
        100,
    ),
)
def test_boundary_results_always_contain_observed_rate(
    games: int,
) -> None:
    zero_win_interval = (
        WinRateConfidenceIntervalCalculator().calculate(
            wins=0,
            games=games,
        )
    )
    all_win_interval = (
        WinRateConfidenceIntervalCalculator().calculate(
            wins=games,
            games=games,
        )
    )

    assert zero_win_interval.lower_bound == 0.0
    assert (
        zero_win_interval.lower_bound
        <= zero_win_interval.observed_rate
        <= zero_win_interval.upper_bound
    )

    assert all_win_interval.upper_bound == 1.0
    assert (
        all_win_interval.lower_bound
        <= all_win_interval.observed_rate
        <= all_win_interval.upper_bound
    )