from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from krs.report.analysis_html import (
    ExperimentAnalysisHtmlReporter,
)
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

    return ExperimentResult(
        config=config,
        game_results=game_results,
        summary=SimulationSummary.from_results(
            games_requested=config.games,
            results=game_results,
        ),
    )


def create_analysis(
    *,
    wins: int = 2,
) -> ExperimentAnalysis:
    games = 4
    win_rate = wins / games

    interval = WinRateConfidenceInterval(
        wins=wins,
        games=games,
        observed_rate=win_rate,
        lower_bound=0.15 if wins else 0.0,
        upper_bound=0.85 if wins else 0.49,
        confidence_level=0.95,
    )

    experiment_statistics = ExperimentStatistics(
        games_completed=games,
        wins=wins,
        non_wins=games - wins,
        win_rate=win_rate,
        win_rate_confidence_interval=interval,
        turn_limit_games=2,
        turn_limit_rate=0.5,
        average_turns_started=4.5,
        turn_standard_deviation=1.6583123951777,
        average_kinnan_activations=1.0,
        kinnan_activation_standard_deviation=(
            0.7071067811865476
        ),
        fastest_win_turn=2 if wins else None,
    )

    if wins == 0:
        win_turn_statistics = WinTurnStatistics(
            games_completed=games,
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
    else:
        win_turn_statistics = WinTurnStatistics(
            games_completed=games,
            wins=wins,
            win_rate=win_rate,
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

    reporter = ExperimentAnalysisHtmlReporter(
        analysis_calculator=calculator,
    )

    analysis = reporter.analyze(result)

    calculator.calculate.assert_called_once_with(result)
    assert analysis is expected_analysis


def test_to_html_calculates_analysis_once() -> None:
    result = create_experiment_result()

    calculator = Mock(
        spec=ExperimentAnalysisCalculator,
    )
    calculator.calculate.return_value = create_analysis()

    reporter = ExperimentAnalysisHtmlReporter(
        analysis_calculator=calculator,
    )

    reporter.to_html(result)

    calculator.calculate.assert_called_once_with(result)


def test_analysis_to_html_returns_complete_document() -> None:
    html = (
        ExperimentAnalysisHtmlReporter()
        .analysis_to_html(create_analysis())
    )

    assert html.startswith("<!DOCTYPE html>")
    assert '<html lang="en">' in html
    assert '<meta charset="utf-8">' in html
    assert "</body>" in html
    assert "</html>" in html


def test_html_contains_overview_values() -> None:
    html = (
        ExperimentAnalysisHtmlReporter()
        .analysis_to_html(create_analysis())
    )

    assert "4 games analyzed" in html
    assert "Win rate" in html
    assert "50.00%" in html
    assert ">2<" in html
    assert "Confidence level" in html
    assert "95.0%" in html


def test_html_contains_confidence_interval() -> None:
    html = (
        ExperimentAnalysisHtmlReporter()
        .analysis_to_html(create_analysis())
    )

    assert "Win Rate Confidence Interval" in html
    assert "Observed win rate" in html
    assert "Lower bound" in html
    assert "15.000%" in html
    assert "Upper bound" in html
    assert "85.000%" in html
    assert "70.000 percentage points" in html
    assert "2 / 4" in html


def test_html_contains_interval_visual() -> None:
    html = (
        ExperimentAnalysisHtmlReporter()
        .analysis_to_html(create_analysis())
    )

    assert 'class="interval-track"' in html
    assert 'class="interval-range"' in html
    assert 'class="interval-observed"' in html
    assert "left: 15.000000%" in html
    assert "width: 70.000000%" in html
    assert "left: 50.000000%" in html


def test_html_contains_experiment_statistics() -> None:
    html = (
        ExperimentAnalysisHtmlReporter()
        .analysis_to_html(create_analysis())
    )

    assert "Experiment Statistics" in html
    assert "Turn-limit games" in html
    assert "Turn-limit rate" in html
    assert "Average turns started" in html
    assert "4.500" in html
    assert "Turn standard deviation" in html
    assert "1.658" in html
    assert "Average Kinnan activations" in html
    assert "Kinnan activation standard deviation" in html
    assert "0.707" in html


def test_html_contains_win_turn_statistics() -> None:
    html = (
        ExperimentAnalysisHtmlReporter()
        .analysis_to_html(create_analysis())
    )

    assert "Win Turn Statistics" in html
    assert "Fastest win turn" in html
    assert "Slowest win turn" in html
    assert "Average win turn" in html
    assert "Median win turn" in html
    assert "90th percentile win turn" in html
    assert "95th percentile win turn" in html
    assert "Win-turn standard deviation" in html


def test_html_supports_no_wins() -> None:
    html = (
        ExperimentAnalysisHtmlReporter()
        .analysis_to_html(
            create_analysis(
                wins=0,
            )
        )
    )

    assert "0.00%" in html
    assert (
        "No winning games were observed."
        in html
    )
    assert html.count(">N/A<") == 8


def test_html_escapes_title() -> None:
    html = ExperimentAnalysisHtmlReporter(
        title="<script>alert('x')</script>",
    ).analysis_to_html(create_analysis())

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_write_creates_html_file(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = ExperimentAnalysisHtmlReporter()

    output_path = tmp_path / "analysis.html"

    returned_path = reporter.write(
        result,
        output_path,
    )

    assert returned_path == output_path
    assert output_path.is_file()

    content = output_path.read_text(
        encoding="utf-8",
    )

    assert content == reporter.to_html(result)


def test_write_creates_parent_directories(
    tmp_path: Path,
) -> None:
    output_path = (
        tmp_path
        / "reports"
        / "analysis"
        / "analysis.html"
    )

    ExperimentAnalysisHtmlReporter().write(
        create_experiment_result(),
        output_path,
    )

    assert output_path.is_file()


@pytest.mark.parametrize(
    "filename",
    (
        "analysis.html",
        "analysis.htm",
        "ANALYSIS.HTML",
    ),
)
def test_write_accepts_html_extensions(
    tmp_path: Path,
    filename: str,
) -> None:
    output_path = tmp_path / filename

    ExperimentAnalysisHtmlReporter().write(
        create_experiment_result(),
        output_path,
    )

    assert output_path.is_file()


def test_write_rejects_directory_path(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Analysis HTML report path is a directory"
        ),
    ):
        ExperimentAnalysisHtmlReporter().write(
            create_experiment_result(),
            tmp_path,
        )


@pytest.mark.parametrize(
    "filename",
    (
        "analysis.json",
        "analysis.txt",
        "analysis",
    ),
)
def test_write_rejects_invalid_extension(
    tmp_path: Path,
    filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Analysis HTML report path must use "
            "the .html or .htm extension."
        ),
    ):
        ExperimentAnalysisHtmlReporter().write(
            create_experiment_result(),
            tmp_path / filename,
        )


@pytest.mark.parametrize(
    "title",
    (
        "",
        " ",
        "\t",
        "\n",
    ),
)
def test_reporter_rejects_empty_title(
    title: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="title must not be empty.",
    ):
        ExperimentAnalysisHtmlReporter(
            title=title,
        )


def test_report_does_not_modify_experiment_result() -> None:
    result = create_experiment_result()

    original_config = result.config
    original_summary = result.summary
    original_results = result.game_results

    ExperimentAnalysisHtmlReporter().to_html(result)

    assert result.config is original_config
    assert result.summary is original_summary
    assert result.game_results is original_results