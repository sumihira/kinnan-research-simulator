from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from pathlib import Path

from krs.report.graph import (
    DistributionData,
    DistributionPoint,
    ExperimentGraphData,
    GraphDataReporter,
)
from krs.simulation.experiment import ExperimentResult
from krs.simulation.runner import GoldfishRunResult


@dataclass(frozen=True, slots=True)
class HtmlExperimentReporter:
    """
    Converts ExperimentResult into a standalone HTML report.

    The report embeds its stylesheet and requires no external assets.
    Existing simulation statistics are displayed without recalculation.

    Graph-ready distribution data is delegated to GraphDataReporter.
    """

    title: str = "Kinnan Research Simulator Report"
    graph_data_reporter: GraphDataReporter = field(
        default_factory=GraphDataReporter,
    )

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be empty.")

    def to_html(
        self,
        result: ExperimentResult,
    ) -> str:
        """
        Return a complete standalone HTML document.
        """
        graph_data = self.graph_data_reporter.build(result)

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
                self._render_header(result),
                self._render_summary(result),
                self._render_config(result),
                self._render_graphs(graph_data),
                self._render_games(result),
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
        Write a standalone UTF-8 HTML report.

        Missing parent directories are created automatically.
        """
        output_path = Path(path)

        if output_path.exists() and output_path.is_dir():
            raise ValueError(
                f"HTML report path is a directory: {output_path}"
            )

        if output_path.suffix.casefold() not in {
            ".html",
            ".htm",
        }:
            raise ValueError(
                "HTML report path must use the .html or .htm extension."
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
        result: ExperimentResult,
    ) -> str:
        """
        Render the report title and headline win rate.
        """
        summary = result.summary
        win_rate_percent = summary.win_rate * 100.0

        return "\n".join(
            (
                "    <header>",
                f"      <h1>{escape(self.title)}</h1>",
                (
                    '      <p class="subtitle">'
                    f"{summary.games_completed:,} games completed"
                    "</p>"
                ),
                (
                    '      <div class="win-rate" '
                    'aria-label="Win rate">'
                ),
                (
                    '        <div class="win-rate-value">'
                    f"{win_rate_percent:.2f}%"
                    "</div>"
                ),
                '        <div class="progress-track">',
                (
                    '          <div class="progress-value" '
                    f'style="width: {win_rate_percent:.6f}%">'
                    "</div>"
                ),
                "        </div>",
                "      </div>",
                "    </header>",
            )
        )

    def _render_summary(
        self,
        result: ExperimentResult,
    ) -> str:
        """
        Render aggregate experiment metrics.
        """
        summary = result.summary

        fastest_win_turn = (
            str(summary.fastest_win_turn)
            if summary.fastest_win_turn is not None
            else "N/A"
        )

        cards = (
            (
                "Games completed",
                f"{summary.games_completed:,}",
            ),
            (
                "Wins",
                f"{summary.wins:,}",
            ),
            (
                "Non-wins",
                f"{summary.non_wins:,}",
            ),
            (
                "Turn-limit games",
                f"{summary.turn_limit_games:,}",
            ),
            (
                "Average turns",
                f"{summary.average_turns_started:.3f}",
            ),
            (
                "Average Kinnan activations",
                f"{summary.average_kinnan_activations:.3f}",
            ),
            (
                "Fastest win turn",
                fastest_win_turn,
            ),
            (
                "Total Kinnan activations",
                f"{summary.total_kinnan_activations:,}",
            ),
        )

        rendered_cards = "\n".join(
            "\n".join(
                (
                    '        <article class="metric-card">',
                    f"          <h3>{escape(label)}</h3>",
                    f"          <p>{escape(value)}</p>",
                    "        </article>",
                )
            )
            for label, value in cards
        )

        return "\n".join(
            (
                '    <section aria-labelledby="summary-heading">',
                '      <h2 id="summary-heading">Summary</h2>',
                '      <div class="metric-grid">',
                rendered_cards,
                "      </div>",
                "    </section>",
            )
        )

    def _render_config(
        self,
        result: ExperimentResult,
    ) -> str:
        """
        Render simulation configuration.
        """
        config = result.config

        seed = (
            str(config.seed)
            if config.seed is not None
            else "None"
        )

        rows = (
            (
                "Strategy",
                config.strategy_name,
            ),
            (
                "Games requested",
                f"{config.games:,}",
            ),
            (
                "Maximum turns",
                str(config.max_turns),
            ),
            (
                "Seed",
                seed,
            ),
            (
                "Workers",
                str(config.workers),
            ),
            (
                "Mulligan enabled",
                self._format_boolean(
                    config.mulligan_enabled
                ),
            ),
            (
                "Save replays",
                self._format_boolean(
                    config.save_replays
                ),
            ),
        )

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
                '    <section aria-labelledby="config-heading">',
                '      <h2 id="config-heading">Configuration</h2>',
                '      <div class="table-container">',
                '        <table class="config-table">',
                "          <tbody>",
                rendered_rows,
                "          </tbody>",
                "        </table>",
                "      </div>",
                "    </section>",
            )
        )

    def _render_graphs(
        self,
        graph_data: ExperimentGraphData,
    ) -> str:
        """
        Render all graph-ready experiment distributions.
        """
        return "\n".join(
            (
                '    <section aria-labelledby="graphs-heading">',
                '      <h2 id="graphs-heading">Distributions</h2>',
                '      <div class="graph-grid">',
                self._render_distribution(
                    graph_data.win_turn_distribution,
                    title="Win Turn Distribution",
                    value_label="Turn",
                ),
                self._render_distribution(
                    graph_data.kinnan_activation_distribution,
                    title="Kinnan Activation Distribution",
                    value_label="Activations",
                ),
                "      </div>",
                "    </section>",
            )
        )

    def _render_distribution(
        self,
        distribution: DistributionData,
        *,
        title: str,
        value_label: str,
    ) -> str:
        """
        Render one frequency distribution as a CSS bar chart.
        """
        distribution_id = self._distribution_id(
            distribution.name
        )

        if not distribution.points:
            content = "\n".join(
                (
                    '          <p class="empty-distribution">',
                    "            No observations available.",
                    "          </p>",
                )
            )
        else:
            content = "\n".join(
                self._render_distribution_point(
                    point,
                    value_label=value_label,
                )
                for point in distribution.points
            )

        return "\n".join(
            (
                (
                    '        <article class="distribution-card" '
                    f'data-distribution="{escape(distribution.name)}">'
                ),
                (
                    f'          <h3 id="{distribution_id}-heading">'
                    f"{escape(title)}"
                    "</h3>"
                ),
                (
                    '          <p class="distribution-total">'
                    f"{distribution.total_observations:,} observations"
                    "</p>"
                ),
                (
                    '          <div class="distribution-chart" '
                    f'aria-labelledby="{distribution_id}-heading">'
                ),
                content,
                "          </div>",
                "        </article>",
            )
        )

    @staticmethod
    def _render_distribution_point(
        point: DistributionPoint,
        *,
        value_label: str,
    ) -> str:
        """
        Render one distribution observation as a horizontal bar.
        """
        percentage = point.percentage * 100.0
        escaped_value_label = escape(value_label)

        return "\n".join(
            (
                (
                    '            <div class="distribution-row" '
                    f'data-value="{point.value}">'
                ),
                '              <div class="distribution-label">',
                (
                    "                "
                    f"{escaped_value_label} {point.value}"
                ),
                "              </div>",
                '              <div class="distribution-bar-area">',
                '                <div class="distribution-track">',
                (
                    '                  <div class="distribution-bar" '
                    f'style="width: {percentage:.6f}%">'
                    "</div>"
                ),
                "                </div>",
                "              </div>",
                '              <div class="distribution-count">',
                (
                    "                "
                    f"{point.count:,} ({percentage:.1f}%)"
                ),
                "              </div>",
                "            </div>",
            )
        )

    @staticmethod
    def _distribution_id(
        name: str,
    ) -> str:
        """
        Convert a distribution name into a safe HTML identifier.
        """
        normalized = "".join(
            character
            if character.isalnum()
            else "-"
            for character in name.casefold()
        )

        normalized = normalized.strip("-")

        if not normalized:
            return "distribution"

        return normalized

    def _render_games(
        self,
        result: ExperimentResult,
    ) -> str:
        """
        Render individual Goldfish game results.
        """
        rendered_rows = "\n".join(
            self._render_game_row(
                game_id=game_id,
                result=game_result,
            )
            for game_id, game_result in enumerate(
                result.game_results
            )
        )

        return "\n".join(
            (
                '    <section aria-labelledby="games-heading">',
                '      <h2 id="games-heading">Games</h2>',
                '      <div class="table-container">',
                '        <table class="games-table">',
                "          <thead>",
                "            <tr>",
                '              <th scope="col">Game ID</th>',
                '              <th scope="col">Turns</th>',
                (
                    '              <th scope="col">'
                    "Kinnan activations"
                    "</th>"
                ),
                '              <th scope="col">Turn limit</th>',
                '              <th scope="col">Game over</th>',
                '              <th scope="col">Winner</th>',
                "            </tr>",
                "          </thead>",
                "          <tbody>",
                rendered_rows,
                "          </tbody>",
                "        </table>",
                "      </div>",
                "    </section>",
            )
        )

    @classmethod
    def _render_game_row(
        cls,
        *,
        game_id: int,
        result: GoldfishRunResult,
    ) -> str:
        """
        Render one individual Goldfish game row.
        """
        winner = (
            result.winner
            if result.winner is not None
            else ""
        )

        row_class = (
            "win"
            if result.game_over
            and result.winner is not None
            else "non-win"
        )

        return "\n".join(
            (
                (
                    f'            <tr class="{row_class}" '
                    f'data-game-id="{game_id}">'
                ),
                f"              <td>{game_id}</td>",
                (
                    "              <td>"
                    f"{result.turns_started}"
                    "</td>"
                ),
                (
                    "              <td>"
                    f"{result.kinnan_activations}"
                    "</td>"
                ),
                (
                    "              <td>"
                    f"{cls._format_boolean(result.reached_turn_limit)}"
                    "</td>"
                ),
                (
                    "              <td>"
                    f"{cls._format_boolean(result.game_over)}"
                    "</td>"
                ),
                f"              <td>{escape(winner)}</td>",
                "            </tr>",
            )
        )

    @staticmethod
    def _format_boolean(
        value: bool,
    ) -> str:
        """
        Format a boolean for human-readable HTML output.
        """
        return "Yes" if value else "No"

    @staticmethod
    def _stylesheet() -> str:
        """
        Return the embedded report stylesheet.
        """
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
      width: min(1200px, calc(100% - 32px));
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
    h3,
    p {
      margin-top: 0;
    }

    h1 {
      margin-bottom: 8px;
      font-size: clamp(28px, 5vw, 42px);
    }

    h2 {
      margin-bottom: 18px;
      font-size: 22px;
    }

    .subtitle {
      margin-bottom: 20px;
      color: #5f6b76;
    }

    .win-rate-value {
      margin-bottom: 8px;
      font-size: 32px;
      font-weight: 700;
    }

    .progress-track {
      width: 100%;
      height: 14px;
      overflow: hidden;
      border-radius: 999px;
      background: #e8edf2;
    }

    .progress-value {
      height: 100%;
      border-radius: inherit;
      background: #2f855a;
    }

    .metric-grid {
      display: grid;
      grid-template-columns:
        repeat(auto-fit, minmax(190px, 1fr));
      gap: 14px;
    }

    .metric-card {
      min-height: 112px;
      padding: 16px;
      border: 1px solid #e2e8ee;
      border-radius: 10px;
      background: #fafbfc;
    }

    .metric-card h3 {
      margin-bottom: 12px;
      color: #5f6b76;
      font-size: 14px;
      font-weight: 600;
    }

    .metric-card p {
      margin-bottom: 0;
      font-size: 26px;
      font-weight: 700;
    }

    .graph-grid {
      display: grid;
      grid-template-columns:
        repeat(auto-fit, minmax(320px, 1fr));
      gap: 18px;
    }

    .distribution-card {
      padding: 18px;
      border: 1px solid #e2e8ee;
      border-radius: 10px;
      background: #fafbfc;
    }

    .distribution-card h3 {
      margin-bottom: 6px;
      font-size: 18px;
    }

    .distribution-total {
      margin-bottom: 18px;
      color: #5f6b76;
      font-size: 13px;
    }

    .distribution-chart {
      display: grid;
      gap: 12px;
    }

    .distribution-row {
      display: grid;
      grid-template-columns: 96px minmax(120px, 1fr) 112px;
      gap: 12px;
      align-items: center;
    }

    .distribution-label {
      font-size: 13px;
      font-weight: 600;
      white-space: nowrap;
    }

    .distribution-bar-area {
      min-width: 0;
    }

    .distribution-track {
      width: 100%;
      height: 18px;
      overflow: hidden;
      border-radius: 999px;
      background: #e8edf2;
    }

    .distribution-bar {
      min-width: 2px;
      height: 100%;
      border-radius: inherit;
      background: #2f855a;
    }

    .distribution-count {
      color: #46515c;
      font-size: 13px;
      text-align: right;
      white-space: nowrap;
    }

    .empty-distribution {
      margin-bottom: 0;
      padding: 16px;
      border: 1px dashed #cbd3da;
      border-radius: 8px;
      color: #5f6b76;
      text-align: center;
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
      white-space: nowrap;
    }

    thead th {
      background: #f7f9fb;
      font-size: 13px;
    }

    .config-table th {
      width: 240px;
      color: #5f6b76;
    }

    .games-table tbody tr.win {
      background: #f1fbf5;
    }

    .games-table tbody tr.non-win {
      background: #ffffff;
    }

    .games-table tbody tr:hover {
      background: #edf4fa;
    }

    @media (max-width: 720px) {
      .report {
        width: min(100% - 16px, 1200px);
        margin: 8px auto;
      }

      header,
      section {
        padding: 16px;
        border-radius: 8px;
      }

      .config-table th {
        width: auto;
      }

      .graph-grid {
        grid-template-columns: 1fr;
      }

      .distribution-row {
        grid-template-columns: 86px minmax(100px, 1fr);
      }

      .distribution-count {
        grid-column: 2;
        text-align: left;
      }
    }
""".strip()