from __future__ import annotations

from pathlib import Path

import pytest

from krs.report.html import HtmlExperimentReporter
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


def test_to_html_returns_complete_document() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    assert html.startswith("<!DOCTYPE html>")
    assert '<html lang="en">' in html
    assert '<meta charset="utf-8">' in html
    assert "</html>" in html


def test_to_html_contains_title() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter(
        title="KRS Monte Carlo Result",
    ).to_html(result)

    assert "<title>KRS Monte Carlo Result</title>" in html
    assert "<h1>KRS Monte Carlo Result</h1>" in html


def test_to_html_contains_summary_values() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    assert "66.67%" in html
    assert "Games completed" in html
    assert ">3<" in html
    assert "Average turns" in html
    assert "5.333" in html
    assert "Average Kinnan activations" in html
    assert "1.000" in html
    assert "Fastest win turn" in html


def test_to_html_contains_configuration_values() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    assert "Configuration" in html
    assert "combo" in html
    assert "12345" in html
    assert ">4<" in html
    assert "Mulligan enabled" in html
    assert "Save replays" in html


def test_to_html_contains_ordered_game_results() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    game_zero_position = html.index(
        'data-game-id="0"'
    )
    game_one_position = html.index(
        'data-game-id="1"'
    )
    game_two_position = html.index(
        'data-game-id="2"'
    )

    assert game_zero_position < game_one_position
    assert game_one_position < game_two_position
    assert "プレイヤー" in html


def test_to_html_marks_wins_and_non_wins() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    assert html.count('class="win"') == 2
    assert html.count('class="non-win"') == 1


def test_to_html_escapes_title() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter(
        title="<script>alert('x')</script>",
    ).to_html(result)

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_to_html_escapes_winner() -> None:
    config = SimulationConfig(
        games=1,
    )
    game_results = (
        create_game_result(
            turns_started=2,
            kinnan_activations=1,
            game_over=True,
            winner="<Admin>",
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

    html = HtmlExperimentReporter().to_html(result)

    assert "<Admin>" not in html
    assert "&lt;Admin&gt;" in html


def test_to_html_displays_none_seed() -> None:
    config = SimulationConfig(
        games=1,
        seed=None,
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
            games_requested=1,
            results=game_results,
        ),
    )

    html = HtmlExperimentReporter().to_html(result)

    assert "Seed" in html
    assert ">None<" in html


def test_to_html_displays_no_fastest_win_as_na() -> None:
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
            games_requested=1,
            results=game_results,
        ),
    )

    html = HtmlExperimentReporter().to_html(result)

    assert "Fastest win turn" in html
    assert ">N/A<" in html


def test_write_creates_html_file(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = HtmlExperimentReporter()

    output_path = tmp_path / "report.html"

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
    result = create_experiment_result()

    output_path = (
        tmp_path
        / "reports"
        / "html"
        / "result.html"
    )

    HtmlExperimentReporter().write(
        result,
        output_path,
    )

    assert output_path.is_file()


@pytest.mark.parametrize(
    "filename",
    (
        "report.html",
        "report.htm",
        "REPORT.HTML",
    ),
)
def test_write_accepts_html_extensions(
    tmp_path: Path,
    filename: str,
) -> None:
    result = create_experiment_result()
    output_path = tmp_path / filename

    HtmlExperimentReporter().write(
        result,
        output_path,
    )

    assert output_path.is_file()


def test_write_rejects_directory_path(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    with pytest.raises(
        ValueError,
        match="HTML report path is a directory",
    ):
        HtmlExperimentReporter().write(
            result,
            tmp_path,
        )


def test_write_rejects_invalid_extension(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    with pytest.raises(
        ValueError,
        match=(
            "HTML report path must use "
            "the .html or .htm extension."
        ),
    ):
        HtmlExperimentReporter().write(
            result,
            tmp_path / "report.txt",
        )


@pytest.mark.parametrize(
    "title",
    (
        "",
        " ",
        "\t",
    ),
)
def test_reporter_rejects_empty_title(
    title: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="title must not be empty.",
    ):
        HtmlExperimentReporter(
            title=title,
        )


def test_html_report_does_not_modify_experiment_result() -> None:
    result = create_experiment_result()
    original_config = result.config
    original_summary = result.summary
    original_game_results = result.game_results

    HtmlExperimentReporter().to_html(result)

    assert result.config is original_config
    assert result.summary is original_summary
    assert result.game_results is original_game_results