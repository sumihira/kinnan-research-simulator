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
)
from krs.statistics.experiment_analysis import (
    ExperimentAnalysis,
    ExperimentAnalysisCalculator,
)
from krs.statistics.experiment_statistics import (
    ExperimentStatistics,
    ExperimentStatisticsCalculator,
)
from krs.statistics.win_turn_statistics import (
    WinTurnStatistics,
    WinTurnStatisticsCalculator,
)


def create_game_result(
    *,
    turns_started: int,
    kinnan_activations: int,
    win: bool = False,
    reached_turn_limit: bool = False,
) -> GoldfishRunResult:
    return GoldfishRunResult(
        turns_started=turns_started,
        kinnan_activations=kinnan_activations,
        reached_turn_limit=reached_turn_limit,
        game_over=win,
        winner="Player" if win else None,
    )


def create_experiment_result() -> ExperimentResult:
    config = SimulationConfig(
        games=4,
    )

    game_results = (
        create_game_result(
            turns_started=2,
            kinnan_activations=1,
            win=True,
        ),
        create_game_result(
            turns_started=4,
            kinnan_activations=2,
            win=True,
        ),
        create_game_result(
            turns_started=6,
            kinnan_activations=0,
            reached_turn_limit=True,
        ),
        create_game_result(
            turns_started=6,
            kinnan_activations=1,
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


def create_experiment_statistics(
    *,
    games_completed: int = 4,
    wins: int = 2,
    fastest_win_turn: int | None = 2,
) -> ExperimentStatistics:
    return ExperimentStatistics(
        games_completed=games_completed,
        wins=wins,
        non_wins=games_completed - wins,
        win_rate=wins / games_completed,
        win_rate_confidence_interval=(
            WinRateConfidenceInterval(
                wins=wins,
                games=games_completed,
                observed_rate=wins / games_completed,
                lower_bound=0.15,
                upper_bound=0.85,
                confidence_level=0.95,
            )
        ),
        turn_limit_games=2,
        turn_limit_rate=0.5,
        average_turns_started=4.5,
        turn_standard_deviation=1.6583123951777,
        average_kinnan_activations=1.0,
        kinnan_activation_standard_deviation=(
            0.7071067811865476
        ),
        fastest_win_turn=fastest_win_turn,
    )


def create_win_turn_statistics(
    *,
    games_completed: int = 4,
    wins: int = 2,
    fastest_win_turn: int | None = 2,
) -> WinTurnStatistics:
    if wins == 0:
        return WinTurnStatistics(
            games_completed=games_completed,
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
        games_completed=games_completed,
        wins=wins,
        win_rate=wins / games_completed,
        fastest_win_turn=fastest_win_turn,
        slowest_win_turn=4,
        average_win_turn=3.0,
        median_win_turn=3.0,
        percentile_90_win_turn=4,
        percentile_95_win_turn=4,
        win_turn_standard_deviation=1.0,
    )


def test_calculate_returns_complete_analysis() -> None:
    result = create_experiment_result()

    analysis = ExperimentAnalysisCalculator().calculate(
        result
    )

    assert isinstance(
        analysis,
        ExperimentAnalysis,
    )
    assert analysis.games_completed == 4
    assert analysis.wins == 2
    assert analysis.non_wins == 2
    assert analysis.win_rate == pytest.approx(0.5)
    assert analysis.win_rate_percent == pytest.approx(
        50.0
    )
    assert analysis.has_wins is True


def test_calculate_contains_experiment_statistics() -> None:
    result = create_experiment_result()

    analysis = ExperimentAnalysisCalculator().calculate(
        result
    )

    statistics = analysis.experiment_statistics

    assert statistics.games_completed == 4
    assert statistics.wins == 2
    assert statistics.turn_limit_games == 2
    assert statistics.average_turns_started == pytest.approx(
        4.5
    )
    assert statistics.average_kinnan_activations == pytest.approx(
        1.0
    )


def test_calculate_contains_win_turn_statistics() -> None:
    result = create_experiment_result()

    analysis = ExperimentAnalysisCalculator().calculate(
        result
    )

    statistics = analysis.win_turn_statistics

    assert statistics.wins == 2
    assert statistics.fastest_win_turn == 2
    assert statistics.slowest_win_turn == 4
    assert statistics.average_win_turn == pytest.approx(
        3.0
    )
    assert statistics.median_win_turn == pytest.approx(
        3.0
    )


def test_calculate_delegates_to_both_calculators() -> None:
    result = create_experiment_result()
    experiment_statistics = create_experiment_statistics()
    win_turn_statistics = create_win_turn_statistics()

    experiment_calculator = Mock(
        spec=ExperimentStatisticsCalculator,
    )
    experiment_calculator.calculate.return_value = (
        experiment_statistics
    )

    win_turn_calculator = Mock(
        spec=WinTurnStatisticsCalculator,
    )
    win_turn_calculator.calculate.return_value = (
        win_turn_statistics
    )

    calculator = ExperimentAnalysisCalculator(
        experiment_statistics_calculator=experiment_calculator,
        win_turn_statistics_calculator=win_turn_calculator,
    )

    analysis = calculator.calculate(result)

    experiment_calculator.calculate.assert_called_once_with(
        result
    )
    win_turn_calculator.calculate.assert_called_once_with(
        result
    )

    assert (
        analysis.experiment_statistics
        is experiment_statistics
    )
    assert (
        analysis.win_turn_statistics
        is win_turn_statistics
    )


def test_confidence_interval_properties() -> None:
    analysis = ExperimentAnalysisCalculator().calculate(
        create_experiment_result()
    )

    interval = (
        analysis.experiment_statistics
        .win_rate_confidence_interval
    )

    assert analysis.confidence_lower_bound == pytest.approx(
        interval.lower_bound
    )
    assert analysis.confidence_upper_bound == pytest.approx(
        interval.upper_bound
    )
    assert analysis.confidence_level == pytest.approx(
        interval.confidence_level
    )


def test_analysis_supports_no_wins() -> None:
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
            reached_turn_limit=True,
        ),
    )
    result = ExperimentResult(
        config=config,
        game_results=game_results,
        summary=SimulationSummary.from_results(
            games_requested=2,
            results=game_results,
        ),
    )

    analysis = ExperimentAnalysisCalculator().calculate(
        result
    )

    assert analysis.wins == 0
    assert analysis.non_wins == 2
    assert analysis.win_rate == 0.0
    assert analysis.has_wins is False
    assert (
        analysis.win_turn_statistics.fastest_win_turn
        is None
    )


