from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from krs.report.graph import (
    DistributionData,
    DistributionPoint,
    ExperimentGraphData,
    GraphDataReporter,
)
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
        games=5,
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
            turns_started=3,
            kinnan_activations=1,
            game_over=True,
            winner="プレイヤー",
        ),
        create_game_result(
            turns_started=5,
            kinnan_activations=2,
            game_over=True,
            winner="Player",
        ),
        create_game_result(
            turns_started=8,
            kinnan_activations=0,
            reached_turn_limit=True,
        ),
        create_game_result(
            turns_started=8,
            kinnan_activations=0,
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


def create_no_win_experiment_result() -> ExperimentResult:
    config = SimulationConfig(
        games=2,
        max_turns=6,
        seed=None,
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


def create_graph_data() -> ExperimentGraphData:
    return ExperimentGraphData(
        win_turn_distribution=DistributionData(
            name="win_turn",
            points=(
                DistributionPoint(
                    value=3,
                    count=2,
                    percentage=2 / 3,
                ),
                DistributionPoint(
                    value=5,
                    count=1,
                    percentage=1 / 3,
                ),
            ),
            total_observations=3,
        ),
        kinnan_activation_distribution=DistributionData(
            name="kinnan_activations",
            points=(
                DistributionPoint(
                    value=0,
                    count=2,
                    percentage=0.4,
                ),
                DistributionPoint(
                    value=1,
                    count=1,
                    percentage=0.2,
                ),
                DistributionPoint(
                    value=2,
                    count=2,
                    percentage=0.4,
                ),
            ),
            total_observations=5,
        ),
    )


def test_to_html_returns_complete_document() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    assert html.startswith("<!DOCTYPE html>")
    assert '<html lang="en">' in html
    assert '<meta charset="utf-8">' in html
    assert "</body>" in html
    assert "</html>" in html


def test_to_html_contains_default_title() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    assert (
        "<title>Kinnan Research Simulator Report</title>"
        in html
    )
    assert (
        "<h1>Kinnan Research Simulator Report</h1>"
        in html
    )


def test_to_html_contains_custom_title() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter(
        title="KRS Monte Carlo Result",
    ).to_html(result)

    assert "<title>KRS Monte Carlo Result</title>" in html
    assert "<h1>KRS Monte Carlo Result</h1>" in html


def test_to_html_contains_summary_values() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    assert "60.00%" in html
    assert "5 games completed" in html
    assert "Games completed" in html
    assert "Wins" in html
    assert "Non-wins" in html
    assert "Turn-limit games" in html
    assert "Average turns" in html
    assert "5.400" in html
    assert "Average Kinnan activations" in html
    assert "1.000" in html
    assert "Fastest win turn" in html


def test_to_html_contains_configuration_values() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    assert "Configuration" in html
    assert "combo" in html
    assert "12345" in html
    assert "Workers" in html
    assert ">4<" in html
    assert "Mulligan enabled" in html
    assert "Save replays" in html


def test_to_html_contains_distribution_section() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    assert "Distributions" in html
    assert "Win Turn Distribution" in html
    assert "Kinnan Activation Distribution" in html


def test_to_html_uses_graph_data_reporter() -> None:
    result = create_experiment_result()
    graph_data = create_graph_data()

    graph_reporter = Mock(
        spec=GraphDataReporter,
    )
    graph_reporter.build.return_value = graph_data

    reporter = HtmlExperimentReporter(
        graph_data_reporter=graph_reporter,
    )

    html = reporter.to_html(result)

    graph_reporter.build.assert_called_once_with(result)
    assert "Win Turn Distribution" in html
    assert "Kinnan Activation Distribution" in html


def test_to_html_calls_graph_reporter_once() -> None:
    result = create_experiment_result()

    graph_reporter = Mock(
        spec=GraphDataReporter,
    )
    graph_reporter.build.return_value = create_graph_data()

    reporter = HtmlExperimentReporter(
        graph_data_reporter=graph_reporter,
    )

    reporter.to_html(result)

    assert graph_reporter.build.call_count == 1


def test_win_turn_distribution_contains_expected_values() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    assert 'data-distribution="win_turn"' in html
    assert 'data-value="3"' in html
    assert 'data-value="5"' in html
    assert "Turn 3" in html
    assert "Turn 5" in html
    assert "2 (66.7%)" in html
    assert "1 (33.3%)" in html
    assert "3 observations" in html


def test_kinnan_distribution_contains_expected_values() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    assert (
        'data-distribution="kinnan_activations"'
        in html
    )
    assert "Activations 0" in html
    assert "Activations 1" in html
    assert "Activations 2" in html
    assert "2 (40.0%)" in html
    assert "1 (20.0%)" in html
    assert "5 observations" in html


def test_win_turn_distribution_preserves_value_order() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    distribution_start = html.index(
        'data-distribution="win_turn"'
    )
    kinnan_distribution_start = html.index(
        'data-distribution="kinnan_activations"'
    )

    win_distribution_html = html[
        distribution_start:kinnan_distribution_start
    ]

    turn_three_position = win_distribution_html.index(
        'data-value="3"'
    )
    turn_five_position = win_distribution_html.index(
        'data-value="5"'
    )

    assert turn_three_position < turn_five_position


def test_kinnan_distribution_preserves_value_order() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    distribution_start = html.index(
        'data-distribution="kinnan_activations"'
    )

    distribution_html = html[distribution_start:]

    zero_position = distribution_html.index(
        'data-value="0"'
    )
    one_position = distribution_html.index(
        'data-value="1"'
    )
    two_position = distribution_html.index(
        'data-value="2"'
    )

    assert zero_position < one_position
    assert one_position < two_position


def test_distribution_bar_contains_expected_widths() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    assert 'style="width: 66.666667%"' in html
    assert 'style="width: 33.333333%"' in html
    assert html.count(
        'style="width: 40.000000%"'
    ) == 2
    assert 'style="width: 20.000000%"' in html


def test_distribution_uses_css_bar_classes() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    assert 'class="distribution-card"' in html
    assert 'class="distribution-chart"' in html
    assert 'class="distribution-row"' in html
    assert 'class="distribution-track"' in html
    assert 'class="distribution-bar"' in html
    assert ".distribution-bar {" in html


def test_empty_win_distribution_is_rendered() -> None:
    result = create_no_win_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    win_distribution_start = html.index(
        'data-distribution="win_turn"'
    )
    kinnan_distribution_start = html.index(
        'data-distribution="kinnan_activations"'
    )

    win_distribution_html = html[
        win_distribution_start:kinnan_distribution_start
    ]

    assert "Win Turn Distribution" in win_distribution_html
    assert "0 observations" in win_distribution_html
    assert (
        "No observations available."
        in win_distribution_html
    )
    assert 'class="empty-distribution"' in win_distribution_html


def test_empty_win_distribution_does_not_hide_kinnan_data() -> None:
    result = create_no_win_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    assert "Kinnan Activation Distribution" in html
    assert "Activations 0" in html
    assert "Activations 1" in html
    assert "2 observations" in html


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
    game_three_position = html.index(
        'data-game-id="3"'
    )
    game_four_position = html.index(
        'data-game-id="4"'
    )

    assert game_zero_position < game_one_position
    assert game_one_position < game_two_position
    assert game_two_position < game_three_position
    assert game_three_position < game_four_position
    assert "プレイヤー" in html


def test_to_html_marks_wins_and_non_wins() -> None:
    result = create_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    assert html.count('class="win"') == 3
    assert html.count('class="non-win"') == 2


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
    result = create_no_win_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    assert "Seed" in html
    assert ">None<" in html


def test_to_html_displays_no_fastest_win_as_na() -> None:
    result = create_no_win_experiment_result()

    html = HtmlExperimentReporter().to_html(result)

    assert "Fastest win turn" in html
    assert ">N/A<" in html


def test_distribution_id_normalizes_name() -> None:
    assert (
        HtmlExperimentReporter._distribution_id(
            "Kinnan Activations"
        )
        == "kinnan-activations"
    )

    assert (
        HtmlExperimentReporter._distribution_id(
            "  Win_Turn  "
        )
        == "win-turn"
    )


def test_distribution_id_supports_empty_normalized_name() -> None:
    assert (
        HtmlExperimentReporter._distribution_id(
            "---"
        )
        == "distribution"
    )


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
    assert "Win Turn Distribution" in content
    assert "Kinnan Activation Distribution" in content


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
        "REPORT.HTM",
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


@pytest.mark.parametrize(
    "filename",
    (
        "report.txt",
        "report.json",
        "report",
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
            "HTML report path must use "
            "the .html or .htm extension."
        ),
    ):
        HtmlExperimentReporter().write(
            result,
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


def test_write_does_not_modify_experiment_result(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    original_config = result.config
    original_summary = result.summary
    original_game_results = result.game_results

    HtmlExperimentReporter().write(
        result,
        tmp_path / "report.html",
    )

    assert result.config is original_config
    assert result.summary is original_summary
    assert result.game_results is original_game_results