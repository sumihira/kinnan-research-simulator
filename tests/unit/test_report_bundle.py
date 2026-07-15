from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from krs.report.analysis import ExperimentAnalysisReporter
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


def test_write_creates_all_report_files(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    paths = ExperimentReportBundleWriter().write(
        result,
        tmp_path,
    )

    assert paths == ExperimentReportBundlePaths(
        output_directory=tmp_path,
        json_path=tmp_path / "experiment.json",
        analysis_path=tmp_path / "analysis.json",
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
        html_path=tmp_path / "experiment.html",
        excel_path=tmp_path / "experiment.xlsx",
    )

    assert paths.json_path.is_file()
    assert paths.analysis_path.is_file()
    assert paths.csv_summary_path.is_file()
    assert paths.csv_games_path.is_file()
    assert paths.html_path.is_file()
    assert paths.excel_path.is_file()


def test_write_creates_missing_output_directories(
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

    assert paths.output_directory == output_directory
    assert output_directory.is_dir()
    assert (
        output_directory
        / "csv"
    ).is_dir()


def test_write_uses_custom_output_names(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    writer = ExperimentReportBundleWriter(
        json_filename="result.json",
        analysis_filename="statistics.json",
        html_filename="result.htm",
        excel_filename="result.xlsx",
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
    assert paths.analysis_path == (
        tmp_path
        / "statistics.json"
    )
    assert paths.html_path == (
        tmp_path
        / "result.htm"
    )
    assert paths.excel_path == (
        tmp_path
        / "result.xlsx"
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
    analysis_reporter = Mock(
        spec=ExperimentAnalysisReporter,
    )
    csv_reporter = Mock(
        spec=CsvExperimentReporter,
    )
    html_reporter = Mock(
        spec=HtmlExperimentReporter,
    )
    excel_reporter = Mock(
        spec=ExcelExperimentReporter,
    )

    json_path = tmp_path / "experiment.json"
    analysis_path = tmp_path / "analysis.json"
    html_path = tmp_path / "experiment.html"
    excel_path = tmp_path / "experiment.xlsx"
    csv_directory = tmp_path / "csv"

    json_reporter.write.return_value = json_path
    analysis_reporter.write.return_value = analysis_path
    csv_reporter.write.return_value = CsvReportPaths(
        summary_path=csv_directory / "summary.csv",
        games_path=csv_directory / "games.csv",
    )
    html_reporter.write.return_value = html_path
    excel_reporter.write.return_value = excel_path

    writer = ExperimentReportBundleWriter(
        json_reporter=json_reporter,
        analysis_reporter=analysis_reporter,
        csv_reporter=csv_reporter,
        html_reporter=html_reporter,
        excel_reporter=excel_reporter,
    )

    paths = writer.write(
        result,
        tmp_path,
    )

    json_reporter.write.assert_called_once_with(
        result,
        json_path,
    )
    analysis_reporter.write.assert_called_once_with(
        result,
        analysis_path,
    )
    csv_reporter.write.assert_called_once_with(
        result,
        csv_directory,
    )
    html_reporter.write.assert_called_once_with(
        result,
        html_path,
    )
    excel_reporter.write.assert_called_once_with(
        result,
        excel_path,
    )

    assert paths.json_path == json_path
    assert paths.analysis_path == analysis_path
    assert paths.html_path == html_path
    assert paths.excel_path == excel_path


def test_reporters_are_called_in_stable_order(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    calls: list[str] = []

    json_reporter = Mock(
        spec=JsonExperimentReporter,
    )
    analysis_reporter = Mock(
        spec=ExperimentAnalysisReporter,
    )
    csv_reporter = Mock(
        spec=CsvExperimentReporter,
    )
    html_reporter = Mock(
        spec=HtmlExperimentReporter,
    )
    excel_reporter = Mock(
        spec=ExcelExperimentReporter,
    )

    def write_json(
        current_result: ExperimentResult,
        path: Path,
    ) -> Path:
        assert current_result is result
        calls.append("json")
        return path

    def write_analysis(
        current_result: ExperimentResult,
        path: Path,
    ) -> Path:
        assert current_result is result
        calls.append("analysis")
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

    def write_html(
        current_result: ExperimentResult,
        path: Path,
    ) -> Path:
        assert current_result is result
        calls.append("html")
        return path

    def write_excel(
        current_result: ExperimentResult,
        path: Path,
    ) -> Path:
        assert current_result is result
        calls.append("excel")
        return path

    json_reporter.write.side_effect = write_json
    analysis_reporter.write.side_effect = write_analysis
    csv_reporter.write.side_effect = write_csv
    html_reporter.write.side_effect = write_html
    excel_reporter.write.side_effect = write_excel

    writer = ExperimentReportBundleWriter(
        json_reporter=json_reporter,
        analysis_reporter=analysis_reporter,
        csv_reporter=csv_reporter,
        html_reporter=html_reporter,
        excel_reporter=excel_reporter,
    )

    writer.write(
        result,
        tmp_path,
    )

    assert calls == [
        "json",
        "analysis",
        "csv",
        "html",
        "excel",
    ]


def test_write_propagates_analysis_reporter_exception(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    analysis_reporter = Mock(
        spec=ExperimentAnalysisReporter,
    )
    analysis_reporter.write.side_effect = RuntimeError(
        "Analysis output failed."
    )

    writer = ExperimentReportBundleWriter(
        analysis_reporter=analysis_reporter,
    )

    with pytest.raises(
        RuntimeError,
        match="Analysis output failed.",
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


@pytest.mark.parametrize(
    (
        "field_name",
        "json_filename",
        "analysis_filename",
        "html_filename",
        "excel_filename",
    ),
    (
        (
            "json_filename",
            "",
            "analysis.json",
            "experiment.html",
            "experiment.xlsx",
        ),
        (
            "analysis_filename",
            "experiment.json",
            " ",
            "experiment.html",
            "experiment.xlsx",
        ),
        (
            "html_filename",
            "experiment.json",
            "analysis.json",
            "\t",
            "experiment.xlsx",
        ),
        (
            "excel_filename",
            "experiment.json",
            "analysis.json",
            "experiment.html",
            "\n",
        ),
    ),
)
def test_writer_rejects_empty_filenames(
    field_name: str,
    json_filename: str,
    analysis_filename: str,
    html_filename: str,
    excel_filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=rf"{field_name} must not be empty.",
    ):
        ExperimentReportBundleWriter(
            json_filename=json_filename,
            analysis_filename=analysis_filename,
            html_filename=html_filename,
            excel_filename=excel_filename,
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "json_filename",
        "analysis_filename",
        "html_filename",
        "excel_filename",
    ),
    (
        (
            "json_filename",
            "reports/experiment.json",
            "analysis.json",
            "experiment.html",
            "experiment.xlsx",
        ),
        (
            "analysis_filename",
            "experiment.json",
            "reports/analysis.json",
            "experiment.html",
            "experiment.xlsx",
        ),
        (
            "html_filename",
            "experiment.json",
            "analysis.json",
            "reports/experiment.html",
            "experiment.xlsx",
        ),
        (
            "excel_filename",
            "experiment.json",
            "analysis.json",
            "experiment.html",
            "reports/experiment.xlsx",
        ),
    ),
)
def test_writer_rejects_directories_in_filenames(
    field_name: str,
    json_filename: str,
    analysis_filename: str,
    html_filename: str,
    excel_filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            rf"{field_name} must not contain "
            r"a directory."
        ),
    ):
        ExperimentReportBundleWriter(
            json_filename=json_filename,
            analysis_filename=analysis_filename,
            html_filename=html_filename,
            excel_filename=excel_filename,
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "json_filename",
        "analysis_filename",
        "html_filename",
        "excel_filename",
    ),
    (
        (
            "json_filename",
            "experiment.txt",
            "analysis.json",
            "experiment.html",
            "experiment.xlsx",
        ),
        (
            "analysis_filename",
            "experiment.json",
            "analysis.txt",
            "experiment.html",
            "experiment.xlsx",
        ),
        (
            "html_filename",
            "experiment.json",
            "analysis.json",
            "experiment.txt",
            "experiment.xlsx",
        ),
        (
            "excel_filename",
            "experiment.json",
            "analysis.json",
            "experiment.html",
            "experiment.xls",
        ),
    ),
)
def test_writer_rejects_invalid_extensions(
    field_name: str,
    json_filename: str,
    analysis_filename: str,
    html_filename: str,
    excel_filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=rf"{field_name} must use the",
    ):
        ExperimentReportBundleWriter(
            json_filename=json_filename,
            analysis_filename=analysis_filename,
            html_filename=html_filename,
            excel_filename=excel_filename,
        )


def test_writer_rejects_duplicate_root_filenames() -> None:
    with pytest.raises(
        ValueError,
        match="Root report filenames must be unique.",
    ):
        ExperimentReportBundleWriter(
            json_filename="result.json",
            analysis_filename="RESULT.JSON",
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
            analysis_path=duplicate_path,
            csv_summary_path=tmp_path / "summary.csv",
            csv_games_path=tmp_path / "games.csv",
            html_path=tmp_path / "result.html",
            excel_path=tmp_path / "result.xlsx",
        )


def test_bundle_paths_reject_paths_outside_output_directory(
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
            analysis_path=(
                output_directory
                / "analysis.json"
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
            html_path=(
                output_directory
                / "experiment.html"
            ),
            excel_path=(
                output_directory
                / "experiment.xlsx"
            ),
        )


def test_bundle_paths_are_immutable(
    tmp_path: Path,
) -> None:
    paths = ExperimentReportBundlePaths(
        output_directory=tmp_path,
        json_path=tmp_path / "experiment.json",
        analysis_path=tmp_path / "analysis.json",
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
        html_path=tmp_path / "experiment.html",
        excel_path=tmp_path / "experiment.xlsx",
    )

    with pytest.raises(AttributeError):
        paths.analysis_path = (  # type: ignore[misc]
            tmp_path
            / "changed.json"
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