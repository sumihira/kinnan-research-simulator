from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from krs.replay.replay import Replay
from krs.replay.replay_html import ReplayHtmlReporter
from krs.replay.replay_json import ReplayJsonReporter
from krs.replay.replay_statistics_json import (
    ReplayStatisticsJsonReporter,
)


@dataclass(frozen=True, slots=True)
class ReplayBundlePaths:
    """
    Stores every path generated for one Replay bundle.
    """

    output_directory: Path
    replay_json_path: Path
    statistics_json_path: Path
    replay_html_path: Path

    def __post_init__(self) -> None:
        generated_paths = self.all_paths

        if len(set(generated_paths)) != len(generated_paths):
            raise ValueError(
                "Replay bundle paths must be unique."
            )

        for generated_path in generated_paths:
            if generated_path == self.output_directory:
                raise ValueError(
                    "Generated Replay path must not equal "
                    "output_directory."
                )

            if (
                self.output_directory
                not in generated_path.parents
            ):
                raise ValueError(
                    "Generated Replay paths must be inside "
                    "output_directory."
                )

    @property
    def all_paths(self) -> tuple[Path, ...]:
        """
        Return all generated paths in stable output order.
        """
        return (
            self.replay_json_path,
            self.statistics_json_path,
            self.replay_html_path,
        )

    @property
    def json_paths(self) -> tuple[Path, Path]:
        """
        Return both generated JSON paths.
        """
        return (
            self.replay_json_path,
            self.statistics_json_path,
        )


@dataclass(frozen=True, slots=True)
class ReplayBundleWriter:
    """
    Writes every supported Replay report into one directory.

    The writer is a facade over the existing Replay reporters. It does not
    duplicate serialization, statistics, or HTML-generation logic.
    """

    replay_json_reporter: ReplayJsonReporter = field(
        default_factory=ReplayJsonReporter,
    )
    statistics_json_reporter: (
        ReplayStatisticsJsonReporter
    ) = field(
        default_factory=ReplayStatisticsJsonReporter,
    )
    replay_html_reporter: ReplayHtmlReporter = field(
        default_factory=ReplayHtmlReporter,
    )

    replay_json_filename: str = "replay.json"
    statistics_json_filename: str = "statistics.json"
    replay_html_filename: str = "replay.html"

    def __post_init__(self) -> None:
        self._validate_filename(
            self.replay_json_filename,
            field_name="replay_json_filename",
            allowed_suffixes=(".json",),
        )
        self._validate_filename(
            self.statistics_json_filename,
            field_name="statistics_json_filename",
            allowed_suffixes=(".json",),
        )
        self._validate_filename(
            self.replay_html_filename,
            field_name="replay_html_filename",
            allowed_suffixes=(
                ".html",
                ".htm",
            ),
        )

        normalized_filenames = tuple(
            filename.casefold()
            for filename in (
                self.replay_json_filename,
                self.statistics_json_filename,
                self.replay_html_filename,
            )
        )

        if (
            len(set(normalized_filenames))
            != len(normalized_filenames)
        ):
            raise ValueError(
                "Replay bundle filenames must be unique."
            )

    def write(
        self,
        replay: Replay,
        directory: str | Path,
    ) -> ReplayBundlePaths:
        """
        Write Replay JSON, statistics JSON, and Replay HTML.

        Missing directories are created automatically. Existing output files
        are overwritten by the delegated reporters. Reporter exceptions are
        propagated without modification.
        """
        output_directory = Path(directory)

        if (
            output_directory.exists()
            and not output_directory.is_dir()
        ):
            raise ValueError(
                "Replay bundle output path is not a directory: "
                f"{output_directory}"
            )

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        replay_json_path = (
            output_directory
            / self.replay_json_filename
        )
        statistics_json_path = (
            output_directory
            / self.statistics_json_filename
        )
        replay_html_path = (
            output_directory
            / self.replay_html_filename
        )

        written_replay_json_path = (
            self.replay_json_reporter.write(
                replay,
                replay_json_path,
            )
        )
        written_statistics_json_path = (
            self.statistics_json_reporter.write(
                replay,
                statistics_json_path,
            )
        )
        written_replay_html_path = (
            self.replay_html_reporter.write(
                replay,
                replay_html_path,
            )
        )

        return ReplayBundlePaths(
            output_directory=output_directory,
            replay_json_path=(
                written_replay_json_path
            ),
            statistics_json_path=(
                written_statistics_json_path
            ),
            replay_html_path=(
                written_replay_html_path
            ),
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