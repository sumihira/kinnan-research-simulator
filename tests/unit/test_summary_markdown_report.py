from __future__ import annotations

from pathlib import Path

import pytest

from krs.report.summary_markdown import (
    ExperimentSummaryMarkdownReporter,
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
        strategy_name="combo",
        games=3,
        max_turns=8,
        seed=12345,
        mulligan_enabled=False,
        save_replays=True,
        workers=4,
    )

    game_results = (
        create_game_result(
            turns_started=3,
            kinnan_activations=2,
            game_over=True,
            winner="Player",
        ),
        create_game_result(
            turns_started=5,
            kinnan_activations=1,
            game_over=True,
            winner="プレイヤー",
        ),
        create_game_result(
            turns_started=8,
            kinnan_activations=0,
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


def create_no_win_experiment_result() -> ExperimentResult:
    config = SimulationConfig(
        strategy_name="default",
        games=2,
        max_turns=6,
        seed=None,
        mulligan_enabled=True,
        save_replays=False,
        workers=1,
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

    summary = SimulationSummary.from_results(
        games_requested=config.games,
        results=game_results,
    )

    return ExperimentResult(
        config=config,
        game_results=game_results,
        summary=summary,
    )


def test_to_markdown_contains_default_title() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_experiment_result())
    )

    assert markdown.startswith(
        "# Goldfish Experiment Report"
    )
    assert markdown.endswith("\n")


def test_to_markdown_contains_custom_title() -> None:
    markdown = ExperimentSummaryMarkdownReporter(
        title="KRS Goldfish Result",
    ).to_markdown(create_experiment_result())

    assert markdown.startswith(
        "# KRS Goldfish Result"
    )


def test_to_markdown_contains_all_sections() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_experiment_result())
    )

    assert "## Simulation Configuration" in markdown
    assert "## Summary" in markdown
    assert "## Individual Games" in markdown


def test_to_markdown_uses_section_separators() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_experiment_result())
    )

    assert markdown.count("\n\n---\n\n") == 3


def test_configuration_contains_expected_values() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_experiment_result())
    )

    assert "| Strategy | combo |" in markdown
    assert "| Games requested | 3 |" in markdown
    assert "| Maximum turns | 8 |" in markdown
    assert "| Seed | 12345 |" in markdown
    assert "| Workers | 4 |" in markdown
    assert "| Mulligan enabled | No |" in markdown
    assert "| Save replays | Yes |" in markdown


def test_configuration_supports_none_seed() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_no_win_experiment_result())
    )

    assert "| Seed | None |" in markdown


def test_configuration_formats_boolean_values() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_no_win_experiment_result())
    )

    assert "| Mulligan enabled | Yes |" in markdown
    assert "| Save replays | No |" in markdown


def test_summary_contains_expected_values() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_experiment_result())
    )

    assert "| Games requested | 3 |" in markdown
    assert "| Games completed | 3 |" in markdown
    assert "| Wins | 2 |" in markdown
    assert "| Non-wins | 1 |" in markdown
    assert "| Win rate | 66.667% |" in markdown
    assert "| Turn-limit games | 1 |" in markdown
    assert "| Total turns started | 16 |" in markdown
    assert "| Average turns started | 5.333 |" in markdown
    assert "| Total Kinnan activations | 3 |" in markdown
    assert "| Average Kinnan activations | 1.000 |" in markdown
    assert "| Fastest win turn | 3 |" in markdown


def test_summary_supports_no_wins() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_no_win_experiment_result())
    )

    assert "| Wins | 0 |" in markdown
    assert "| Non-wins | 2 |" in markdown
    assert "| Win rate | 0.000% |" in markdown
    assert "| Fastest win turn | N/A |" in markdown


def test_markdown_contains_metric_tables() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_experiment_result())
    )

    assert markdown.count("| Metric | Value |") == 2
    assert markdown.count("|:--|--:|") == 2


def test_games_table_contains_expected_header() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_experiment_result())
    )

    assert (
        "| Game ID | Result | Turns started | "
        "Kinnan activations | Turn limit | Winner |"
        in markdown
    )
    assert "|--:|:--:|--:|--:|:--:|:--|" in markdown


def test_games_table_contains_first_game() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_experiment_result())
    )

    assert "| 0 | Win | 3 | 2 | No | Player |" in markdown


def test_games_table_contains_unicode_winner() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_experiment_result())
    )

    assert "| 1 | Win | 5 | 1 | No | プレイヤー |" in markdown


def test_games_table_contains_non_win() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_experiment_result())
    )

    assert "| 2 | Non-win | 8 | 0 | Yes |  |" in markdown


def test_games_table_preserves_game_order() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_experiment_result())
    )

    game_zero_position = markdown.index(
        "| 0 | Win |"
    )
    game_one_position = markdown.index(
        "| 1 | Win |"
    )
    game_two_position = markdown.index(
        "| 2 | Non-win |"
    )

    assert game_zero_position < game_one_position
    assert game_one_position < game_two_position


def test_game_over_without_winner_is_non_win() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_no_win_experiment_result())
    )

    assert "| 1 | Non-win | 6 | 1 | No |  |" in markdown


