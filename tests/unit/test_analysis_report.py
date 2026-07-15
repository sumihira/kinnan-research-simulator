from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from krs.report.analysis import ExperimentAnalysisReporter
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
)
from krs.statistics.win_turn_statistics import (
    WinTurnStatistics,
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


def create_analysis() -> ExperimentAnalysis:
    interval = WinRateConfidenceInterval(
        wins=2,
        games=4,
        observed_rate=0.5,
        lower_bound=0.15,
        upper_bound=0.85,
        confidence_level=0.95,
    )

    experiment_statistics = ExperimentStatistics(
        games_completed=4,
        wins=2,
        non_wins=2,
        win_rate=0.5,
        win_rate_confidence_interval=interval,
        turn_limit_games=2,
        turn_limit_rate=0.5,
        average_turns_started=4.5,
        turn_standard_deviation=1.6583123951777,
        average_kinnan_activations=1.0,
        kinnan_activation_standard_deviation=(
            0.7071067811865476
        ),
        fastest_win_turn=2,
    )

    win_turn_statistics = WinTurnStatistics(
        games_completed=4,
        wins=2,
        win_rate=0.5,
        fastest_win_turn=2,
        slowest_win_turn=4,
        average_win_turn=3.0,
        median_win_turn=3.0,
        percentile_90_win_turn=4,
        percentile_95_win_turn=4,
        win_turn_standard_deviation=1.0,
    )

    return ExperimentAnalysis(
        experiment_statistics=experiment_statistics,
        win_turn_statistics=win_turn_statistics,
    )


def test_analyze_delegates_to_calculator() -> None:
    result = create_experiment_result()
    expected_analysis = create_analysis()

    calculator = Mock(
        spec=ExperimentAnalysisCalculator,
    )
    calculator.calculate.return_value = expected_analysis

    reporter = ExperimentAnalysisReporter(
        analysis_calculator=calculator,
    )

    analysis = reporter.analyze(result)

    calculator.calculate.assert_called_once_with(result)
    assert analysis is expected_analysis


def test_to_dict_contains_overview() -> None:
    analysis = create_analysis()

    report = (
        ExperimentAnalysisReporter()
        .analysis_to_dict(analysis)
    )

    assert report["overview"] == {
        "games_completed": 4,
        "wins": 2,
        "non_wins": 2,
        "win_rate": 0.5,
        "win_rate_percent": 50.0,
        "has_wins": True,
    }


def test_to_dict_contains_confidence_interval() -> None:
    analysis = create_analysis()

    report = (
        ExperimentAnalysisReporter()
        .analysis_to_dict(analysis)
    )

    interval = report["confidence_interval"]

    assert interval["confidence_level"] == 0.95
    assert interval["wins"] == 2
    assert interval["games"] == 4
    assert interval["observed_rate"] == 0.5
    assert interval["lower_bound"] == 0.15
    assert interval["upper_bound"] == 0.85
    assert interval["width"] == pytest.approx(0.7)
    assert interval["margin_below"] == pytest.approx(
        0.35
    )
    assert interval["margin_above"] == pytest.approx(
        0.35
    )
    assert interval["observed_percent"] == 50.0
    assert interval["lower_percent"] == 15.0
    assert interval["upper_percent"] == 85.0


def test_to_dict_contains_experiment_statistics() -> None:
    analysis = create_analysis()

    report = (
        ExperimentAnalysisReporter()
        .analysis_to_dict(analysis)
    )

    statistics = report["experiment_statistics"]

    assert statistics["turn_limit_games"] == 2
    assert statistics["turn_limit_rate"] == 0.5
    assert statistics["turn_limit_percent"] == 50.0
    assert statistics["average_turns_started"] == 4.5
    assert statistics[
        "turn_standard_deviation"
    ] == pytest.approx(1.6583123951777)
    assert statistics[
        "average_kinnan_activations"
    ] == 1.0
    assert statistics[
        "kinnan_activation_standard_deviation"
    ] == pytest.approx(
        0.7071067811865476
    )
    assert statistics["fastest_win_turn"] == 2


def test_to_dict_contains_win_turn_statistics() -> None:
    analysis = create_analysis()

    report = (
        ExperimentAnalysisReporter()
        .analysis_to_dict(analysis)
    )

    statistics = report["win_turn_statistics"]

    assert statistics == {
        "wins": 2,
        "win_rate": 0.5,
        "win_rate_percent": 50.0,
        "has_wins": True,
        "fastest_win_turn": 2,
        "slowest_win_turn": 4,
        "average_win_turn": 3.0,
        "median_win_turn": 3.0,
        "percentile_90_win_turn": 4,
        "percentile_95_win_turn": 4,
        "win_turn_standard_deviation": 1.0,
    }


def test_to_dict_calculates_analysis_once() -> None:
    result = create_experiment_result()
    expected_analysis = create_analysis()

    calculator = Mock(
        spec=ExperimentAnalysisCalculator,
    )
    calculator.calculate.return_value = expected_analysis

    reporter = ExperimentAnalysisReporter(
        analysis_calculator=calculator,
    )

    report = reporter.to_dict(result)

    calculator.calculate.assert_called_once_with(result)
    assert report["overview"]["wins"] == 2


def test_to_json_returns_valid_json() -> None:
    result = create_experiment_result()
    reporter = ExperimentAnalysisReporter()

    serialized = reporter.to_json(result)
    decoded = json.loads(serialized)

    assert decoded == reporter.to_dict(result)


def test_to_json_supports_compact_output() -> None:
    result = create_experiment_result()

    serialized = ExperimentAnalysisReporter(
        indent=None,
    ).to_json(result)

    assert "\n" not in serialized


def test_write_creates_analysis_file(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = ExperimentAnalysisReporter()

    output_path = tmp_path / "analysis.json"

    returned_path = reporter.write(
        result,
        output_path,
    )

    assert returned_path == output_path
    assert output_path.is_file()

    decoded = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert decoded == reporter.to_dict(result)


def test_write_creates_parent_directories(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    output_path = (
        tmp_path
        / "reports"
        / "statistics"
        / "analysis.json"
    )

    ExperimentAnalysisReporter().write(
        result,
        output_path,
    )

    assert output_path.is_file()


def test_write_adds_trailing_newline(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    output_path = tmp_path / "analysis.json"

    ExperimentAnalysisReporter().write(
        result,
        output_path,
    )

    assert output_path.read_text(
        encoding="utf-8",
    ).endswith("\n")


def test_write_rejects_directory_path(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    with pytest.raises(
        ValueError,
        match="Analysis report path is a directory",
    ):
        ExperimentAnalysisReporter().write(
            result,
            tmp_path,
        )


@pytest.mark.parametrize(
    "filename",
    (
        "analysis.txt",
        "analysis.csv",
        "analysis",
    ),
)
def test_write_rejects_invalid_extension(
    tmp_path: Path,
    filename: str,
) -> None:
    result = create_experiment_result()

    with pytest.raises(
        ValueError,
        match=(
            "Analysis report path must use "
            "the .json extension."
        ),
    ):
        ExperimentAnalysisReporter().write(
            result,
            tmp_path / filename,
        )


def test_reporter_rejects_negative_indent() -> None:
    with pytest.raises(
        ValueError,
        match="indent must not be negative.",
    ):
        ExperimentAnalysisReporter(
            indent=-1,
        )


def test_report_supports_no_wins() -> None:
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

    report = ExperimentAnalysisReporter().to_dict(
        result
    )

    assert report["overview"]["has_wins"] is False
    assert (
        report["win_turn_statistics"]
        ["fastest_win_turn"]
        is None
    )
    assert (
        report["win_turn_statistics"]
        ["average_win_turn"]
        is None
    )


def test_report_does_not_modify_experiment_result() -> None:
    result = create_experiment_result()

    original_config = result.config
    original_summary = result.summary
    original_results = result.game_results

    ExperimentAnalysisReporter().to_dict(result)

    assert result.config is original_config
    assert result.summary is original_summary
    assert result.game_results is original_results