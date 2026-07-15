from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from krs.report.analysis_markdown import (
    ExperimentAnalysisMarkdownReporter,
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

    confidence_interval = WinRateConfidenceInterval(
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
        win_rate_confidence_interval=confidence_interval,
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

    reporter = ExperimentAnalysisMarkdownReporter(
        analysis_calculator=calculator,
    )

    analysis = reporter.analyze(result)

    calculator.calculate.assert_called_once_with(result)
    assert analysis is expected_analysis


def test_to_markdown_calculates_analysis_once() -> None:
    result = create_experiment_result()
    expected_analysis = create_analysis()

    calculator = Mock(
        spec=ExperimentAnalysisCalculator,
    )
    calculator.calculate.return_value = expected_analysis

    reporter = ExperimentAnalysisMarkdownReporter(
        analysis_calculator=calculator,
    )

    markdown = reporter.to_markdown(result)

    calculator.calculate.assert_called_once_with(result)
    assert markdown.startswith(
        "# Kinnan Research Simulator Analysis"
    )


def test_analysis_to_markdown_contains_title() -> None:
    markdown = (
        ExperimentAnalysisMarkdownReporter()
        .analysis_to_markdown(create_analysis())
    )

    assert markdown.startswith(
        "# Kinnan Research Simulator Analysis"
    )
    assert markdown.endswith("\n")


def test_analysis_to_markdown_contains_custom_title() -> None:
    markdown = ExperimentAnalysisMarkdownReporter(
        title="KRS Statistical Report",
    ).analysis_to_markdown(create_analysis())

    assert markdown.startswith(
        "# KRS Statistical Report"
    )


def test_markdown_contains_all_sections() -> None:
    markdown = (
        ExperimentAnalysisMarkdownReporter()
        .analysis_to_markdown(create_analysis())
    )

    assert "## Overview" in markdown
    assert "## Win Rate Confidence Interval" in markdown
    assert "## Experiment Statistics" in markdown
    assert "## Win Turn Statistics" in markdown


def test_markdown_uses_section_separators() -> None:
    markdown = (
        ExperimentAnalysisMarkdownReporter()
        .analysis_to_markdown(create_analysis())
    )

    assert markdown.count("\n\n---\n\n") == 4


def test_markdown_contains_github_compatible_tables() -> None:
    markdown = (
        ExperimentAnalysisMarkdownReporter()
        .analysis_to_markdown(create_analysis())
    )

    assert markdown.count("| Metric | Value |") == 4
    assert markdown.count("|:--|--:|") == 4


def test_markdown_contains_overview_values() -> None:
    markdown = (
        ExperimentAnalysisMarkdownReporter()
        .analysis_to_markdown(create_analysis())
    )

    assert "| Games completed | 4 |" in markdown
    assert "| Wins | 2 |" in markdown
    assert "| Non-wins | 2 |" in markdown
    assert "| Win rate | 50.000% |" in markdown
    assert "| Winning games observed | Yes |" in markdown


def test_markdown_contains_confidence_interval_values() -> None:
    markdown = (
        ExperimentAnalysisMarkdownReporter()
        .analysis_to_markdown(create_analysis())
    )

    assert "| Confidence level | 95.000% |" in markdown
    assert "| Wins / Games | 2 / 4 |" in markdown
    assert "| Observed win rate | 50.000% |" in markdown
    assert "| Lower bound | 15.000% |" in markdown
    assert "| Upper bound | 85.000% |" in markdown
    assert (
        "| Interval width | "
        "70.000 percentage points |"
        in markdown
    )
    assert (
        "| Margin below | "
        "35.000 percentage points |"
        in markdown
    )
    assert (
        "| Margin above | "
        "35.000 percentage points |"
        in markdown
    )


def test_markdown_contains_experiment_statistics() -> None:
    markdown = (
        ExperimentAnalysisMarkdownReporter()
        .analysis_to_markdown(create_analysis())
    )

    assert "| Turn-limit games | 2 |" in markdown
    assert "| Turn-limit rate | 50.000% |" in markdown
    assert "| Average turns started | 4.500 |" in markdown
    assert "| Turn standard deviation | 1.658 |" in markdown
    assert (
        "| Average Kinnan activations | 1.000 |"
        in markdown
    )
    assert (
        "| Kinnan activation standard deviation | "
        "0.707 |"
        in markdown
    )
    assert "| Fastest win turn | 2 |" in markdown


def test_markdown_contains_win_turn_statistics() -> None:
    markdown = (
        ExperimentAnalysisMarkdownReporter()
        .analysis_to_markdown(create_analysis())
    )

    assert "| Winning games | 2 |" in markdown
    assert "| Win rate | 50.000% |" in markdown
    assert "| Fastest win turn | 2 |" in markdown
    assert "| Slowest win turn | 4 |" in markdown
    assert "| Average win turn | 3.000 |" in markdown
    assert "| Median win turn | 3.000 |" in markdown
    assert "| 90th percentile win turn | 4 |" in markdown
    assert "| 95th percentile win turn | 4 |" in markdown
    assert (
        "| Win-turn standard deviation | 1.000 |"
        in markdown
    )


def test_markdown_supports_no_wins() -> None:
    markdown = (
        ExperimentAnalysisMarkdownReporter()
        .analysis_to_markdown(
            create_analysis(
                wins=0,
            )
        )
    )

    assert "| Wins | 0 |" in markdown
    assert "| Win rate | 0.000% |" in markdown
    assert "| Winning games observed | No |" in markdown
    assert markdown.count("| Fastest win turn | N/A |") == 2
    assert "| Slowest win turn | N/A |" in markdown
    assert "| Average win turn | N/A |" in markdown
    assert "| Median win turn | N/A |" in markdown
    assert "| 90th percentile win turn | N/A |" in markdown
    assert "| 95th percentile win turn | N/A |" in markdown
    assert (
        "| Win-turn standard deviation | N/A |"
        in markdown
    )
    assert (
        "> No winning games were observed. "
        "Win-turn measurements are unavailable."
        in markdown
    )


def test_markdown_no_win_message_is_not_rendered_when_wins_exist() -> None:
    markdown = (
        ExperimentAnalysisMarkdownReporter()
        .analysis_to_markdown(create_analysis())
    )

    assert (
        "No winning games were observed."
        not in markdown
    )


def test_title_escapes_markdown_control_characters() -> None:
    markdown = ExperimentAnalysisMarkdownReporter(
        title="# KRS | *Analysis*",
    ).analysis_to_markdown(create_analysis())

    assert markdown.startswith(
        "# \\# KRS \\| \\*Analysis\\*"
    )


def test_render_table_escapes_pipe_characters() -> None:
    table = ExperimentAnalysisMarkdownReporter._render_table(
        (
            (
                "Metric | Name",
                "Value | Result",
            ),
        )
    )

    assert "| Metric \\| Name | Value \\| Result |" in table


def test_render_table_escapes_backslashes() -> None:
    table = ExperimentAnalysisMarkdownReporter._render_table(
        (
            (
                r"Metric\Name",
                r"Value\Result",
            ),
        )
    )

    assert (
        r"| Metric\\Name | Value\\Result |"
        in table
    )


def test_render_table_replaces_newlines() -> None:
    table = ExperimentAnalysisMarkdownReporter._render_table(
        (
            (
                "Metric\nName",
                "Value\r\nResult",
            ),
        )
    )

    assert "| Metric<br>Name | Value<br>Result |" in table


def test_escape_text_escapes_expected_characters() -> None:
    escaped = ExperimentAnalysisMarkdownReporter._escape_text(
        r"\`*_{}[]<>#+-!|"
    )

    assert escaped == (
        r"\\\`\*\_\{\}\[\]\<\>\#\+\-\!\|"
    )


def test_format_boolean_returns_human_readable_value() -> None:
    assert (
        ExperimentAnalysisMarkdownReporter
        ._format_boolean(True)
        == "Yes"
    )
    assert (
        ExperimentAnalysisMarkdownReporter
        ._format_boolean(False)
        == "No"
    )


def test_format_optional_integer() -> None:
    assert (
        ExperimentAnalysisMarkdownReporter
        ._format_optional_integer(3)
        == "3"
    )
    assert (
        ExperimentAnalysisMarkdownReporter
        ._format_optional_integer(None)
        == "N/A"
    )


def test_format_optional_float() -> None:
    assert (
        ExperimentAnalysisMarkdownReporter
        ._format_optional_float(3.14159)
        == "3.142"
    )
    assert (
        ExperimentAnalysisMarkdownReporter
        ._format_optional_float(None)
        == "N/A"
    )


def test_write_creates_markdown_file(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = ExperimentAnalysisMarkdownReporter()

    output_path = tmp_path / "analysis.md"

    returned_path = reporter.write(
        result,
        output_path,
    )

    assert returned_path == output_path
    assert output_path.is_file()

    content = output_path.read_text(
        encoding="utf-8",
    )

    assert content == reporter.to_markdown(result)


def test_write_creates_parent_directories(
    tmp_path: Path,
) -> None:
    output_path = (
        tmp_path
        / "reports"
        / "analysis"
        / "analysis.md"
    )

    ExperimentAnalysisMarkdownReporter().write(
        create_experiment_result(),
        output_path,
    )

    assert output_path.is_file()


@pytest.mark.parametrize(
    "filename",
    (
        "analysis.md",
        "analysis.markdown",
        "ANALYSIS.MD",
        "ANALYSIS.MARKDOWN",
    ),
)
def test_write_accepts_markdown_extensions(
    tmp_path: Path,
    filename: str,
) -> None:
    output_path = tmp_path / filename

    ExperimentAnalysisMarkdownReporter().write(
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
            "Analysis Markdown report path "
            "is a directory"
        ),
    ):
        ExperimentAnalysisMarkdownReporter().write(
            create_experiment_result(),
            tmp_path,
        )


@pytest.mark.parametrize(
    "filename",
    (
        "analysis.txt",
        "analysis.json",
        "analysis.html",
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
            "Analysis Markdown report path must use "
            "the .md or .markdown extension."
        ),
    ):
        ExperimentAnalysisMarkdownReporter().write(
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
        ExperimentAnalysisMarkdownReporter(
            title=title,
        )


def test_report_does_not_modify_experiment_result() -> None:
    result = create_experiment_result()

    original_config = result.config
    original_summary = result.summary
    original_results = result.game_results

    ExperimentAnalysisMarkdownReporter().to_markdown(
        result
    )

    assert result.config is original_config
    assert result.summary is original_summary
    assert result.game_results is original_results


def test_write_does_not_modify_experiment_result(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    original_config = result.config
    original_summary = result.summary
    original_results = result.game_results

    ExperimentAnalysisMarkdownReporter().write(
        result,
        tmp_path / "analysis.md",
    )

    assert result.config is original_config
    assert result.summary is original_summary
    assert result.game_results is original_results