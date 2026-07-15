from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from pathlib import Path

from krs.simulation.experiment import ExperimentResult
from krs.statistics.experiment_analysis import (
    ExperimentAnalysis,
    ExperimentAnalysisCalculator,
)


@dataclass(frozen=True, slots=True)
class ExperimentAnalysisHtmlReporter:
    """
    Creates a standalone HTML report from experiment statistics.

    Statistical calculations are delegated to
    ExperimentAnalysisCalculator. The reporter performs presentation and
    serialization only.
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
        """Calculate complete analysis for one experiment."""
        return self.analysis_calculator.calculate(result)

    def to_html(
        self,
        result: ExperimentResult,
    ) -> str:
        """Create a complete standalone HTML document."""
        analysis = self.analyze(result)

        return self.analysis_to_html(analysis)

    def analysis_to_html(
        self,
        analysis: ExperimentAnalysis,
    ) -> str:
        """Convert an existing ExperimentAnalysis into HTML."""
        return "\n".join(
            (
                "<!DOCTYPE html>",
                '<html lang="en">',
                "<head>",
                '  <meta charset="utf-8">',
                (
                    '  <meta name="viewport" '
                    'content="width=device-width, initial-scale=1">'
                ),
                f"  <title>{escape(self.title)}</title>",
                "  <style>",
                self._stylesheet(),
                "  </style>",
                "</head>",
                "<body>",
                '  <main class="report">',
                self._render_header(analysis),
                self._render_confidence_interval(analysis),
                self._render_experiment_statistics(analysis),
                self._render_win_turn_statistics(analysis),
                "  </main>",
                "</body>",
                "</html>",
                "",
            )
        )

    def write(
        self,
        result: ExperimentResult,
        path: str | Path,
    ) -> Path:
        """
        Write a standalone UTF-8 HTML analysis report.

        Missing parent directories are created automatically.
        """
        output_path = Path(path)

        if output_path.exists() and output_path.is_dir():
            raise ValueError(
                "Analysis HTML report path is a directory: "
                f"{output_path}"
            )

        if output_path.suffix.casefold() not in {
            ".html",
            ".htm",
        }:
            raise ValueError(
                "Analysis HTML report path must use "
                "the .html or .htm extension."
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            self.to_html(result),
            encoding="utf-8",
        )

        return output_path

    def _render_header(
        self,
        analysis: ExperimentAnalysis,
    ) -> str:
        interval = (
            analysis.experiment_statistics
            .win_rate_confidence_interval
        )

        confidence_percent = (
            interval.confidence_level
            * 100.0
        )

        return "\n".join(
            (
                "    <header>",
                f"      <h1>{escape(self.title)}</h1>",
                (
                    '      <p class="subtitle">'
                    f"{analysis.games_completed:,} games analyzed"
                    "</p>"
                ),
                '      <div class="headline-grid">',
                self._render_headline_metric(
                    label="Win rate",
                    value=f"{analysis.win_rate_percent:.2f}%",
                ),
                self._render_headline_metric(
                    label="Wins",
                    value=f"{analysis.wins:,}",
                ),
                self._render_headline_metric(
                    label="Non-wins",
                    value=f"{analysis.non_wins:,}",
                ),
                self._render_headline_metric(
                    label="Confidence level",
                    value=f"{confidence_percent:.1f}%",
                ),
                "      </div>",
                "    </header>",
            )
        )

    @staticmethod
    def _render_headline_metric(
        *,
        label: str,
        value: str,
    ) -> str:
        return "\n".join(
            (
                '        <article class="headline-card">',
                f"          <h2>{escape(label)}</h2>",
                f"          <p>{escape(value)}</p>",
                "        </article>",
            )
        )

    def _render_confidence_interval(
        self,
        analysis: ExperimentAnalysis,
    ) -> str:
        interval = (
            analysis.experiment_statistics
            .win_rate_confidence_interval
        )

        observed_percent = interval.observed_percent
        lower_percent = interval.lower_percent
        upper_percent = interval.upper_percent
        width_percent = interval.width * 100.0

        rows = (
            (
                "Observed win rate",
                f"{observed_percent:.3f}%",
            ),
            (
                "Lower bound",
                f"{lower_percent:.3f}%",
            ),
            (
                "Upper bound",
                f"{upper_percent:.3f}%",
            ),
            (
                "Interval width",
                f"{width_percent:.3f} percentage points",
            ),
            (
                "Wins / Games",
                f"{interval.wins:,} / {interval.games:,}",
            ),
        )

        return "\n".join(
            (
                (
                    '    <section '
                    'aria-labelledby="confidence-heading">'
                ),
                (
                    '      <h2 id="confidence-heading">'
                    "Win Rate Confidence Interval"
                    "</h2>"
                ),
                '      <div class="interval-visual">',
                (
                    '        <div class="interval-track" '
                    'aria-label="Win rate confidence interval">'
                ),
                (
                    '          <div class="interval-range" '
                    f'style="left: {lower_percent:.6f}%; '
                    f'width: {width_percent:.6f}%">'
                    "</div>"
                ),
                (
                    '          <div class="interval-observed" '
                    f'style="left: {observed_percent:.6f}%">'
                    "</div>"
                ),
                "        </div>",
                "      </div>",
                self._render_table(rows),
                "    </section>",
            )
        )

    def _render_experiment_statistics(
        self,
        analysis: ExperimentAnalysis,
    ) -> str:
        statistics = analysis.experiment_statistics

        activation_deviation = (
            statistics.kinnan_activation_standard_deviation
        )

        rows = (
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

        return "\n".join(
            (
                (
                    '    <section '
                    'aria-labelledby="experiment-statistics-heading">'
                ),
                (
                    '      <h2 id="experiment-statistics-heading">'
                    "Experiment Statistics"
                    "</h2>"
                ),
                self._render_table(rows),
                "    </section>",
            )
        )

    def _render_win_turn_statistics(
        self,
        analysis: ExperimentAnalysis,
    ) -> str:
        statistics = analysis.win_turn_statistics

        rows = (
            (
                "Winning games",
                f"{statistics.wins:,}",
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

        empty_message = (
            ""
            if statistics.has_wins
            else "\n".join(
                (
                    '      <p class="empty-message">',
                    (
                        "        No winning games were observed. "
                        "Win-turn measurements are unavailable."
                    ),
                    "      </p>",
                )
            )
        )

        return "\n".join(
            (
                (
                    '    <section '
                    'aria-labelledby="win-turn-heading">'
                ),
                (
                    '      <h2 id="win-turn-heading">'
                    "Win Turn Statistics"
                    "</h2>"
                ),
                empty_message,
                self._render_table(rows),
                "    </section>",
            )
        )

    @staticmethod
    def _render_table(
        rows: tuple[tuple[str, str], ...],
    ) -> str:
        rendered_rows = "\n".join(
            "\n".join(
                (
                    "          <tr>",
                    (
                        '            <th scope="row">'
                        f"{escape(label)}"
                        "</th>"
                    ),
                    f"            <td>{escape(value)}</td>",
                    "          </tr>",
                )
            )
            for label, value in rows
        )

        return "\n".join(
            (
                '      <div class="table-container">',
                '        <table class="statistics-table">',
                "          <tbody>",
                rendered_rows,
                "          </tbody>",
                "        </table>",
                "      </div>",
            )
        )

    @staticmethod
    def _format_optional_integer(
        value: int | None,
    ) -> str:
        return (
            str(value)
            if value is not None
            else "N/A"
        )

    @staticmethod
    def _format_optional_float(
        value: float | None,
    ) -> str:
        return (
            f"{value:.3f}"
            if value is not None
            else "N/A"
        )

    @staticmethod
    def _stylesheet() -> str:
        return """
    :root {
      color-scheme: light;
      font-family:
        Inter,
        "Segoe UI",
        Arial,
        sans-serif;
      background: #f4f6f8;
      color: #17202a;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      background: #f4f6f8;
    }

    .report {
      width: min(1100px, calc(100% - 32px));
      margin: 32px auto;
    }

    header,
    section {
      margin-bottom: 24px;
      padding: 24px;
      border: 1px solid #dce1e6;
      border-radius: 12px;
      background: #ffffff;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
    }

    h1,
    h2,
    p {
      margin-top: 0;
    }

    h1 {
      margin-bottom: 8px;
      font-size: clamp(28px, 5vw, 42px);
    }

    section > h2 {
      margin-bottom: 18px;
      font-size: 22px;
    }

    .subtitle {
      margin-bottom: 20px;
      color: #5f6b76;
    }

    .headline-grid {
      display: grid;
      grid-template-columns:
        repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
    }

    .headline-card {
      padding: 16px;
      border: 1px solid #e2e8ee;
      border-radius: 10px;
      background: #fafbfc;
    }

    .headline-card h2 {
      margin-bottom: 10px;
      color: #5f6b76;
      font-size: 14px;
    }

    .headline-card p {
      margin-bottom: 0;
      font-size: 27px;
      font-weight: 700;
    }

    .interval-visual {
      margin-bottom: 22px;
      padding: 18px 10px;
    }

    .interval-track {
      position: relative;
      width: 100%;
      height: 18px;
      border-radius: 999px;
      background: #e8edf2;
    }

    .interval-range {
      position: absolute;
      top: 0;
      height: 100%;
      border-radius: inherit;
      background: #90cdf4;
    }

    .interval-observed {
      position: absolute;
      top: -6px;
      width: 4px;
      height: 30px;
      border-radius: 2px;
      background: #1f4e78;
      transform: translateX(-2px);
    }

    .table-container {
      overflow-x: auto;
    }

    table {
      width: 100%;
      border-collapse: collapse;
    }

    th,
    td {
      padding: 12px;
      border-bottom: 1px solid #e2e8ee;
      text-align: left;
    }

    th {
      width: 55%;
      color: #5f6b76;
      font-weight: 600;
    }

    td {
      font-variant-numeric: tabular-nums;
    }

    .empty-message {
      padding: 14px;
      border: 1px dashed #cbd3da;
      border-radius: 8px;
      background: #fafbfc;
      color: #5f6b76;
    }

    @media (max-width: 640px) {
      .report {
        width: min(100% - 16px, 1100px);
        margin: 8px auto;
      }

      header,
      section {
        padding: 16px;
        border-radius: 8px;
      }

      th {
        width: auto;
      }
    }
""".strip()