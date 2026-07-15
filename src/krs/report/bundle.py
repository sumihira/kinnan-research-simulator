from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from krs.report.analysis import ExperimentAnalysisReporter
from krs.report.csv import (
    CsvExperimentReporter,
    CsvReportPaths,
)
from krs.report.excel import ExcelExperimentReporter
from krs.report.html import HtmlExperimentReporter
from krs.report.json import JsonExperimentReporter
from krs.simulation.experiment import ExperimentResult


@dataclass(frozen=True, slots=True)
class ExperimentReportBundlePaths:
    """
    Stores every path generated for one experiment report bundle.
    """

    output_directory: Path
    json_path: Path
    analysis_path: Path
    csv_summary_path: Path
    csv_games_path: Path
    html_path: Path
    excel_path: Path

    def __post_init__(self) -> None:
        generated_paths = (
            self.json_path,
            self.analysis_path,
            self.csv_summary_path,
            self.csv_games_path,
            self.html_path,
            self.excel_path,
        )

        if len(set(generated_paths)) != len(generated_paths):
            raise ValueError(
                "Report bundle paths must be unique."
            )

        for generated_path in generated_paths:
            if generated_path == self.output_directory:
                raise ValueError(
                    "Generated report path must not equal "
                    "output_directory."
                )

            if self.output_directory not in generated_path.parents:
                raise ValueError(
                    "Generated report paths must be inside "
                    "output_directory."
                )


@dataclass(frozen=True, slots=True)
class ExperimentReportBundleWriter:
    """
    Writes all supported report formats for one experiment.

    The bundle writer coordinates existing reporters only. It does not
    calculate statistics, mutate ExperimentResult, or duplicate individual
    serialization logic.
    """

    json_reporter: JsonExperimentReporter = field(
        default_factory=JsonExperimentReporter,
    )
    analysis_reporter: ExperimentAnalysisReporter = field(
        default_factory=ExperimentAnalysisReporter,
    )
    csv_reporter: CsvExperimentReporter = field(
        default_factory=CsvExperimentReporter,
    )
    html_reporter: HtmlExperimentReporter = field(
        default_factory=HtmlExperimentReporter,
    )
    excel_reporter: ExcelExperimentReporter = field(
        default_factory=ExcelExperimentReporter,
    )
    json_filename: str = "experiment.json"
    analysis_filename: str = "analysis.json"
    html_filename: str = "experiment.html"
    excel_filename: str = "experiment.xlsx"
    csv_directory_name: str = "csv"

    def __post_init__(self) -> None:
        self._validate_filename(
            self.json_filename,
            field_name="json_filename",
            allowed_suffixes=(".json",),
        )
        self._validate_filename(
            self.analysis_filename,
            field_name="analysis_filename",
            allowed_suffixes=(".json",),
        )
        self._validate_filename(
            self.html_filename,
            field_name="html_filename",
            allowed_suffixes=(
                ".html",
                ".htm",
            ),
        )
        self._validate_filename(
            self.excel_filename,
            field_name="excel_filename",
            allowed_suffixes=(".xlsx",),
        )
        self._validate_directory_name(
            self.csv_directory_name,
            field_name="csv_directory_name",
        )

        root_filenames = (
            self.json_filename.casefold(),
            self.analysis_filename.casefold(),
            self.html_filename.casefold(),
            self.excel_filename.casefold(),
        )

        if len(set(root_filenames)) != len(root_filenames):
            raise ValueError(
                "Root report filenames must be unique."
            )

    def write(
        self,
        result: ExperimentResult,
        directory: str | Path,
    ) -> ExperimentReportBundlePaths:
        """
        Write JSON, analysis JSON, CSV, HTML, and Excel reports.

        Missing output directories are created automatically.
        """
        output_directory = Path(directory)

        if (
            output_directory.exists()
            and not output_directory.is_dir()
        ):
            raise ValueError(
                "Report bundle output path is not a directory: "
                f"{output_directory}"
            )

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        json_path = (
            output_directory
            / self.json_filename
        )
        analysis_path = (
            output_directory
            / self.analysis_filename
        )
        html_path = (
            output_directory
            / self.html_filename
        )
        excel_path = (
            output_directory
            / self.excel_filename
        )
        csv_directory = (
            output_directory
            / self.csv_directory_name
        )

        written_json_path = self.json_reporter.write(
            result,
            json_path,
        )
        written_analysis_path = self.analysis_reporter.write(
            result,
            analysis_path,
        )
        csv_paths = self.csv_reporter.write(
            result,
            csv_directory,
        )
        written_html_path = self.html_reporter.write(
            result,
            html_path,
        )
        written_excel_path = self.excel_reporter.write(
            result,
            excel_path,
        )

        return self._create_paths(
            output_directory=output_directory,
            json_path=written_json_path,
            analysis_path=written_analysis_path,
            csv_paths=csv_paths,
            html_path=written_html_path,
            excel_path=written_excel_path,
        )

    @staticmethod
    def _create_paths(
        *,
        output_directory: Path,
        json_path: Path,
        analysis_path: Path,
        csv_paths: CsvReportPaths,
        html_path: Path,
        excel_path: Path,
    ) -> ExperimentReportBundlePaths:
        """
        Create the immutable output-path result.
        """
        return ExperimentReportBundlePaths(
            output_directory=output_directory,
            json_path=json_path,
            analysis_path=analysis_path,
            csv_summary_path=csv_paths.summary_path,
            csv_games_path=csv_paths.games_path,
            html_path=html_path,
            excel_path=excel_path,
        )

    @staticmethod
    def _validate_filename(
        filename: str,
        *,
        field_name: str,
        allowed_suffixes: tuple[str, ...],
    ) -> None:
        """
        Validate a plain output filename and its extension.
        """
        if not filename.strip():
            raise ValueError(
                f"{field_name} must not be empty."
            )

        filename_path = Path(filename)

        if filename_path.name != filename:
            raise ValueError(
                f"{field_name} must not contain a directory."
            )

        if (
            filename_path.suffix.casefold()
            not in allowed_suffixes
        ):
            formatted_suffixes = " or ".join(
                allowed_suffixes
            )

            raise ValueError(
                f"{field_name} must use the "
                f"{formatted_suffixes} extension."
            )

    @staticmethod
    def _validate_directory_name(
        directory_name: str,
        *,
        field_name: str,
    ) -> None:
        """
        Validate a single output subdirectory name.
        """
        if not directory_name.strip():
            raise ValueError(
                f"{field_name} must not be empty."
            )

        directory_path = Path(directory_name)

        if directory_path.name != directory_name:
            raise ValueError(
                f"{field_name} must not contain a directory."
            )

        if directory_name in {
            ".",
            "..",
        }:
            raise ValueError(
                f"{field_name} must be a valid directory name."
            )