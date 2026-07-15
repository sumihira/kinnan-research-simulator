from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path

from krs.replay.replay import Replay
from krs.replay.replay_event import ReplayEvent
from krs.replay.replay_statistics import (
    ReplayCount,
    ReplayStatistics,
)


@dataclass(frozen=True, slots=True)
class ReplayHtmlReporter:
    """
    Creates a standalone HTML report from one Replay.

    The report includes aggregate ReplayStatistics and the complete event
    timeline in insertion order. The supplied Replay is never modified.
    """

    title: str = "Kinnan Research Simulator Replay"

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError(
                "title must not be empty."
            )

    def to_html(
        self,
        replay: Replay,
    ) -> str:
        """
        Convert one Replay into a complete standalone HTML document.
        """
        statistics = ReplayStatistics.from_replay(
            replay
        )

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
                '  <main class="replay-report">',
                self._render_header(statistics),
                self._render_summary(statistics),
                self._render_count_section(
                    title="Action Counts",
                    table_label="Action",
                    counts=statistics.action_counts,
                ),
                self._render_count_section(
                    title="Phase Counts",
                    table_label="Phase",
                    counts=statistics.phase_counts,
                ),
                self._render_timeline(replay),
                "  </main>",
                "</body>",
                "</html>",
                "",
            )
        )

    def write(
        self,
        replay: Replay,
        path: str | Path,
    ) -> Path:
        """
        Write a standalone Replay HTML document using UTF-8 encoding.

        Missing parent directories are created automatically. Existing files
        are overwritten.
        """
        output_path = Path(path)

        if (
            output_path.exists()
            and output_path.is_dir()
        ):
            raise ValueError(
                "Replay HTML path is a directory: "
                f"{output_path}"
            )

        if output_path.suffix.casefold() not in {
            ".html",
            ".htm",
        }:
            raise ValueError(
                "Replay HTML path must use "
                "the .html or .htm extension."
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            self.to_html(replay),
            encoding="utf-8",
        )

        return output_path

    def _render_header(
        self,
        statistics: ReplayStatistics,
    ) -> str:
        """
        Render the report title and a compact Replay description.
        """
        event_word = (
            "event"
            if statistics.event_count == 1
            else "events"
        )
        turn_word = (
            "turn"
            if statistics.turn_count == 1
            else "turns"
        )

        return "\n".join(
            (
                "    <header>",
                f"      <h1>{escape(self.title)}</h1>",
                (
                    '      <p class="subtitle">'
                    f"{statistics.event_count:,} {event_word} "
                    f"across {statistics.turn_count:,} {turn_word}"
                    "</p>"
                ),
                "    </header>",
            )
        )

    @classmethod
    def _render_summary(
        cls,
        statistics: ReplayStatistics,
    ) -> str:
        """
        Render headline Replay statistics.
        """
        max_turn = (
            str(statistics.max_turn)
            if statistics.max_turn is not None
            else "N/A"
        )

        values = (
            (
                "Events",
                f"{statistics.event_count:,}",
            ),
            (
                "Turns represented",
                f"{statistics.turn_count:,}",
            ),
            (
                "Maximum turn",
                max_turn,
            ),
            (
                "Game starts",
                f"{statistics.game_start_count:,}",
            ),
            (
                "Game ends",
                f"{statistics.game_end_count:,}",
            ),
            (
                "Kinnan activations",
                (
                    f"{statistics.action_count('activate_kinnan'):,}"
                ),
            ),
        )

        cards = "\n".join(
            cls._render_summary_card(
                label=label,
                value=value,
            )
            for label, value in values
        )

        return "\n".join(
            (
                (
                    '    <section '
                    'aria-labelledby="summary-heading">'
                ),
                (
                    '      <h2 id="summary-heading">'
                    "Summary"
                    "</h2>"
                ),
                '      <div class="summary-grid">',
                cards,
                "      </div>",
                "    </section>",
            )
        )

    @staticmethod
    def _render_summary_card(
        *,
        label: str,
        value: str,
    ) -> str:
        """
        Render one summary metric card.
        """
        return "\n".join(
            (
                '        <article class="summary-card">',
                (
                    '          <span class="summary-label">'
                    f"{escape(label)}"
                    "</span>"
                ),
                (
                    '          <strong class="summary-value">'
                    f"{escape(value)}"
                    "</strong>"
                ),
                "        </article>",
            )
        )

    @classmethod
    def _render_count_section(
        cls,
        *,
        title: str,
        table_label: str,
        counts: tuple[ReplayCount, ...],
    ) -> str:
        """
        Render Action or Phase count statistics.
        """
        heading_id = (
            title.casefold()
            .replace(" ", "-")
        )

        if not counts:
            content = "\n".join(
                (
                    '      <p class="empty-message">',
                    "        No count data is available.",
                    "      </p>",
                )
            )
        else:
            rows = "\n".join(
                cls._render_count_row(count)
                for count in counts
            )

            content = "\n".join(
                (
                    '      <div class="table-container">',
                    '        <table class="count-table">',
                    "          <thead>",
                    "            <tr>",
                    (
                        '              <th scope="col">'
                        f"{escape(table_label)}"
                        "</th>"
                    ),
                    (
                        '              <th scope="col">'
                        "Count"
                        "</th>"
                    ),
                    "            </tr>",
                    "          </thead>",
                    "          <tbody>",
                    rows,
                    "          </tbody>",
                    "        </table>",
                    "      </div>",
                )
            )

        return "\n".join(
            (
                (
                    "    <section "
                    f'aria-labelledby="{heading_id}">'
                ),
                (
                    f'      <h2 id="{heading_id}">'
                    f"{escape(title)}"
                    "</h2>"
                ),
                content,
                "    </section>",
            )
        )

    @staticmethod
    def _render_count_row(
        count: ReplayCount,
    ) -> str:
        """
        Render one Action or Phase count row.
        """
        return "\n".join(
            (
                "            <tr>",
                (
                    "              <td>"
                    f"{escape(count.name)}"
                    "</td>"
                ),
                (
                    '              <td class="numeric">'
                    f"{count.count:,}"
                    "</td>"
                ),
                "            </tr>",
            )
        )

    @classmethod
    def _render_timeline(
        cls,
        replay: Replay,
    ) -> str:
        """
        Render every ReplayEvent in insertion order.
        """
        if replay.is_empty:
            content = "\n".join(
                (
                    '      <p class="empty-message">',
                    "        No Replay events were recorded.",
                    "      </p>",
                )
            )
        else:
            rows = "\n".join(
                cls._render_event_row(
                    index=index,
                    event=event,
                )
                for index, event in enumerate(
                    replay.events,
                    start=1,
                )
            )

            content = "\n".join(
                (
                    '      <div class="table-container">',
                    '        <table class="timeline-table">',
                    "          <thead>",
                    "            <tr>",
                    '              <th scope="col">#</th>',
                    '              <th scope="col">Turn</th>',
                    '              <th scope="col">Phase</th>',
                    '              <th scope="col">Action</th>',
                    '              <th scope="col">Description</th>',
                    "            </tr>",
                    "          </thead>",
                    "          <tbody>",
                    rows,
                    "          </tbody>",
                    "        </table>",
                    "      </div>",
                )
            )

        return "\n".join(
            (
                (
                    '    <section '
                    'aria-labelledby="timeline-heading">'
                ),
                (
                    '      <h2 id="timeline-heading">'
                    "Event Timeline"
                    "</h2>"
                ),
                content,
                "    </section>",
            )
        )

    @staticmethod
    def _render_event_row(
        *,
        index: int,
        event: ReplayEvent,
    ) -> str:
        """
        Render one ReplayEvent timeline row.
        """
        return "\n".join(
            (
                (
                    "            <tr "
                    f'data-turn="{event.turn}" '
                    f'data-action="{escape(event.action)}">'
                ),
                (
                    '              <td class="numeric">'
                    f"{index:,}"
                    "</td>"
                ),
                (
                    '              <td class="numeric">'
                    f"{event.turn:,}"
                    "</td>"
                ),
                (
                    "              <td>"
                    f"{escape(event.phase)}"
                    "</td>"
                ),
                (
                    "              <td>"
                    f"<code>{escape(event.action)}</code>"
                    "</td>"
                ),
                (
                    "              <td>"
                    f"{escape(event.description)}"
                    "</td>"
                ),
                "            </tr>",
            )
        )

    @staticmethod
    def _stylesheet() -> str:
        """
        Return the embedded Replay report stylesheet.
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

    .replay-report {
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
      margin-bottom: 0;
      color: #5f6b76;
    }

    .summary-grid {
      display: grid;
      grid-template-columns:
        repeat(auto-fit, minmax(160px, 1fr));
      gap: 14px;
    }

    .summary-card {
      padding: 18px;
      border: 1px solid #e2e8ee;
      border-radius: 10px;
      background: #f8fafc;
    }

    .summary-label,
    .summary-value {
      display: block;
    }

    .summary-label {
      margin-bottom: 8px;
      color: #5f6b76;
      font-size: 13px;
    }

    .summary-value {
      font-size: 26px;
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
      vertical-align: top;
    }

    thead th {
      background: #f7f9fb;
      color: #46515c;
      font-size: 13px;
      white-space: nowrap;
    }

    tbody tr:hover {
      background: #f4f8fb;
    }

    .numeric {
      text-align: right;
      white-space: nowrap;
    }

    code {
      padding: 3px 6px;
      border-radius: 5px;
      background: #eef2f6;
      font-family:
        "Cascadia Code",
        Consolas,
        monospace;
      font-size: 13px;
    }

    .empty-message {
      margin-bottom: 0;
      padding: 18px;
      border: 1px dashed #cbd3da;
      border-radius: 8px;
      background: #fafbfc;
      color: #5f6b76;
      text-align: center;
    }

    @media (max-width: 640px) {
      .replay-report {
        width: min(100% - 16px, 1200px);
        margin: 8px auto;
      }

      header,
      section {
        padding: 16px;
        border-radius: 8px;
      }
    }
""".strip()