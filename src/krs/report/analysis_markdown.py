from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from krs.simulation.experiment import ExperimentResult
from krs.statistics.experiment_analysis import (
    ExperimentAnalysis,
    ExperimentAnalysisCalculator,
)


MarkdownRows = tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class ExperimentAnalysisMarkdownReporter:
    """
    Creates a Markdown report from complete experiment statistics.

    Statistical calculations are delegated to
    ExperimentAnalysisCalculator. This reporter performs presentation and
    file serialization only.
    """

    title: str = "Kinnan Research Simulator Analysis"
    analysis_calculator: ExperimentAnalysisCalculator = field(
        default_factory=ExperimentAnalysisCalculator,
    )

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be empty.")

    def analyze(
        self,
        result: ExperimentResult,
    ) -> ExperimentAnalysis:
        """
        Calculate complete statistical analysis for one experiment.
        """
        return self.analysis_calculator.calculate(result)

    def to_markdown(
        self,
        result: ExperimentResult,
    ) -> str:
        """
        Calculate analysis and return a complete Markdown report.
        """
        analysis = self.analyze(result)

        return self.analysis_to_markdown(analysis)

    def analysis_to_markdown(
        self,
        analysis: ExperimentAnalysis,
    ) -> str:
        """
        Convert an existing ExperimentAnalysis into Markdown.
        """
        sections = (
            self._render_title(),
            self._render_overview(analysis),
            self._render_confidence_interval(analysis),
            self._render_experiment_statistics(analysis),
            self._render_win_turn_statistics(analysis),
        )

        return "\n\n---\n\n".join(sections) + "\n"

    def write(
        self,
        result: ExperimentResult,
        path: str | Path,
    ) -> Path:
        """
        Write a UTF-8 Markdown analysis report.

        Missing parent directories are created automatically.
        """
        output_path = Path(path)

        if output_path.exists() and output_path.is_dir():
            raise ValueError(
                "Analysis Markdown report path is a directory: "
                f"{output_path}"
            )

        if output_path.suffix.casefold() not in {
            ".md",
            ".markdown",
        }:
            raise ValueError(
                "Analysis Markdown report path must use "
                "the .md or .markdown extension."
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            self.to_markdown(result),
            encoding="utf-8",
        )

        return output_path

    def _render_title(self) -> str:
        """
        Render the report title.
        """
        return f"# {self._escape_text(self.title)}"

    def _render_overview(
        self,
        analysis: ExperimentAnalysis,
    ) -> str:
        """
        Render top-level experiment results.
        """
        rows: MarkdownRows = (
            (
                "Games completed",
                f"{analysis.games_completed:,}",
            ),
            (
                "Wins",
                f"{analysis.wins:,}",
            ),
            (
                "Non-wins",
                f"{analysis.non_wins:,}",
            ),
            (
                "Win rate",
                f"{analysis.win_rate_percent:.3f}%",
            ),
            (
                "Winning games observed",
                self._format_boolean(analysis.has_wins),
            ),
        )

        return self._render_section(
            title="Overview",
            rows=rows,
        )

    def _render_confidence_interval(
        self,
        analysis: ExperimentAnalysis,
    ) -> str:
        """
        Render the win-rate confidence interval.
        """
        interval = (
            analysis.experiment_statistics
            .win_rate_confidence_interval
        )

        confidence_percent = (
            interval.confidence_level
            * 100.0
        )
        width_percent = interval.width * 100.0
        margin_below_percent = interval.margin_below * 100.0
        margin_above_percent = interval.margin_above * 100.0

        rows: MarkdownRows = (
            (
                "Confidence level",
                f"{confidence_percent:.3f}%",
            ),
            (
                "Wins / Games",
                f"{interval.wins:,} / {interval.games:,}",
            ),
            (
                "Observed win rate",
                f"{interval.observed_percent:.3f}%",
            ),
            (
                "Lower bound",
                f"{interval.lower_percent:.3f}%",
            ),
            (
                "Upper bound",
                f"{interval.upper_percent:.3f}%",
            ),
            (
                "Interval width",
                f"{width_percent:.3f} percentage points",
            ),
            (
                "Margin below",
                f"{margin_below_percent:.3f} percentage points",
            ),
            (
                "Margin above",
                f"{margin_above_percent:.3f} percentage points",
            ),
        )

        return self._render_section(
            title="Win Rate Confidence Interval",
            rows=rows,
        )

    def _render_experiment_statistics(
        self,
        analysis: ExperimentAnalysis,
    ) -> str:
        """
        Render statistics calculated from all completed games.
        """
        statistics = analysis.experiment_statistics

        activation_deviation = (
            statistics.kinnan_activation_standard_deviation
        )

        rows: MarkdownRows = (
            (
                "Turn-limit games",
                f"{statistics.turn_limit_games:,}",
            ),
            (
                "Turn-limit rate",
                f"{statistics.turn_limit_percent:.3f}%",
            ),
            (
                "Average turns started",
                f"{statistics.average_turns_started:.3f}",
            ),
            (
                "Turn standard deviation",
                f"{statistics.turn_standard_deviation:.3f}",
            ),
            (
                "Average Kinnan activations",
                f"{statistics.average_kinnan_activations:.3f}",
            ),
            (
                "Kinnan activation standard deviation",
                f"{activation_deviation:.3f}",
            ),
            (
                "Fastest win turn",
                self._format_optional_integer(
                    statistics.fastest_win_turn
                ),
            ),
        )

        return self._render_section(
            title="Experiment Statistics",
            rows=rows,
        )

    def _render_win_turn_statistics(
        self,
        analysis: ExperimentAnalysis,
    ) -> str:
        """
        Render statistics calculated from winning games only.
        """
        statistics = analysis.win_turn_statistics

        rows: MarkdownRows = (
            (
                "Winning games",
                f"{statistics.wins:,}",
            ),
            (
                "Win rate",
                f"{statistics.win_rate_percent:.3f}%",
            ),
            (
                "Fastest win turn",
                self._format_optional_integer(
                    statistics.fastest_win_turn
                ),
            ),
            (
                "Slowest win turn",
                self._format_optional_integer(
                    statistics.slowest_win_turn
                ),
            ),
            (
                "Average win turn",
                self._format_optional_float(
                    statistics.average_win_turn
                ),
            ),
            (
                "Median win turn",
                self._format_optional_float(
                    statistics.median_win_turn
                ),
            ),
            (
                "90th percentile win turn",
                self._format_optional_integer(
                    statistics.percentile_90_win_turn
                ),
            ),
            (
                "95th percentile win turn",
                self._format_optional_integer(
                    statistics.percentile_95_win_turn
                ),
            ),
            (
                "Win-turn standard deviation",
                self._format_optional_float(
                    statistics.win_turn_standard_deviation
                ),
            ),
        )

        section = self._render_section(
            title="Win Turn Statistics",
            rows=rows,
        )

        if statistics.has_wins:
            return section

        return "\n\n".join(
            (
                section,
                (
                    "> No winning games were observed. "
                    "Win-turn measurements are unavailable."
                ),
            )
        )

    @classmethod
    def _render_section(
        cls,
        *,
        title: str,
        rows: MarkdownRows,
    ) -> str:
        """
        Render one Markdown heading followed by a two-column table.
        """
        return "\n\n".join(
            (
                f"## {cls._escape_text(title)}",
                cls._render_table(rows),
            )
        )

    @classmethod
    def _render_table(
        cls,
        rows: MarkdownRows,
    ) -> str:
        """
        Render a GitHub-compatible Markdown table.
        """
        header = "\n".join(
            (
                "| Metric | Value |",
                "|:--|--:|",
            )
        )

        rendered_rows = "\n".join(
            (
                f"| {cls._escape_table_cell(label)} "
                f"| {cls._escape_table_cell(value)} |"
            )
            for label, value in rows
        )

        return "\n".join(
            (
                header,
                rendered_rows,
            )
        )

    @staticmethod
    def _format_boolean(
        value: bool,
    ) -> str:
        """
        Format a boolean for human-readable Markdown.
        """
        return "Yes" if value else "No"

    @staticmethod
    def _format_optional_integer(
        value: int | None,
    ) -> str:
        """
        Format an optional integer statistic.
        """
        return (
            str(value)
            if value is not None
            else "N/A"
        )

    @staticmethod
    def _format_optional_float(
        value: float | None,
    ) -> str:
        """
        Format an optional floating-point statistic.
        """
        return (
            f"{value:.3f}"
            if value is not None
            else "N/A"
        )

    @staticmethod
    def _escape_table_cell(
        value: str,
    ) -> str:
        """
        Escape characters that can break a Markdown table cell.
        """
        return (
            value
            .replace("\\", "\\\\")
            .replace("|", "\\|")
            .replace("\r\n", "<br>")
            .replace("\n", "<br>")
            .replace("\r", "<br>")
        )

    @staticmethod
    def _escape_text(
        value: str,
    ) -> str:
        """
        Escape common Markdown control characters in headings.
        """
        escaped_characters = {
            "\\": "\\\\",
            "`": "\\`",
            "*": "\\*",
            "_": "\\_",
            "{": "\\{",
            "}": "\\}",
            "[": "\\[",
            "]": "\\]",
            "<": "\\<",
            ">": "\\>",
            "#": "\\#",
            "+": "\\+",
            "-": "\\-",
            "!": "\\!",
            "|": "\\|",
        }

        return "".join(
            escaped_characters.get(
                character,
                character,
            )
            for character in value
        )