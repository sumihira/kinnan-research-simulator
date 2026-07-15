from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from krs.report.analysis import ExperimentAnalysisReporter
from krs.report.analysis_html import (
    ExperimentAnalysisHtmlReporter,
)
from krs.report.analysis_markdown import (
    ExperimentAnalysisMarkdownReporter,
)
from krs.report.bundle import (
    ExperimentReportBundlePaths,
    ExperimentReportBundleWriter,
)
from krs.report.csv import (
    CsvExperimentReporter,
    CsvReportPaths,
)
from krs.report.excel import ExcelExperimentReporter
from krs.report.html import HtmlExperimentReporter
from krs.report.json import JsonExperimentReporter
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
        games=2,
        max_turns=8,
        seed=12345,
        mulligan_enabled=False,
        save_replays=True,
        workers=2,
    )

    game_results = (
        create_game_result(
            turns_started=3,
            kinnan_activations=2,
            game_over=True,
            winner="Player",
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


def create_bundle_paths(
    output_directory: Path,
) -> ExperimentReportBundlePaths:
    return ExperimentReportBundlePaths(
        output_directory=output_directory,
        json_path=(
            output_directory
            / "experiment.json"
        ),
        analysis_json_path=(
            output_directory
            / "analysis.json"
        ),
        html_path=(
            output_directory
            / "experiment.html"
        ),
        analysis_html_path=(
            output_directory
            / "analysis.html"
        ),
        excel_path=(
            output_directory
            / "experiment.xlsx"
        ),
        summary_markdown_path=(
            output_directory
            / "summary.md"
        ),
        analysis_markdown_path=(
            output_directory
            / "analysis.md"
        ),
        csv_summary_path=(
            output_directory
            / "csv"
            / "summary.csv"
        ),
        csv_games_path=(
            output_directory
            / "csv"
            / "games.csv"
        ),
    )


def test_write_creates_all_report_files(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    paths = ExperimentReportBundleWriter().write(
        result,
        tmp_path,
    )

    assert paths == create_bundle_paths(tmp_path)

    assert paths.output_directory == tmp_path
    assert paths.json_path.is_file()
    assert paths.analysis_json_path.is_file()
    assert paths.html_path.is_file()
    assert paths.analysis_html_path.is_file()
    assert paths.excel_path.is_file()
    assert paths.summary_markdown_path.is_file()
    assert paths.analysis_markdown_path.is_file()
    assert paths.csv_summary_path.is_file()
    assert paths.csv_games_path.is_file()


def test_write_creates_expected_directory_structure(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    output_directory = (
        tmp_path
        / "reports"
        / "experiment-001"
    )

    paths = ExperimentReportBundleWriter().write(
        result,
        output_directory,
    )

    assert output_directory.is_dir()
    assert (
        output_directory
        / "csv"
    ).is_dir()

    assert paths.json_path == (
        output_directory
        / "experiment.json"
    )
    assert paths.analysis_json_path == (
        output_directory
        / "analysis.json"
    )
    assert paths.html_path == (
        output_directory
        / "experiment.html"
    )
    assert paths.analysis_html_path == (
        output_directory
        / "analysis.html"
    )
    assert paths.excel_path == (
        output_directory
        / "experiment.xlsx"
    )
    assert paths.summary_markdown_path == (
        output_directory
        / "summary.md"
    )
    assert paths.analysis_markdown_path == (
        output_directory
        / "analysis.md"
    )
    assert paths.csv_summary_path == (
        output_directory
        / "csv"
        / "summary.csv"
    )
    assert paths.csv_games_path == (
        output_directory
        / "csv"
        / "games.csv"
    )


def test_write_supports_existing_output_directory(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    output_directory = tmp_path / "existing"
    output_directory.mkdir()

    marker_path = output_directory / "marker.txt"
    marker_path.write_text(
        "keep",
        encoding="utf-8",
    )

    paths = ExperimentReportBundleWriter().write(
        result,
        output_directory,
    )

    assert marker_path.read_text(
        encoding="utf-8",
    ) == "keep"

    assert paths.output_directory == output_directory
    assert len(paths.all_paths) == 9


def test_write_uses_custom_output_names(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    writer = ExperimentReportBundleWriter(
        json_filename="result.json",
        analysis_json_filename="statistics.json",
        html_filename="result.htm",
        analysis_html_filename="statistics.htm",
        excel_filename="result.xlsx",
        summary_markdown_filename="summary.markdown",
        analysis_markdown_filename="statistics.md",
        csv_directory_name="tables",
    )

    paths = writer.write(
        result,
        tmp_path,
    )

    assert paths.json_path == (
        tmp_path
        / "result.json"
    )
    assert paths.analysis_json_path == (
        tmp_path
        / "statistics.json"
    )
    assert paths.html_path == (
        tmp_path
        / "result.htm"
    )
    assert paths.analysis_html_path == (
        tmp_path
        / "statistics.htm"
    )
    assert paths.excel_path == (
        tmp_path
        / "result.xlsx"
    )
    assert paths.summary_markdown_path == (
        tmp_path
        / "summary.markdown"
    )
    assert paths.analysis_markdown_path == (
        tmp_path
        / "statistics.md"
    )
    assert paths.csv_summary_path == (
        tmp_path
        / "tables"
        / "summary.csv"
    )
    assert paths.csv_games_path == (
        tmp_path
        / "tables"
        / "games.csv"
    )


def test_write_delegates_to_all_reporters(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    json_reporter = Mock(
        spec=JsonExperimentReporter,
    )
    analysis_json_reporter = Mock(
        spec=ExperimentAnalysisReporter,
    )
    html_reporter = Mock(
        spec=HtmlExperimentReporter,
    )
    analysis_html_reporter = Mock(
        spec=ExperimentAnalysisHtmlReporter,
    )
    excel_reporter = Mock(
        spec=ExcelExperimentReporter,
    )
    summary_markdown_reporter = Mock(
        spec=ExperimentSummaryMarkdownReporter,
    )
    analysis_markdown_reporter = Mock(
        spec=ExperimentAnalysisMarkdownReporter,
    )
    csv_reporter = Mock(
        spec=CsvExperimentReporter,
    )

    json_path = tmp_path / "experiment.json"
    analysis_json_path = tmp_path / "analysis.json"
    html_path = tmp_path / "experiment.html"
    analysis_html_path = tmp_path / "analysis.html"
    excel_path = tmp_path / "experiment.xlsx"
    summary_markdown_path = tmp_path / "summary.md"
    analysis_markdown_path = tmp_path / "analysis.md"
    csv_directory = tmp_path / "csv"

    json_reporter.write.return_value = json_path
    analysis_json_reporter.write.return_value = (
        analysis_json_path
    )
    html_reporter.write.return_value = html_path
    analysis_html_reporter.write.return_value = (
        analysis_html_path
    )
    excel_reporter.write.return_value = excel_path
    summary_markdown_reporter.write.return_value = (
        summary_markdown_path
    )
    analysis_markdown_reporter.write.return_value = (
        analysis_markdown_path
    )
    csv_reporter.write.return_value = CsvReportPaths(
        summary_path=csv_directory / "summary.csv",
        games_path=csv_directory / "games.csv",
    )

    writer = ExperimentReportBundleWriter(
        json_reporter=json_reporter,
        analysis_json_reporter=analysis_json_reporter,
        html_reporter=html_reporter,
        analysis_html_reporter=analysis_html_reporter,
        excel_reporter=excel_reporter,
        summary_markdown_reporter=(
            summary_markdown_reporter
        ),
        analysis_markdown_reporter=(
            analysis_markdown_reporter
        ),
        csv_reporter=csv_reporter,
    )

    paths = writer.write(
        result,
        tmp_path,
    )

    json_reporter.write.assert_called_once_with(
        result,
        json_path,
    )
    analysis_json_reporter.write.assert_called_once_with(
        result,
        analysis_json_path,
    )
    html_reporter.write.assert_called_once_with(
        result,
        html_path,
    )
    analysis_html_reporter.write.assert_called_once_with(
        result,
        analysis_html_path,
    )
    excel_reporter.write.assert_called_once_with(
        result,
        excel_path,
    )
    summary_markdown_reporter.write.assert_called_once_with(
        result,
        summary_markdown_path,
    )
    analysis_markdown_reporter.write.assert_called_once_with(
        result,
        analysis_markdown_path,
    )
    csv_reporter.write.assert_called_once_with(
        result,
        csv_directory,
    )

    assert paths == create_bundle_paths(tmp_path)


def test_reporters_are_called_in_stable_order(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    calls: list[str] = []

    json_reporter = Mock(
        spec=JsonExperimentReporter,
    )
    analysis_json_reporter = Mock(
        spec=ExperimentAnalysisReporter,
    )
    html_reporter = Mock(
        spec=HtmlExperimentReporter,
    )
    analysis_html_reporter = Mock(
        spec=ExperimentAnalysisHtmlReporter,
    )
    excel_reporter = Mock(
        spec=ExcelExperimentReporter,
    )
    summary_markdown_reporter = Mock(
        spec=ExperimentSummaryMarkdownReporter,
    )
    analysis_markdown_reporter = Mock(
        spec=ExperimentAnalysisMarkdownReporter,
    )
    csv_reporter = Mock(
        spec=CsvExperimentReporter,
    )

    def write_json(
        current_result: ExperimentResult,
        path: Path,
    ) -> Path:
        assert current_result is result
        calls.append("json")
        return path

    def write_analysis_json(
        current_result: ExperimentResult,
        path: Path,
    ) -> Path:
        assert current_result is result
        calls.append("analysis_json")
        return path

    def write_html(
        current_result: ExperimentResult,
        path: Path,
    ) -> Path:
        assert current_result is result
        calls.append("html")
        return path

    def write_analysis_html(
        current_result: ExperimentResult,
        path: Path,
    ) -> Path:
        assert current_result is result
        calls.append("analysis_html")
        return path

    def write_excel(
        current_result: ExperimentResult,
        path: Path,
    ) -> Path:
        assert current_result is result
        calls.append("excel")
        return path

    def write_summary_markdown(
        current_result: ExperimentResult,
        path: Path,
    ) -> Path:
        assert current_result is result
        calls.append("summary_markdown")
        return path

    def write_analysis_markdown(
        current_result: ExperimentResult,
        path: Path,
    ) -> Path:
        assert current_result is result
        calls.append("analysis_markdown")
        return path

    def write_csv(
        current_result: ExperimentResult,
        directory: Path,
    ) -> CsvReportPaths:
        assert current_result is result
        calls.append("csv")

        return CsvReportPaths(
            summary_path=directory / "summary.csv",
            games_path=directory / "games.csv",
        )

    json_reporter.write.side_effect = write_json
    analysis_json_reporter.write.side_effect = (
        write_analysis_json
    )
    html_reporter.write.side_effect = write_html
    analysis_html_reporter.write.side_effect = (
        write_analysis_html
    )
    excel_reporter.write.side_effect = write_excel
    summary_markdown_reporter.write.side_effect = (
        write_summary_markdown
    )
    analysis_markdown_reporter.write.side_effect = (
        write_analysis_markdown
    )
    csv_reporter.write.side_effect = write_csv

    writer = ExperimentReportBundleWriter(
        json_reporter=json_reporter,
        analysis_json_reporter=analysis_json_reporter,
        html_reporter=html_reporter,
        analysis_html_reporter=analysis_html_reporter,
        excel_reporter=excel_reporter,
        summary_markdown_reporter=(
            summary_markdown_reporter
        ),
        analysis_markdown_reporter=(
            analysis_markdown_reporter
        ),
        csv_reporter=csv_reporter,
    )

    writer.write(
        result,
        tmp_path,
    )

    assert calls == [
        "json",
        "analysis_json",
        "html",
        "analysis_html",
        "excel",
        "summary_markdown",
        "analysis_markdown",
        "csv",
    ]


@pytest.mark.parametrize(
    (
        "reporter_field",
        "error_message",
    ),
    (
        (
            "json_reporter",
            "JSON output failed.",
        ),
        (
            "analysis_json_reporter",
            "Analysis JSON output failed.",
        ),
        (
            "html_reporter",
            "HTML output failed.",
        ),
        (
            "analysis_html_reporter",
            "Analysis HTML output failed.",
        ),
        (
            "excel_reporter",
            "Excel output failed.",
        ),
        (
            "summary_markdown_reporter",
            "Summary Markdown output failed.",
        ),
        (
            "analysis_markdown_reporter",
            "Analysis Markdown output failed.",
        ),
        (
            "csv_reporter",
            "CSV output failed.",
        ),
    ),
)
def test_write_propagates_reporter_exception(
    tmp_path: Path,
    reporter_field: str,
    error_message: str,
) -> None:
    result = create_experiment_result()

    reporters: dict[str, Mock] = {
        "json_reporter": Mock(
            spec=JsonExperimentReporter,
        ),
        "analysis_json_reporter": Mock(
            spec=ExperimentAnalysisReporter,
        ),
        "html_reporter": Mock(
            spec=HtmlExperimentReporter,
        ),
        "analysis_html_reporter": Mock(
            spec=ExperimentAnalysisHtmlReporter,
        ),
        "excel_reporter": Mock(
            spec=ExcelExperimentReporter,
        ),
        "summary_markdown_reporter": Mock(
            spec=ExperimentSummaryMarkdownReporter,
        ),
        "analysis_markdown_reporter": Mock(
            spec=ExperimentAnalysisMarkdownReporter,
        ),
        "csv_reporter": Mock(
            spec=CsvExperimentReporter,
        ),
    }

    reporters["json_reporter"].write.side_effect = (
        lambda current_result, path: path
    )
    reporters[
        "analysis_json_reporter"
    ].write.side_effect = (
        lambda current_result, path: path
    )
    reporters["html_reporter"].write.side_effect = (
        lambda current_result, path: path
    )
    reporters[
        "analysis_html_reporter"
    ].write.side_effect = (
        lambda current_result, path: path
    )
    reporters["excel_reporter"].write.side_effect = (
        lambda current_result, path: path
    )
    reporters[
        "summary_markdown_reporter"
    ].write.side_effect = (
        lambda current_result, path: path
    )
    reporters[
        "analysis_markdown_reporter"
    ].write.side_effect = (
        lambda current_result, path: path
    )
    reporters["csv_reporter"].write.side_effect = (
        lambda current_result, directory: CsvReportPaths(
            summary_path=directory / "summary.csv",
            games_path=directory / "games.csv",
        )
    )

    reporters[
        reporter_field
    ].write.side_effect = RuntimeError(
        error_message
    )

    writer = ExperimentReportBundleWriter(
        json_reporter=reporters["json_reporter"],
        analysis_json_reporter=reporters[
            "analysis_json_reporter"
        ],
        html_reporter=reporters["html_reporter"],
        analysis_html_reporter=reporters[
            "analysis_html_reporter"
        ],
        excel_reporter=reporters["excel_reporter"],
        summary_markdown_reporter=reporters[
            "summary_markdown_reporter"
        ],
        analysis_markdown_reporter=reporters[
            "analysis_markdown_reporter"
        ],
        csv_reporter=reporters["csv_reporter"],
    )

    with pytest.raises(
        RuntimeError,
        match=error_message,
    ):
        writer.write(
            result,
            tmp_path,
        )


def test_write_rejects_file_as_output_directory(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    output_file = tmp_path / "existing.txt"
    output_file.write_text(
        "content",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Report bundle output path is not "
            "a directory"
        ),
    ):
        ExperimentReportBundleWriter().write(
            result,
            output_file,
        )


def test_bundle_paths_all_paths_are_stable() -> None:
    output_directory = Path("reports")
    paths = create_bundle_paths(output_directory)

    assert paths.all_paths == (
        output_directory / "experiment.json",
        output_directory / "analysis.json",
        output_directory / "experiment.html",
        output_directory / "analysis.html",
        output_directory / "experiment.xlsx",
        output_directory / "summary.md",
        output_directory / "analysis.md",
        output_directory / "csv" / "summary.csv",
        output_directory / "csv" / "games.csv",
    )


def test_bundle_paths_return_format_groups() -> None:
    output_directory = Path("reports")
    paths = create_bundle_paths(output_directory)

    assert paths.json_paths == (
        output_directory / "experiment.json",
        output_directory / "analysis.json",
    )
    assert paths.html_paths == (
        output_directory / "experiment.html",
        output_directory / "analysis.html",
    )
    assert paths.markdown_paths == (
        output_directory / "summary.md",
        output_directory / "analysis.md",
    )
    assert paths.csv_paths == (
        output_directory / "csv" / "summary.csv",
        output_directory / "csv" / "games.csv",
    )


def test_bundle_paths_reject_duplicate_paths(
    tmp_path: Path,
) -> None:
    duplicate_path = tmp_path / "result.json"

    with pytest.raises(
        ValueError,
        match="Report bundle paths must be unique.",
    ):
        ExperimentReportBundlePaths(
            output_directory=tmp_path,
            json_path=duplicate_path,
            analysis_json_path=duplicate_path,
            html_path=tmp_path / "experiment.html",
            analysis_html_path=tmp_path / "analysis.html",
            excel_path=tmp_path / "experiment.xlsx",
            summary_markdown_path=tmp_path / "summary.md",
            analysis_markdown_path=tmp_path / "analysis.md",
            csv_summary_path=(
                tmp_path
                / "csv"
                / "summary.csv"
            ),
            csv_games_path=(
                tmp_path
                / "csv"
                / "games.csv"
            ),
        )


def test_bundle_paths_reject_output_directory_as_file_path(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Generated report path must not equal "
            "output_directory."
        ),
    ):
        ExperimentReportBundlePaths(
            output_directory=tmp_path,
            json_path=tmp_path,
            analysis_json_path=tmp_path / "analysis.json",
            html_path=tmp_path / "experiment.html",
            analysis_html_path=tmp_path / "analysis.html",
            excel_path=tmp_path / "experiment.xlsx",
            summary_markdown_path=tmp_path / "summary.md",
            analysis_markdown_path=tmp_path / "analysis.md",
            csv_summary_path=(
                tmp_path
                / "csv"
                / "summary.csv"
            ),
            csv_games_path=(
                tmp_path
                / "csv"
                / "games.csv"
            ),
        )


def test_bundle_paths_reject_path_outside_output_directory(
    tmp_path: Path,
) -> None:
    output_directory = tmp_path / "reports"

    with pytest.raises(
        ValueError,
        match=(
            "Generated report paths must be inside "
            "output_directory."
        ),
    ):
        ExperimentReportBundlePaths(
            output_directory=output_directory,
            json_path=tmp_path / "outside.json",
            analysis_json_path=(
                output_directory
                / "analysis.json"
            ),
            html_path=(
                output_directory
                / "experiment.html"
            ),
            analysis_html_path=(
                output_directory
                / "analysis.html"
            ),
            excel_path=(
                output_directory
                / "experiment.xlsx"
            ),
            summary_markdown_path=(
                output_directory
                / "summary.md"
            ),
            analysis_markdown_path=(
                output_directory
                / "analysis.md"
            ),
            csv_summary_path=(
                output_directory
                / "csv"
                / "summary.csv"
            ),
            csv_games_path=(
                output_directory
                / "csv"
                / "games.csv"
            ),
        )


def test_bundle_paths_are_immutable(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)

    with pytest.raises(AttributeError):
        paths.json_path = (  # type: ignore[misc]
            tmp_path
            / "changed.json"
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "overrides",
    ),
    (
        (
            "json_filename",
            {
                "json_filename": "",
            },
        ),
        (
            "analysis_json_filename",
            {
                "analysis_json_filename": " ",
            },
        ),
        (
            "html_filename",
            {
                "html_filename": "\t",
            },
        ),
        (
            "analysis_html_filename",
            {
                "analysis_html_filename": "\n",
            },
        ),
        (
            "excel_filename",
            {
                "excel_filename": "",
            },
        ),
        (
            "summary_markdown_filename",
            {
                "summary_markdown_filename": " ",
            },
        ),
        (
            "analysis_markdown_filename",
            {
                "analysis_markdown_filename": "\t",
            },
        ),
    ),
)
def test_writer_rejects_empty_filenames(
    field_name: str,
    overrides: dict[str, str],
) -> None:
    with pytest.raises(
        ValueError,
        match=rf"{field_name} must not be empty.",
    ):
        ExperimentReportBundleWriter(
            **overrides,
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "overrides",
    ),
    (
        (
            "json_filename",
            {
                "json_filename": "reports/result.json",
            },
        ),
        (
            "analysis_json_filename",
            {
                "analysis_json_filename": (
                    "reports/analysis.json"
                ),
            },
        ),
        (
            "html_filename",
            {
                "html_filename": "reports/result.html",
            },
        ),
        (
            "analysis_html_filename",
            {
                "analysis_html_filename": (
                    "reports/analysis.html"
                ),
            },
        ),
        (
            "excel_filename",
            {
                "excel_filename": "reports/result.xlsx",
            },
        ),
        (
            "summary_markdown_filename",
            {
                "summary_markdown_filename": (
                    "reports/summary.md"
                ),
            },
        ),
        (
            "analysis_markdown_filename",
            {
                "analysis_markdown_filename": (
                    "reports/analysis.md"
                ),
            },
        ),
    ),
)
def test_writer_rejects_directories_in_filenames(
    field_name: str,
    overrides: dict[str, str],
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            rf"{field_name} must not contain "
            r"a directory."
        ),
    ):
        ExperimentReportBundleWriter(
            **overrides,
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "overrides",
    ),
    (
        (
            "json_filename",
            {
                "json_filename": "result.txt",
            },
        ),
        (
            "analysis_json_filename",
            {
                "analysis_json_filename": "analysis.txt",
            },
        ),
        (
            "html_filename",
            {
                "html_filename": "result.txt",
            },
        ),
        (
            "analysis_html_filename",
            {
                "analysis_html_filename": "analysis.txt",
            },
        ),
        (
            "excel_filename",
            {
                "excel_filename": "result.xls",
            },
        ),
        (
            "summary_markdown_filename",
            {
                "summary_markdown_filename": "summary.txt",
            },
        ),
        (
            "analysis_markdown_filename",
            {
                "analysis_markdown_filename": "analysis.txt",
            },
        ),
    ),
)
def test_writer_rejects_invalid_extensions(
    field_name: str,
    overrides: dict[str, str],
) -> None:
    with pytest.raises(
        ValueError,
        match=rf"{field_name} must use the",
    ):
        ExperimentReportBundleWriter(
            **overrides,
        )


@pytest.mark.parametrize(
    "csv_directory_name",
    (
        "",
        " ",
        "\t",
    ),
)
def test_writer_rejects_empty_csv_directory(
    csv_directory_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="csv_directory_name must not be empty.",
    ):
        ExperimentReportBundleWriter(
            csv_directory_name=csv_directory_name,
        )


@pytest.mark.parametrize(
    "csv_directory_name",
    (
        "reports/csv",
        "tables/csv",
    ),
)
def test_writer_rejects_nested_csv_directory(
    csv_directory_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "csv_directory_name must not contain "
            "a directory."
        ),
    ):
        ExperimentReportBundleWriter(
            csv_directory_name=csv_directory_name,
        )


@pytest.mark.parametrize(
    (
        "csv_directory_name",
        "expected_message",
    ),
    (
        (
            ".",
            (
                "csv_directory_name must not contain "
                "a directory."
            ),
        ),
        (
            "..",
            (
                "csv_directory_name must be a valid "
                "directory name."
            ),
        ),
    ),
)
def test_writer_rejects_invalid_csv_directory_name(
    csv_directory_name: str,
    expected_message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        ExperimentReportBundleWriter(
            csv_directory_name=csv_directory_name,
        )


def test_writer_rejects_duplicate_root_filenames() -> None:
    with pytest.raises(
        ValueError,
        match="Root report filenames must be unique.",
    ):
        ExperimentReportBundleWriter(
            json_filename="result.json",
            analysis_json_filename="RESULT.JSON",
        )


def test_writer_rejects_csv_directory_matching_root_filename() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "csv_directory_name must not match "
            "a root report filename."
        ),
    ):
        ExperimentReportBundleWriter(
            json_filename="csv.json",
            csv_directory_name="CSV.JSON",
        )


def test_write_does_not_modify_experiment_result(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    original_config = result.config
    original_summary = result.summary
    original_results = result.game_results

    ExperimentReportBundleWriter().write(
        result,
        tmp_path,
    )

    assert result.config is original_config
    assert result.summary is original_summary
    assert result.game_results is original_results