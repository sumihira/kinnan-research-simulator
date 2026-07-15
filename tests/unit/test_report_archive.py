from __future__ import annotations

from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from krs.report.bundle import ExperimentReportBundlePaths
from krs.report.report_archive import (
    ExperimentReportArchiveWriter,
    ReportArchiveEntry,
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


def create_report_files(
    paths: ExperimentReportBundlePaths,
    *,
    include_index: bool = True,
) -> None:
    paths.output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    if include_index:
        (
            paths.output_directory
            / "index.html"
        ).write_text(
            "index content",
            encoding="utf-8",
        )

    for report_path in paths.all_paths:
        report_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        report_path.write_text(
            f"content: {report_path.name}",
            encoding="utf-8",
        )


def read_archive_names(
    archive_path: Path,
) -> tuple[str, ...]:
    with ZipFile(
        archive_path,
        mode="r",
    ) as archive:
        return tuple(archive.namelist())


def test_create_entries_returns_index_and_bundle_files(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_report_files(paths)

    entries = (
        ExperimentReportArchiveWriter()
        .create_entries(paths)
    )

    assert len(entries) == 10
    assert entries[0].source_path == (
        tmp_path
        / "index.html"
    )
    assert entries[0].archive_path == PurePosixPath(
        "index.html"
    )


def test_create_entries_preserves_stable_order(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_report_files(paths)

    entries = (
        ExperimentReportArchiveWriter()
        .create_entries(paths)
    )

    assert tuple(
        entry.archive_path.as_posix()
        for entry in entries
    ) == (
        "index.html",
        "experiment.json",
        "analysis.json",
        "experiment.html",
        "analysis.html",
        "experiment.xlsx",
        "summary.md",
        "analysis.md",
        "csv/summary.csv",
        "csv/games.csv",
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
        "summary",
        encoding="utf-8",
    )

    entries = (
        ExperimentReportArchiveWriter()
        .create_entries(paths)
    )

    assert tuple(
        entry.archive_path.as_posix()
        for entry in entries
    ) == (
        "experiment.html",
        "summary.md",
    )


def test_create_entries_excludes_missing_index(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_report_files(
        paths,
        include_index=False,
    )

    entries = (
        ExperimentReportArchiveWriter()
        .create_entries(paths)
    )

    assert len(entries) == 9
    assert all(
        entry.archive_path
        != PurePosixPath("index.html")
        for entry in entries
    )


def test_create_entries_can_exclude_existing_index(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_report_files(paths)

    entries = ExperimentReportArchiveWriter(
        include_index=False,
    ).create_entries(paths)

    assert len(entries) == 9
    assert all(
        entry.archive_path
        != PurePosixPath("index.html")
        for entry in entries
    )


def test_create_entries_requires_all_bundle_files(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)

    with pytest.raises(
        FileNotFoundError,
        match=(
            "Required report archive file "
            "does not exist"
        ),
    ):
        ExperimentReportArchiveWriter(
            include_index=False,
            require_all_files=True,
        ).create_entries(paths)


def test_create_entries_requires_index_when_enabled(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_report_files(
        paths,
        include_index=False,
    )

    with pytest.raises(
        FileNotFoundError,
        match=(
            "Required report archive file "
            "does not exist"
        ),
    ):
        ExperimentReportArchiveWriter(
            include_index=True,
            require_all_files=True,
        ).create_entries(paths)


def test_create_entries_does_not_require_index_when_disabled(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_report_files(
        paths,
        include_index=False,
    )

    entries = ExperimentReportArchiveWriter(
        include_index=False,
        require_all_files=True,
    ).create_entries(paths)

    assert len(entries) == 9


def test_write_creates_zip_file(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_report_files(paths)

    output_path = (
        ExperimentReportArchiveWriter()
        .write(paths)
    )

    assert output_path == (
        tmp_path
        / "report.zip"
    )
    assert output_path.is_file()


def test_written_archive_contains_expected_files(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_report_files(paths)

    archive_path = (
        ExperimentReportArchiveWriter()
        .write(paths)
    )

    assert read_archive_names(archive_path) == (
        "index.html",
        "experiment.json",
        "analysis.json",
        "experiment.html",
        "analysis.html",
        "experiment.xlsx",
        "summary.md",
        "analysis.md",
        "csv/summary.csv",
        "csv/games.csv",
    )


def test_written_archive_preserves_file_contents(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_report_files(paths)

    archive_path = (
        ExperimentReportArchiveWriter()
        .write(paths)
    )

    with ZipFile(
        archive_path,
        mode="r",
    ) as archive:
        assert archive.read(
            "index.html"
        ).decode("utf-8") == "index content"

        assert archive.read(
            "experiment.json"
        ).decode("utf-8") == (
            "content: experiment.json"
        )

        assert archive.read(
            "csv/games.csv"
        ).decode("utf-8") == (
            "content: games.csv"
        )


def test_written_archive_uses_deflate_compression(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_report_files(paths)

    archive_path = (
        ExperimentReportArchiveWriter()
        .write(paths)
    )

    with ZipFile(
        archive_path,
        mode="r",
    ) as archive:
        assert all(
            info.compress_type == ZIP_DEFLATED
            for info in archive.infolist()
        )


def test_write_supports_custom_archive_filename(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_report_files(paths)

    output_path = ExperimentReportArchiveWriter(
        filename="experiment-results.zip",
    ).write(paths)

    assert output_path == (
        tmp_path
        / "experiment-results.zip"
    )
    assert output_path.is_file()


def test_write_supports_custom_index_filename(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_report_files(
        paths,
        include_index=False,
    )

    custom_index_path = (
        tmp_path
        / "reports.htm"
    )
    custom_index_path.write_text(
        "custom index",
        encoding="utf-8",
    )

    archive_path = ExperimentReportArchiveWriter(
        index_filename="reports.htm",
    ).write(paths)

    with ZipFile(
        archive_path,
        mode="r",
    ) as archive:
        assert archive.namelist()[0] == "reports.htm"
        assert archive.read(
            "reports.htm"
        ).decode("utf-8") == "custom index"


def test_write_skips_missing_files(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)

    paths.output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.json_path.write_text(
        "json",
        encoding="utf-8",
    )
    paths.csv_games_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.csv_games_path.write_text(
        "games",
        encoding="utf-8",
    )

    archive_path = (
        ExperimentReportArchiveWriter()
        .write(paths)
    )

    assert read_archive_names(archive_path) == (
        "experiment.json",
        "csv/games.csv",
    )


def test_write_can_create_empty_archive(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)

    archive_path = (
        ExperimentReportArchiveWriter()
        .write(paths)
    )

    assert archive_path.is_file()
    assert read_archive_names(archive_path) == ()


def test_write_creates_missing_output_directory(
    tmp_path: Path,
) -> None:
    output_directory = (
        tmp_path
        / "reports"
        / "latest"
    )
    paths = create_bundle_paths(output_directory)

    archive_path = (
        ExperimentReportArchiveWriter()
        .write(paths)
    )

    assert output_directory.is_dir()
    assert archive_path.is_file()


def test_write_overwrites_existing_archive(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)
    create_report_files(paths)

    archive_path = tmp_path / "report.zip"
    archive_path.write_bytes(
        b"old archive content"
    )

    returned_path = (
        ExperimentReportArchiveWriter()
        .write(paths)
    )

    assert returned_path == archive_path
    assert returned_path.read_bytes() != (
        b"old archive content"
    )

    assert "experiment.json" in read_archive_names(
        returned_path
    )


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
            "Report archive output path is not "
            "a directory"
        ),
    ):
        ExperimentReportArchiveWriter().write(
            paths
        )


def test_write_rejects_archive_path_that_is_directory(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)

    archive_directory = (
        tmp_path
        / "report.zip"
    )
    archive_directory.mkdir(
        parents=True,
    )

    with pytest.raises(
        ValueError,
        match="Report archive path is a directory",
    ):
        ExperimentReportArchiveWriter().write(
            paths
        )


def test_relative_archive_path_returns_posix_path(
    tmp_path: Path,
) -> None:
    source_path = (
        tmp_path
        / "csv"
        / "games.csv"
    )

    archive_path = (
        ExperimentReportArchiveWriter
        ._relative_archive_path(
            source_path=source_path,
            output_directory=tmp_path,
        )
    )

    assert archive_path == PurePosixPath(
        "csv/games.csv"
    )
    assert archive_path.as_posix() == (
        "csv/games.csv"
    )


def test_relative_archive_path_supports_unicode(
    tmp_path: Path,
) -> None:
    source_path = (
        tmp_path
        / "解析結果"
        / "ゲーム.csv"
    )

    archive_path = (
        ExperimentReportArchiveWriter
        ._relative_archive_path(
            source_path=source_path,
            output_directory=tmp_path,
        )
    )

    assert archive_path == PurePosixPath(
        "解析結果/ゲーム.csv"
    )


def test_relative_archive_path_rejects_outside_path(
    tmp_path: Path,
) -> None:
    output_directory = (
        tmp_path
        / "reports"
    )
    outside_path = (
        tmp_path
        / "outside.json"
    )

    with pytest.raises(
        ValueError,
        match=(
            "Report archive source path must be "
            "inside output_directory."
        ),
    ):
        (
            ExperimentReportArchiveWriter
            ._relative_archive_path(
                source_path=outside_path,
                output_directory=output_directory,
            )
        )


def test_written_archive_supports_unicode_filename(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)

    unicode_path = (
        tmp_path
        / "解析結果.html"
    )
    unicode_path.write_text(
        "日本語コンテンツ",
        encoding="utf-8",
    )

    entry = ReportArchiveEntry(
        source_path=unicode_path,
        archive_path=PurePosixPath(
            "解析結果.html"
        ),
    )

    archive_path = (
        tmp_path
        / "unicode.zip"
    )

    with ZipFile(
        archive_path,
        mode="w",
        compression=ZIP_DEFLATED,
    ) as archive:
        archive.write(
            filename=entry.source_path,
            arcname=entry.archive_path.as_posix(),
        )

    with ZipFile(
        archive_path,
        mode="r",
    ) as archive:
        assert archive.namelist() == [
            "解析結果.html",
        ]
        assert archive.read(
            "解析結果.html"
        ).decode("utf-8") == (
            "日本語コンテンツ"
        )

    assert paths.output_directory == tmp_path


@pytest.mark.parametrize(
    "filename",
    (
        "report.zip",
        "REPORT.ZIP",
        "experiment-results.zip",
    ),
)
def test_writer_accepts_zip_filename(
    filename: str,
) -> None:
    writer = ExperimentReportArchiveWriter(
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
def test_writer_rejects_empty_archive_filename(
    filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="filename must not be empty.",
    ):
        ExperimentReportArchiveWriter(
            filename=filename,
        )


@pytest.mark.parametrize(
    "filename",
    (
        "reports/report.zip",
        "archives/report.zip",
    ),
)
def test_writer_rejects_directory_in_archive_filename(
    filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "filename must not contain a directory."
        ),
    ):
        ExperimentReportArchiveWriter(
            filename=filename,
        )


@pytest.mark.parametrize(
    "filename",
    (
        "report.tar",
        "report.gz",
        "report",
    ),
)
def test_writer_rejects_invalid_archive_extension(
    filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "filename must use the .zip extension."
        ),
    ):
        ExperimentReportArchiveWriter(
            filename=filename,
        )


@pytest.mark.parametrize(
    "index_filename",
    (
        "index.html",
        "index.htm",
        "INDEX.HTML",
    ),
)
def test_writer_accepts_html_index_filename(
    index_filename: str,
) -> None:
    writer = ExperimentReportArchiveWriter(
        index_filename=index_filename,
    )

    assert writer.index_filename == index_filename


@pytest.mark.parametrize(
    "index_filename",
    (
        "",
        " ",
        "\t",
        "\n",
    ),
)
def test_writer_rejects_empty_index_filename(
    index_filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="index_filename must not be empty.",
    ):
        ExperimentReportArchiveWriter(
            index_filename=index_filename,
        )


@pytest.mark.parametrize(
    "index_filename",
    (
        "reports/index.html",
        "pages/index.htm",
    ),
)
def test_writer_rejects_directory_in_index_filename(
    index_filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "index_filename must not contain "
            "a directory."
        ),
    ):
        ExperimentReportArchiveWriter(
            index_filename=index_filename,
        )


@pytest.mark.parametrize(
    "index_filename",
    (
        "index.txt",
        "index.json",
        "index",
    ),
)
def test_writer_rejects_invalid_index_extension(
    index_filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "index_filename must use the "
            ".html or .htm extension."
        ),
    ):
        ExperimentReportArchiveWriter(
            index_filename=index_filename,
        )


def test_writer_rejects_zip_extension_for_index_filename() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "index_filename must use the "
            ".html or .htm extension."
        ),
    ):
        ExperimentReportArchiveWriter(
            filename="report.zip",
            index_filename="REPORT.ZIP",
        )


@pytest.mark.parametrize(
    "compression_level",
    (
        -1,
        10,
        100,
    ),
)
def test_writer_rejects_invalid_compression_level(
    compression_level: int,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "compression_level must be between "
            "0 and 9."
        ),
    ):
        ExperimentReportArchiveWriter(
            compression_level=compression_level,
        )


def test_writer_accepts_none_compression_level() -> None:
    writer = ExperimentReportArchiveWriter(
        compression_level=None,
    )

    assert writer.compression_level is None


def test_archive_entry_accepts_relative_path(
    tmp_path: Path,
) -> None:
    entry = ReportArchiveEntry(
        source_path=tmp_path / "report.html",
        archive_path=PurePosixPath(
            "report.html"
        ),
    )

    assert entry.source_path == (
        tmp_path
        / "report.html"
    )
    assert entry.archive_path == PurePosixPath(
        "report.html"
    )


def test_archive_entry_rejects_absolute_path(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="archive_path must be relative.",
    ):
        ReportArchiveEntry(
            source_path=tmp_path / "report.html",
            archive_path=PurePosixPath(
                "/report.html"
            ),
        )


def test_archive_entry_rejects_parent_traversal(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "archive_path must not contain "
            "parent traversal."
        ),
    ):
        ReportArchiveEntry(
            source_path=tmp_path / "report.html",
            archive_path=PurePosixPath(
                "../report.html"
            ),
        )


def test_archive_entry_is_immutable(
    tmp_path: Path,
) -> None:
    entry = ReportArchiveEntry(
        source_path=tmp_path / "report.html",
        archive_path=PurePosixPath(
            "report.html"
        ),
    )

    with pytest.raises(AttributeError):
        entry.archive_path = (  # type: ignore[misc]
            PurePosixPath("changed.html")
        )


def test_archive_writer_is_immutable() -> None:
    writer = ExperimentReportArchiveWriter()

    with pytest.raises(AttributeError):
        writer.filename = "changed.zip"  # type: ignore[misc]