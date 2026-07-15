from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile

from krs.report.bundle import ExperimentReportBundlePaths


@dataclass(frozen=True, slots=True)
class ReportArchiveEntry:
    """
    Stores one file included in a report archive.

    source_path is the original filesystem path.
    archive_path is the POSIX-style relative path stored inside the ZIP.
    """

    source_path: Path
    archive_path: PurePosixPath

    def __post_init__(self) -> None:
        if self.archive_path.is_absolute():
            raise ValueError(
                "archive_path must be relative."
            )

        if not self.archive_path.parts:
            raise ValueError(
                "archive_path must not be empty."
            )

        if ".." in self.archive_path.parts:
            raise ValueError(
                "archive_path must not contain parent traversal."
            )


@dataclass(frozen=True, slots=True)
class ExperimentReportArchiveWriter:
    """
    Creates a compressed ZIP archive from an experiment report bundle.

    Existing bundle files are stored relative to the bundle output
    directory. Missing files are skipped unless require_all_files is true.

    An existing report index is included when it is found at
    output_directory / index_filename.
    """

    filename: str = "report.zip"
    index_filename: str = "index.html"
    include_index: bool = True
    require_all_files: bool = False
    compression: int = ZIP_DEFLATED
    compression_level: int | None = 9

    def __post_init__(self) -> None:
        self._validate_plain_filename(
            self.filename,
            field_name="filename",
            allowed_suffixes=(".zip",),
        )
        self._validate_plain_filename(
            self.index_filename,
            field_name="index_filename",
            allowed_suffixes=(
                ".html",
                ".htm",
            ),
        )

        if (
            self.filename.casefold()
            == self.index_filename.casefold()
        ):
            raise ValueError(
                "filename and index_filename must be different."
            )

        if (
            self.compression_level is not None
            and not 0 <= self.compression_level <= 9
        ):
            raise ValueError(
                "compression_level must be between 0 and 9."
            )

    def create_entries(
        self,
        paths: ExperimentReportBundlePaths,
    ) -> tuple[ReportArchiveEntry, ...]:
        """
        Create archive entries in a stable order.

        The report index is placed first when enabled and present, followed
        by ExperimentReportBundlePaths.all_paths.
        """
        output_directory = paths.output_directory

        candidates: list[Path] = []

        if self.include_index:
            candidates.append(
                output_directory
                / self.index_filename
            )

        candidates.extend(paths.all_paths)

        entries: list[ReportArchiveEntry] = []
        seen_archive_paths: set[PurePosixPath] = set()

        for source_path in candidates:
            if not source_path.is_file():
                if self.require_all_files:
                    raise FileNotFoundError(
                        "Required report archive file does not exist: "
                        f"{source_path}"
                    )
                continue

            archive_path = self._relative_archive_path(
                source_path=source_path,
                output_directory=output_directory,
            )

            if archive_path in seen_archive_paths:
                raise ValueError(
                    "Report archive paths must be unique."
                )

            entries.append(
                ReportArchiveEntry(
                    source_path=source_path,
                    archive_path=archive_path,
                )
            )
            seen_archive_paths.add(archive_path)

        return tuple(entries)

    def write(
        self,
        paths: ExperimentReportBundlePaths,
    ) -> Path:
        """
        Create or overwrite the ZIP archive in the bundle directory.
        """
        output_directory = paths.output_directory

        if (
            output_directory.exists()
            and not output_directory.is_dir()
        ):
            raise ValueError(
                "Report archive output path is not a directory: "
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
                "Report archive path is a directory: "
                f"{output_path}"
            )

        entries = self.create_entries(paths)

        with ZipFile(
            output_path,
            mode="w",
            compression=self.compression,
            compresslevel=self.compression_level,
        ) as archive:
            for entry in entries:
                archive.write(
                    filename=entry.source_path,
                    arcname=entry.archive_path.as_posix(),
                )

        return output_path

    @staticmethod
    def _relative_archive_path(
        *,
        source_path: Path,
        output_directory: Path,
    ) -> PurePosixPath:
        """
        Convert a bundle file into a safe POSIX ZIP entry path.
        """
        try:
            relative_path = source_path.relative_to(
                output_directory
            )
        except ValueError as error:
            raise ValueError(
                "Report archive source path must be inside "
                "output_directory."
            ) from error

        archive_path = PurePosixPath(
            *relative_path.parts
        )

        if archive_path.is_absolute():
            raise ValueError(
                "Report archive path must be relative."
            )

        if ".." in archive_path.parts:
            raise ValueError(
                "Report archive path must not contain "
                "parent traversal."
            )

        return archive_path

    @staticmethod
    def _validate_plain_filename(
        filename: str,
        *,
        field_name: str,
        allowed_suffixes: tuple[str, ...],
    ) -> None:
        """
        Validate a filename that must not contain a directory.
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