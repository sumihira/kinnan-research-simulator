from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from krs.report.analysis import ExperimentAnalysisReporter
from krs.report.analysis_html import (
    ExperimentAnalysisHtmlReporter,
)
from krs.report.analysis_markdown import (
    ExperimentAnalysisMarkdownReporter,
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
from krs.simulation.experiment import ExperimentResult


@dataclass(frozen=True, slots=True)
class ExperimentReportBundlePaths:
    """
    Stores every path generated for one experiment report bundle.
    """

    output_directory: Path
    json_path: Path
    analysis_json_path: Path
    html_path: Path
    analysis_html_path: Path
    excel_path: Path
    summary_markdown_path: Path
    analysis_markdown_path: Path
    csv_summary_path: Path
    csv_games_path: Path

    def __post_init__(self) -> None:
        generated_paths = self.all_paths

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

    @property
    def all_paths(self) -> tuple[Path, ...]:
        """
        Return every generated report path in stable output order.
        """
        return (
            self.json_path,
            self.analysis_json_path,
            self.html_path,
            self.analysis_html_path,
            self.excel_path,
            self.summary_markdown_path,
            self.analysis_markdown_path,
            self.csv_summary_path,
            self.csv_games_path,
        )

    @property
    def markdown_paths(self) -> tuple[Path, Path]:
        """
        Return the generated Markdown report paths.
        """
        return (
            self.summary_markdown_path,
            self.analysis_markdown_path,
        )

    @property
    def html_paths(self) -> tuple[Path, Path]:
        """
        Return the generated HTML report paths.
        """
        return (
            self.html_path,
            self.analysis_html_path,
        )

    @property
    def json_paths(self) -> tuple[Path, Path]:
        """
        Return the generated JSON report paths.
        """
        return (
            self.json_path,
            self.analysis_json_path,
        )

    @property
    def csv_paths(self) -> tuple[Path, Path]:
        """
        Return the generated CSV report paths.
        """
        return (
            self.csv_summary_path,
            self.csv_games_path,
        )


@dataclass(frozen=True, slots=True)
class ExperimentReportBundleWriter:
    """
    Writes every supported report format for one experiment.

    The bundle writer is a facade over existing reporters. It does not
    calculate statistics, duplicate serialization logic, or modify the
    supplied ExperimentResult.
    """

    json_reporter: JsonExperimentReporter = field(
        default_factory=JsonExperimentReporter,
    )
    analysis_json_reporter: ExperimentAnalysisReporter = field(
        default_factory=ExperimentAnalysisReporter,
    )
    html_reporter: HtmlExperimentReporter = field(
        default_factory=HtmlExperimentReporter,
    )
    analysis_html_reporter: (
        ExperimentAnalysisHtmlReporter
    ) = field(
        default_factory=ExperimentAnalysisHtmlReporter,
    )
    excel_reporter: ExcelExperimentReporter = field(
        default_factory=ExcelExperimentReporter,
    )
    summary_markdown_reporter: (
        ExperimentSummaryMarkdownReporter
    ) = field(
        default_factory=ExperimentSummaryMarkdownReporter,
    )
    analysis_markdown_reporter: (
        ExperimentAnalysisMarkdownReporter
    ) = field(
        default_factory=ExperimentAnalysisMarkdownReporter,
    )
    csv_reporter: CsvExperimentReporter = field(
        default_factory=CsvExperimentReporter,
    )

    json_filename: str = "experiment.json"
    analysis_json_filename: str = "analysis.json"
    html_filename: str = "experiment.html"
    analysis_html_filename: str = "analysis.html"
    excel_filename: str = "experiment.xlsx"
    summary_markdown_filename: str = "summary.md"
    analysis_markdown_filename: str = "analysis.md"
    csv_directory_name: str = "csv"

    def __post_init__(self) -> None:
        self._validate_filename(
            self.json_filename,
            field_name="json_filename",
            allowed_suffixes=(".json",),
        )
        self._validate_filename(
            self.analysis_json_filename,
            field_name="analysis_json_filename",
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
            self.analysis_html_filename,
            field_name="analysis_html_filename",
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
        self._validate_filename(
            self.summary_markdown_filename,
            field_name="summary_markdown_filename",
            allowed_suffixes=(
                ".md",
                ".markdown",
            ),
        )
        self._validate_filename(
            self.analysis_markdown_filename,
            field_name="analysis_markdown_filename",
            allowed_suffixes=(
                ".md",
                ".markdown",
            ),
        )
        self._validate_directory_name(
            self.csv_directory_name,
            field_name="csv_directory_name",
        )

        root_filenames = tuple(
            filename.casefold()
            for filename in (
                self.json_filename,
                self.analysis_json_filename,
                self.html_filename,
                self.analysis_html_filename,
                self.excel_filename,
                self.summary_markdown_filename,
                self.analysis_markdown_filename,
            )
        )

        if len(set(root_filenames)) != len(root_filenames):
            raise ValueError(
                "Root report filenames must be unique."
            )

        csv_directory_name = (
            self.csv_directory_name.casefold()
        )

        if csv_directory_name in root_filenames:
            raise ValueError(
                "csv_directory_name must not match a root "
                "report filename."
            )

    def write(
        self,
        result: ExperimentResult,
        directory: str | Path,
    ) -> ExperimentReportBundlePaths:
        """
        Write every supported report into one output directory.

        Missing output directories are created automatically. Exceptions
        raised by individual reporters are propagated to the caller.
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
        analysis_json_path = (
            output_directory
            / self.analysis_json_filename
        )
        html_path = (
            output_directory
            / self.html_filename
        )
        analysis_html_path = (
            output_directory
            / self.analysis_html_filename
        )
        excel_path = (
            output_directory
            / self.excel_filename
        )
        summary_markdown_path = (
            output_directory
            / self.summary_markdown_filename
        )
        analysis_markdown_path = (
            output_directory
            / self.analysis_markdown_filename
        )
        csv_directory = (
            output_directory
            / self.csv_directory_name
        )

        written_json_path = self.json_reporter.write(
            result,
            json_path,
        )
        written_analysis_json_path = (
            self.analysis_json_reporter.write(
                result,
                analysis_json_path,
            )
        )
        written_html_path = self.html_reporter.write(
            result,
            html_path,
        )
        written_analysis_html_path = (
            self.analysis_html_reporter.write(
                result,
                analysis_html_path,
            )
        )
        written_excel_path = self.excel_reporter.write(
            result,
            excel_path,
        )
        written_summary_markdown_path = (
            self.summary_markdown_reporter.write(
                result,
                summary_markdown_path,
            )
        )
        written_analysis_markdown_path = (
            self.analysis_markdown_reporter.write(
                result,
                analysis_markdown_path,
            )
        )
        csv_paths = self.csv_reporter.write(
            result,
            csv_directory,
        )

        return self._create_paths(
            output_directory=output_directory,
            json_path=written_json_path,
            analysis_json_path=(
                written_analysis_json_path
            ),
            html_path=written_html_path,
            analysis_html_path=(
                written_analysis_html_path
            ),
            excel_path=written_excel_path,
            summary_markdown_path=(
                written_summary_markdown_path
            ),
            analysis_markdown_path=(
                written_analysis_markdown_path
            ),
            csv_paths=csv_paths,
        )

    @staticmethod
    def _create_paths(
        *,
        output_directory: Path,
        json_path: Path,
        analysis_json_path: Path,
        html_path: Path,
        analysis_html_path: Path,
        excel_path: Path,
        summary_markdown_path: Path,
        analysis_markdown_path: Path,
        csv_paths: CsvReportPaths,
    ) -> ExperimentReportBundlePaths:
        """
        Create the immutable bundle path result.
        """
        return ExperimentReportBundlePaths(
            output_directory=output_directory,
            json_path=json_path,
            analysis_json_path=analysis_json_path,
            html_path=html_path,
            analysis_html_path=analysis_html_path,
            excel_path=excel_path,
            summary_markdown_path=summary_markdown_path,
            analysis_markdown_path=analysis_markdown_path,
            csv_summary_path=csv_paths.summary_path,
            csv_games_path=csv_paths.games_path,
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