def test_render_game_row_escapes_winner_pipe() -> None:
    row = ExperimentSummaryMarkdownReporter._render_game_row(
        game_id=0,
        result=create_game_result(
            turns_started=3,
            kinnan_activations=1,
            game_over=True,
            winner="Player | One",
        ),
    )

    assert "Player \\| One" in row


def test_render_game_row_escapes_winner_backslash() -> None:
    row = ExperimentSummaryMarkdownReporter._render_game_row(
        game_id=0,
        result=create_game_result(
            turns_started=3,
            kinnan_activations=1,
            game_over=True,
            winner=r"Player\One",
        ),
    )

    assert r"Player\\One" in row


def test_render_game_row_replaces_winner_newline() -> None:
    row = ExperimentSummaryMarkdownReporter._render_game_row(
        game_id=0,
        result=create_game_result(
            turns_started=3,
            kinnan_activations=1,
            game_over=True,
            winner="Player\nOne",
        ),
    )

    assert "Player<br>One" in row


def test_render_metric_table_escapes_values() -> None:
    table = (
        ExperimentSummaryMarkdownReporter
        ._render_metric_table(
            (
                (
                    "Metric | Name",
                    r"Value\Result",
                ),
            )
        )
    )

    assert (
        r"| Metric \| Name | Value\\Result |"
        in table
    )


def test_escape_table_cell_replaces_line_endings() -> None:
    escaped = (
        ExperimentSummaryMarkdownReporter
        ._escape_table_cell(
            "First\r\nSecond\nThird\rFourth"
        )
    )

    assert escaped == (
        "First<br>Second<br>Third<br>Fourth"
    )


def test_title_escapes_markdown_control_characters() -> None:
    markdown = ExperimentSummaryMarkdownReporter(
        title="# Goldfish | *Report*",
    ).to_markdown(create_experiment_result())

    assert markdown.startswith(
        "# \\# Goldfish \\| \\*Report\\*"
    )


def test_escape_text_escapes_expected_characters() -> None:
    escaped = ExperimentSummaryMarkdownReporter._escape_text(
        r"\`*_{}[]<>#+-!|"
    )

    assert escaped == (
        r"\\\`\*\_\{\}\[\]\<\>\#\+\-\!\|"
    )


def test_format_boolean_returns_expected_values() -> None:
    assert (
        ExperimentSummaryMarkdownReporter
        ._format_boolean(True)
        == "Yes"
    )
    assert (
        ExperimentSummaryMarkdownReporter
        ._format_boolean(False)
        == "No"
    )


def test_render_games_displays_empty_message() -> None:
    config = SimulationConfig(
        games=1,
    )
    summary = SimulationSummary.from_results(
        games_requested=1,
        results=(),
    )
    result = ExperimentResult(
        config=config,
        game_results=(),
        summary=summary,
    )

    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(result)
    )

    assert (
        "> No individual game results are available."
        in markdown
    )
    assert (
        "| Game ID | Result | Turns started |"
        not in markdown
    )


def test_write_creates_markdown_file(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = ExperimentSummaryMarkdownReporter()

    output_path = tmp_path / "summary.md"

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
        / "markdown"
        / "summary.md"
    )

    ExperimentSummaryMarkdownReporter().write(
        create_experiment_result(),
        output_path,
    )

    assert output_path.is_file()


@pytest.mark.parametrize(
    "filename",
    (
        "summary.md",
        "summary.markdown",
        "SUMMARY.MD",
        "SUMMARY.MARKDOWN",
    ),
)
def test_write_accepts_markdown_extensions(
    tmp_path: Path,
    filename: str,
) -> None:
    output_path = tmp_path / filename

    ExperimentSummaryMarkdownReporter().write(
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
            "Summary Markdown report path "
            "is a directory"
        ),
    ):
        ExperimentSummaryMarkdownReporter().write(
            create_experiment_result(),
            tmp_path,
        )


@pytest.mark.parametrize(
    "filename",
    (
        "summary.txt",
        "summary.json",
        "summary.html",
        "summary",
    ),
)
def test_write_rejects_invalid_extension(
    tmp_path: Path,
    filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Summary Markdown report path must use "
            "the .md or .markdown extension."
        ),
    ):
        ExperimentSummaryMarkdownReporter().write(
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
        ExperimentSummaryMarkdownReporter(
            title=title,
        )


def test_to_markdown_does_not_modify_experiment_result() -> None:
    result = create_experiment_result()

    original_config = result.config
    original_summary = result.summary
    original_game_results = result.game_results

    ExperimentSummaryMarkdownReporter().to_markdown(
        result
    )

    assert result.config is original_config
    assert result.summary is original_summary
    assert result.game_results is original_game_results


def test_write_does_not_modify_experiment_result(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    original_config = result.config
    original_summary = result.summary
    original_game_results = result.game_results

    ExperimentSummaryMarkdownReporter().write(
        result,
        tmp_path / "summary.md",
    )

    assert result.config is original_config
    assert result.summary is original_summary
    assert result.game_results is original_game_results