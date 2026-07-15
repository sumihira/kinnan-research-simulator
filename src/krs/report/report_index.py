from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from urllib.parse import quote

from krs.report.bundle import ExperimentReportBundlePaths


@dataclass(frozen=True, slots=True)
class ReportIndexEntry:
    """
    Stores one report link displayed in the report index.

    path is the generated report's filesystem path. category and label are
    human-readable presentation values.
    """

    category: str
    label: str
    path: Path

    def __post_init__(self) -> None:
        if not self.category.strip():
            raise ValueError(
                "category must not be empty."
            )

        if not self.label.strip():
            raise ValueError(
                "label must not be empty."
            )

    def relative_path(
        self,
        output_directory: Path,
    ) -> Path:
        """
        Return this report path relative to the bundle directory.
        """
        try:
            return self.path.relative_to(
                output_directory
            )
        except ValueError as error:
            raise ValueError(
                "Report index entry path must be inside "
                "output_directory."
            ) from error


@dataclass(frozen=True, slots=True)
class ReportIndexWriter:
    """
    Creates a standalone HTML index for an experiment report bundle.

    Only files that currently exist are included. The index contains relative
    links so the entire bundle directory can be moved without breaking links.
    """

    title: str = "Kinnan Research Simulator Reports"
    filename: str = "index.html"
    include_missing: bool = False

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError(
                "title must not be empty."
            )

        if not self.filename.strip():
            raise ValueError(
                "filename must not be empty."
            )

        filename_path = Path(self.filename)

        if filename_path.name != self.filename:
            raise ValueError(
                "filename must not contain a directory."
            )

        if filename_path.suffix.casefold() not in {
            ".html",
            ".htm",
        }:
            raise ValueError(
                "filename must use the .html or .htm extension."
            )

    def create_entries(
        self,
        paths: ExperimentReportBundlePaths,
    ) -> tuple[ReportIndexEntry, ...]:
        """
        Create report index entries in stable presentation order.

        Missing files are excluded unless include_missing is enabled.
        """
        candidates = (
            ReportIndexEntry(
                category="HTML",
                label="Experiment Report",
                path=paths.html_path,
            ),
            ReportIndexEntry(
                category="HTML",
                label="Statistical Analysis",
                path=paths.analysis_html_path,
            ),
            ReportIndexEntry(
                category="Markdown",
                label="Experiment Summary",
                path=paths.summary_markdown_path,
            ),
            ReportIndexEntry(
                category="Markdown",
                label="Statistical Analysis",
                path=paths.analysis_markdown_path,
            ),
            ReportIndexEntry(
                category="JSON",
                label="Experiment Data",
                path=paths.json_path,
            ),
            ReportIndexEntry(
                category="JSON",
                label="Statistical Analysis",
                path=paths.analysis_json_path,
            ),
            ReportIndexEntry(
                category="Excel",
                label="Experiment Workbook",
                path=paths.excel_path,
            ),
            ReportIndexEntry(
                category="CSV",
                label="Summary Table",
                path=paths.csv_summary_path,
            ),
            ReportIndexEntry(
                category="CSV",
                label="Individual Games",
                path=paths.csv_games_path,
            ),
        )

        for entry in candidates:
            entry.relative_path(
                paths.output_directory
            )

        if self.include_missing:
            return candidates

        return tuple(
            entry
            for entry in candidates
            if entry.path.is_file()
        )

    def to_html(
        self,
        paths: ExperimentReportBundlePaths,
    ) -> str:
        """
        Create a complete standalone HTML index document.
        """
        entries = self.create_entries(paths)

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
                '  <main class="report-index">',
                self._render_header(
                    report_count=len(entries),
                ),
                self._render_entries(
                    entries=entries,
                    output_directory=paths.output_directory,
                ),
                "  </main>",
                "</body>",
                "</html>",
                "",
            )
        )

    def write(
        self,
        paths: ExperimentReportBundlePaths,
    ) -> Path:
        """
        Write the report index into the bundle output directory.
        """
        output_directory = paths.output_directory

        if (
            output_directory.exists()
            and not output_directory.is_dir()
        ):
            raise ValueError(
                "Report index output path is not a directory: "
                f"{output_directory}"
            )

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            output_directory
            / self.filename
        )

        if output_path.exists() and output_path.is_dir():
            raise ValueError(
                "Report index path is a directory: "
                f"{output_path}"
            )

        output_path.write_text(
            self.to_html(paths),
            encoding="utf-8",
        )

        return output_path

    def _render_header(
        self,
        *,
        report_count: int,
    ) -> str:
        """
        Render the page heading and report count.
        """
        report_word = (
            "report"
            if report_count == 1
            else "reports"
        )

        return "\n".join(
            (
                "    <header>",
                f"      <h1>{escape(self.title)}</h1>",
                (
                    '      <p class="subtitle">'
                    f"{report_count:,} {report_word} available"
                    "</p>"
                ),
                "    </header>",
            )
        )

    def _render_entries(
        self,
        *,
        entries: tuple[ReportIndexEntry, ...],
        output_directory: Path,
    ) -> str:
        """
        Render the report list or an empty-state message.
        """
        if not entries:
            return "\n".join(
                (
                    (
                        '    <section '
                        'aria-labelledby="reports-heading">'
                    ),
                    (
                        '      <h2 id="reports-heading">'
                        "Available Reports"
                        "</h2>"
                    ),
                    '      <p class="empty-message">',
                    "        No report files are currently available.",
                    "      </p>",
                    "    </section>",
                )
            )

        rendered_rows = "\n".join(
            self._render_entry(
                entry=entry,
                output_directory=output_directory,
            )
            for entry in entries
        )

        return "\n".join(
            (
                (
                    '    <section '
                    'aria-labelledby="reports-heading">'
                ),
                (
                    '      <h2 id="reports-heading">'
                    "Available Reports"
                    "</h2>"
                ),
                '      <div class="table-container">',
                '        <table class="report-table">',
                "          <thead>",
                "            <tr>",
                '              <th scope="col">Category</th>',
                '              <th scope="col">Report</th>',
                '              <th scope="col">File</th>',
                '              <th scope="col">Action</th>',
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

    @staticmethod
    def _render_entry(
        *,
        entry: ReportIndexEntry,
        output_directory: Path,
    ) -> str:
        """
        Render one report-link table row.
        """
        relative_path = entry.relative_path(
            output_directory
        )

        relative_path_text = relative_path.as_posix()
        encoded_href = quote(
            relative_path_text,
            safe="/",
        )

        return "\n".join(
            (
                (
                    '            <tr '
                    f'data-category="{escape(entry.category)}">'
                ),
                (
                    "              <td>"
                    f"{escape(entry.category)}"
                    "</td>"
                ),
                (
                    "              <td>"
                    f"{escape(entry.label)}"
                    "</td>"
                ),
                (
                    '              <td class="file-path">'
                    f"{escape(relative_path_text)}"
                    "</td>"
                ),
                "              <td>",
                (
                    '                <a class="open-link" '
                    f'href="{escape(encoded_href)}">'
                    "Open"
                    "</a>"
                ),
                "              </td>",
                "            </tr>",
            )
        )

    @staticmethod
    def _stylesheet() -> str:
        """
        Return the embedded report-index stylesheet.
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

    .report-index {
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

    h2 {
      margin-bottom: 18px;
      font-size: 22px;
    }

    .subtitle {
      margin-bottom: 0;
      color: #5f6b76;
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
      padding: 13px 12px;
      border-bottom: 1px solid #e2e8ee;
      text-align: left;
      white-space: nowrap;
    }

    thead th {
      background: #f7f9fb;
      color: #46515c;
      font-size: 13px;
    }

    tbody tr:hover {
      background: #f4f8fb;
    }

    .file-path {
      color: #5f6b76;
      font-family:
        "Cascadia Code",
        Consolas,
        monospace;
      font-size: 13px;
    }

    .open-link {
      display: inline-block;
      padding: 7px 13px;
      border-radius: 7px;
      background: #1f4e78;
      color: #ffffff;
      font-weight: 600;
      text-decoration: none;
    }

    .open-link:hover {
      background: #163b5d;
    }

    .open-link:focus-visible {
      outline: 3px solid #90cdf4;
      outline-offset: 2px;
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
      .report-index {
        width: min(100% - 16px, 1100px);
        margin: 8px auto;
      }

      header,
      section {
        padding: 16px;
        border-radius: 8px;
      }
    }
""".strip()