def test_analysis_rejects_mismatched_game_counts() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Analysis statistics must use the same "
            "games_completed value."
        ),
    ):
        ExperimentAnalysis(
            experiment_statistics=(
                create_experiment_statistics(
                    games_completed=4,
                    wins=2,
                )
            ),
            win_turn_statistics=(
                create_win_turn_statistics(
                    games_completed=5,
                    wins=2,
                )
            ),
        )


def test_analysis_rejects_mismatched_win_counts() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Analysis statistics must use the same "
            "wins value."
        ),
    ):
        ExperimentAnalysis(
            experiment_statistics=(
                create_experiment_statistics(
                    games_completed=4,
                    wins=2,
                )
            ),
            win_turn_statistics=(
                create_win_turn_statistics(
                    games_completed=4,
                    wins=1,
                )
            ),
        )


def test_analysis_rejects_mismatched_fastest_win_turn() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Analysis statistics must use the same "
            "fastest_win_turn value."
        ),
    ):
        ExperimentAnalysis(
            experiment_statistics=(
                create_experiment_statistics(
                    fastest_win_turn=2,
                )
            ),
            win_turn_statistics=(
                create_win_turn_statistics(
                    fastest_win_turn=3,
                )
            ),
        )


def test_analysis_is_immutable() -> None:
    analysis = ExperimentAnalysisCalculator().calculate(
        create_experiment_result()
    )

    with pytest.raises(AttributeError):
        analysis.experiment_statistics = (  # type: ignore[misc]
            create_experiment_statistics()
        )


def test_calculation_does_not_modify_experiment() -> None:
    result = create_experiment_result()

    original_config = result.config
    original_summary = result.summary
    original_results = result.game_results

    ExperimentAnalysisCalculator().calculate(result)

    assert result.config is original_config
    assert result.summary is original_summary
    assert result.game_results is original_results