from __future__ import annotations

from pathlib import Path

import pytest

from krs.report.bundle import ExperimentReportBundlePaths
from krs.report.report_index import (
    ReportIndexEntry,
    ReportIndexWriter,
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


def create_all_report_files(
    paths: ExperimentReportBundlePaths,
) -> None:
    paths.output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    for path in paths.all_paths:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_text(
            f"content: {path.name}",
            encoding="utf-8",
        )


def test_create_entries_returns_all_existing_reports(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_all_report_files(paths)

    entries = ReportIndexWriter().create_entries(
        paths
    )

    assert len(entries) == 9
    assert all(
        entry.path.is_file()
        for entry in entries
    )


def test_create_entries_preserves_stable_order(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_all_report_files(paths)

    entries = ReportIndexWriter().create_entries(
        paths
    )

    assert tuple(
        entry.path
        for entry in entries
    ) == (
        paths.html_path,
        paths.analysis_html_path,
        paths.summary_markdown_path,
        paths.analysis_markdown_path,
        paths.json_path,
        paths.analysis_json_path,
        paths.excel_path,
        paths.csv_summary_path,
        paths.csv_games_path,
    )


def test_create_entries_contains_expected_categories(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_all_report_files(paths)

    entries = ReportIndexWriter().create_entries(
        paths
    )

    assert tuple(
        entry.category
        for entry in entries
    ) == (
        "HTML",
        "HTML",
        "Markdown",
        "Markdown",
        "JSON",
        "JSON",
        "Excel",
        "CSV",
        "CSV",
    )


def test_create_entries_contains_expected_labels(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_all_report_files(paths)

    entries = ReportIndexWriter().create_entries(
        paths
    )

    assert tuple(
        entry.label
        for entry in entries
    ) == (
        "Experiment Report",
        "Statistical Analysis",
        "Experiment Summary",
        "Statistical Analysis",
        "Experiment Data",
        "Statistical Analysis",
        "Experiment Workbook",
        "Summary Table",
        "Individual Games",
    )


def test_create_entries_excludes_missing_files(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)

    paths.output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.html_path.write_text(
        "html",
        encoding="utf-8",
    )
    paths.summary_markdown_path.write_text(
        "markdown",
        encoding="utf-8",
    )

    entries = ReportIndexWriter().create_entries(
        paths
    )

    assert tuple(
        entry.path
        for entry in entries
    ) == (
        paths.html_path,
        paths.summary_markdown_path,
    )


def test_create_entries_include_missing_returns_all_reports(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)

    entries = ReportIndexWriter(
        include_missing=True,
    ).create_entries(paths)

    assert len(entries) == 9
    assert tuple(
        entry.path
        for entry in entries
    ) == (
        paths.html_path,
        paths.analysis_html_path,
        paths.summary_markdown_path,
        paths.analysis_markdown_path,
        paths.json_path,
        paths.analysis_json_path,
        paths.excel_path,
        paths.csv_summary_path,
        paths.csv_games_path,
    )


def test_to_html_returns_complete_document(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_all_report_files(paths)

    html = ReportIndexWriter().to_html(paths)

    assert html.startswith("<!DOCTYPE html>")
    assert '<html lang="en">' in html
    assert '<meta charset="utf-8">' in html
    assert "</body>" in html
    assert html.endswith("</html>\n")


def test_to_html_contains_default_title(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_all_report_files(paths)

    html = ReportIndexWriter().to_html(paths)

    assert (
        "<title>Kinnan Research Simulator Reports</title>"
        in html
    )
    assert (
        "<h1>Kinnan Research Simulator Reports</h1>"
        in html
    )


def test_to_html_contains_custom_title(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_all_report_files(paths)

    html = ReportIndexWriter(
        title="KRS Report Library",
    ).to_html(paths)

    assert "<title>KRS Report Library</title>" in html
    assert "<h1>KRS Report Library</h1>" in html


def test_to_html_contains_report_count(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_all_report_files(paths)

    html = ReportIndexWriter().to_html(paths)

    assert "9 reports available" in html


def test_to_html_uses_singular_report_count(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)

    paths.output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.html_path.write_text(
        "html",
        encoding="utf-8",
    )

    html = ReportIndexWriter().to_html(paths)

    assert "1 report available" in html
    assert "1 reports available" not in html


def test_to_html_contains_all_relative_links(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_all_report_files(paths)

    html = ReportIndexWriter().to_html(paths)

    expected_links = (
        'href="experiment.html"',
        'href="analysis.html"',
        'href="summary.md"',
        'href="analysis.md"',
        'href="experiment.json"',
        'href="analysis.json"',
        'href="experiment.xlsx"',
        'href="csv/summary.csv"',
        'href="csv/games.csv"',
    )

    for expected_link in expected_links:
        assert expected_link in html


def test_to_html_displays_relative_file_paths(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_all_report_files(paths)

    html = ReportIndexWriter().to_html(paths)

    assert ">experiment.html<" in html
    assert ">analysis.html<" in html
    assert ">summary.md<" in html
    assert ">analysis.md<" in html
    assert ">experiment.json<" in html
    assert ">analysis.json<" in html
    assert ">experiment.xlsx<" in html
    assert ">csv/summary.csv<" in html
    assert ">csv/games.csv<" in html


def test_to_html_contains_expected_table_headers(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_all_report_files(paths)

    html = ReportIndexWriter().to_html(paths)

    assert '<th scope="col">Category</th>' in html
    assert '<th scope="col">Report</th>' in html
    assert '<th scope="col">File</th>' in html
    assert '<th scope="col">Action</th>' in html


def test_to_html_contains_open_links(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_all_report_files(paths)

    html = ReportIndexWriter().to_html(paths)

    assert html.count(
        'class="open-link"'
    ) == 9
    assert html.count(">Open</a>") == 9


def test_to_html_contains_category_attributes(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_all_report_files(paths)

    html = ReportIndexWriter().to_html(paths)

    assert html.count(
        'data-category="HTML"'
    ) == 2
    assert html.count(
        'data-category="Markdown"'
    ) == 2
    assert html.count(
        'data-category="JSON"'
    ) == 2
    assert html.count(
        'data-category="Excel"'
    ) == 1
    assert html.count(
        'data-category="CSV"'
    ) == 2


def test_to_html_renders_empty_state(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)

    html = ReportIndexWriter().to_html(paths)

    assert "0 reports available" in html
    assert (
        "No report files are currently available."
        in html
    )
    assert 'class="empty-message"' in html
    assert '<table class="report-table">' not in html


def test_to_html_include_missing_does_not_render_empty_state(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)

    html = ReportIndexWriter(
        include_missing=True,
    ).to_html(paths)

    assert "9 reports available" in html
    assert (
        "No report files are currently available."
        not in html
    )
    assert '<table class="report-table">' in html


def test_title_is_html_escaped(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)

    html = ReportIndexWriter(
        title="<script>alert('x')</script>",
        include_missing=True,
    ).to_html(paths)

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_render_entry_escapes_category_and_label(
    tmp_path: Path,
) -> None:
    entry = ReportIndexEntry(
        category="<HTML>",
        label="Report & Analysis",
        path=tmp_path / "report.html",
    )

    html = ReportIndexWriter._render_entry(
        entry=entry,
        output_directory=tmp_path,
    )

    assert 'data-category="&lt;HTML&gt;"' in html
    assert "&lt;HTML&gt;" in html
    assert "Report &amp; Analysis" in html
    assert "<HTML>" not in html


def test_render_entry_url_encodes_spaces(
    tmp_path: Path,
) -> None:
    entry = ReportIndexEntry(
        category="HTML",
        label="Experiment Report",
        path=(
            tmp_path
            / "experiment report.html"
        ),
    )

    html = ReportIndexWriter._render_entry(
        entry=entry,
        output_directory=tmp_path,
    )

    assert (
        'href="experiment%20report.html"'
        in html
    )
    assert ">experiment report.html<" in html


def test_render_entry_url_encodes_unicode(
    tmp_path: Path,
) -> None:
    entry = ReportIndexEntry(
        category="HTML",
        label="日本語レポート",
        path=tmp_path / "解析結果.html",
    )

    html = ReportIndexWriter._render_entry(
        entry=entry,
        output_directory=tmp_path,
    )

    assert (
        'href="%E8%A7%A3%E6%9E%90'
        '%E7%B5%90%E6%9E%9C.html"'
        in html
    )
    assert ">解析結果.html<" in html
    assert "日本語レポート" in html


def test_render_entry_preserves_relative_subdirectories(
    tmp_path: Path,
) -> None:
    entry = ReportIndexEntry(
        category="CSV",
        label="Summary Table",
        path=(
            tmp_path
            / "csv exports"
            / "summary result.csv"
        ),
    )

    html = ReportIndexWriter._render_entry(
        entry=entry,
        output_directory=tmp_path,
    )

    assert (
        'href="csv%20exports/summary%20result.csv"'
        in html
    )
    assert (
        ">csv exports/summary result.csv<"
        in html
    )


def test_entry_relative_path_returns_expected_path(
    tmp_path: Path,
) -> None:
    entry = ReportIndexEntry(
        category="CSV",
        label="Games",
        path=tmp_path / "csv" / "games.csv",
    )

    assert entry.relative_path(tmp_path) == (
        Path("csv")
        / "games.csv"
    )


def test_entry_relative_path_rejects_path_outside_directory(
    tmp_path: Path,
) -> None:
    output_directory = tmp_path / "reports"

    entry = ReportIndexEntry(
        category="JSON",
        label="Outside",
        path=tmp_path / "outside.json",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Report index entry path must be inside "
            "output_directory."
        ),
    ):
        entry.relative_path(output_directory)


def test_create_entries_rejects_bundle_path_outside_directory(
    tmp_path: Path,
) -> None:
    output_directory = tmp_path / "reports"

    paths = ExperimentReportBundlePaths(
        output_directory=output_directory,
        json_path=output_directory / "experiment.json",
        analysis_json_path=(
            output_directory
            / "analysis.json"
        ),
        html_path=output_directory / "experiment.html",
        analysis_html_path=(
            output_directory
            / "analysis.html"
        ),
        excel_path=output_directory / "experiment.xlsx",
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

    entries = ReportIndexWriter(
        include_missing=True,
    ).create_entries(paths)

    assert len(entries) == 9


def test_write_creates_index_html(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_all_report_files(paths)

    output_path = ReportIndexWriter().write(paths)

    assert output_path == tmp_path / "index.html"
    assert output_path.is_file()

    content = output_path.read_text(
        encoding="utf-8",
    )

    assert content == ReportIndexWriter().to_html(
        paths
    )


def test_write_supports_custom_filename(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_all_report_files(paths)

    output_path = ReportIndexWriter(
        filename="reports.htm",
    ).write(paths)

    assert output_path == tmp_path / "reports.htm"
    assert output_path.is_file()


def test_write_creates_missing_output_directory(
    tmp_path: Path,
) -> None:
    output_directory = (
        tmp_path
        / "reports"
        / "latest"
    )
    paths = create_bundle_paths(output_directory)

    output_path = ReportIndexWriter(
        include_missing=True,
    ).write(paths)

    assert output_directory.is_dir()
    assert output_path.is_file()


def test_write_overwrites_existing_index_file(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_all_report_files(paths)

    output_path = tmp_path / "index.html"
    output_path.write_text(
        "old content",
        encoding="utf-8",
    )

    ReportIndexWriter().write(paths)

    content = output_path.read_text(
        encoding="utf-8",
    )

    assert content != "old content"
    assert content.startswith("<!DOCTYPE html>")


def test_write_rejects_output_directory_that_is_file(
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "reports"
    output_file.write_text(
        "content",
        encoding="utf-8",
    )

    paths = create_bundle_paths(output_file)

    with pytest.raises(
        ValueError,
        match=(
            "Report index output path is not "
            "a directory"
        ),
    ):
        ReportIndexWriter(
            include_missing=True,
        ).write(paths)


def test_write_rejects_index_path_that_is_directory(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    index_directory = tmp_path / "index.html"
    index_directory.mkdir()

    with pytest.raises(
        ValueError,
        match="Report index path is a directory",
    ):
        ReportIndexWriter(
            include_missing=True,
        ).write(paths)


@pytest.mark.parametrize(
    "filename",
    (
        "index.html",
        "index.htm",
        "INDEX.HTML",
        "INDEX.HTM",
    ),
)
def test_writer_accepts_html_filenames(
    filename: str,
) -> None:
    writer = ReportIndexWriter(
        filename=filename,
    )

    assert writer.filename == filename


@pytest.mark.parametrize(
    "filename",
    (
        "",
        " ",
        "\t",
        "\n",
    ),
)
def test_writer_rejects_empty_filename(
    filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="filename must not be empty.",
    ):
        ReportIndexWriter(
            filename=filename,
        )


@pytest.mark.parametrize(
    "filename",
    (
        "reports/index.html",
        "reports\\index.html",
    ),
)
def test_writer_rejects_directory_in_filename(
    filename: str,
) -> None:
    expected_message = (
        "filename must not contain a directory."
        if Path(filename).name != filename
        else (
            "filename must use the .html "
            "or .htm extension."
        )
    )

    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        ReportIndexWriter(
            filename=filename,
        )


@pytest.mark.parametrize(
    "filename",
    (
        "index.txt",
        "index.json",
        "index",
    ),
)
def test_writer_rejects_invalid_filename_extension(
    filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "filename must use the .html "
            "or .htm extension."
        ),
    ):
        ReportIndexWriter(
            filename=filename,
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
def test_writer_rejects_empty_title(
    title: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="title must not be empty.",
    ):
        ReportIndexWriter(
            title=title,
        )


@pytest.mark.parametrize(
    (
        "category",
        "label",
        "expected_message",
    ),
    (
        (
            "",
            "Report",
            "category must not be empty.",
        ),
        (
            " ",
            "Report",
            "category must not be empty.",
        ),
        (
            "HTML",
            "",
            "label must not be empty.",
        ),
        (
            "HTML",
            "\t",
            "label must not be empty.",
        ),
    ),
)
def test_entry_rejects_empty_presentation_values(
    category: str,
    label: str,
    expected_message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        ReportIndexEntry(
            category=category,
            label=label,
            path=Path("report.html"),
        )


def test_entry_is_immutable() -> None:
    entry = ReportIndexEntry(
        category="HTML",
        label="Experiment",
        path=Path("experiment.html"),
    )

    with pytest.raises(AttributeError):
        entry.label = "Changed"  # type: ignore[misc]


def test_writer_is_immutable() -> None:
    writer = ReportIndexWriter()

    with pytest.raises(AttributeError):
        writer.title = "Changed"  # type: ignore[misc]