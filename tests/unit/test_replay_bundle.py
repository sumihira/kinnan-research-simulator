from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from krs.replay.replay import Replay
from krs.replay.replay_bundle import (
    ReplayBundlePaths,
    ReplayBundleWriter,
)
from krs.replay.replay_event import ReplayEvent
from krs.replay.replay_html import ReplayHtmlReporter
from krs.replay.replay_json import ReplayJsonReporter
from krs.replay.replay_statistics_json import (
    ReplayStatisticsJsonReporter,
)


def create_replay() -> Replay:
    replay = Replay()

    replay.add(
        ReplayEvent(
            turn=1,
            phase="untap",
            action="game_start",
            description=(
                "Started game 42 with 1 player(s)."
            ),
        )
    )
    replay.add(
        ReplayEvent(
            turn=1,
            phase="draw",
            action="draw",
            description=(
                "Player 0 executed draw."
            ),
        )
    )
    replay.add(
        ReplayEvent(
            turn=2,
            phase="main",
            action="activate_kinnan",
            description=(
                "Player 0 executed activate_kinnan."
            ),
        )
    )
    replay.add(
        ReplayEvent(
            turn=3,
            phase="main",
            action="game_end",
            description=(
                "Game ended. Winner: Player."
            ),
        )
    )

    return replay


def create_bundle_paths(
    output_directory: Path,
) -> ReplayBundlePaths:
    return ReplayBundlePaths(
        output_directory=output_directory,
        replay_json_path=(
            output_directory
            / "replay.json"
        ),
        statistics_json_path=(
            output_directory
            / "statistics.json"
        ),
        replay_html_path=(
            output_directory
            / "replay.html"
        ),
    )


def test_write_creates_all_replay_files(
    tmp_path: Path,
) -> None:
    replay = create_replay()

    paths = ReplayBundleWriter().write(
        replay,
        tmp_path,
    )

    assert paths == create_bundle_paths(
        tmp_path
    )
    assert paths.output_directory == tmp_path
    assert paths.replay_json_path.is_file()
    assert paths.statistics_json_path.is_file()
    assert paths.replay_html_path.is_file()


def test_write_creates_missing_output_directory(
    tmp_path: Path,
) -> None:
    output_directory = (
        tmp_path
        / "replays"
        / "game-0001"
    )

    paths = ReplayBundleWriter().write(
        create_replay(),
        output_directory,
    )

    assert output_directory.is_dir()
    assert paths.replay_json_path.is_file()
    assert paths.statistics_json_path.is_file()
    assert paths.replay_html_path.is_file()


def test_write_supports_existing_output_directory(
    tmp_path: Path,
) -> None:
    output_directory = tmp_path / "existing"
    output_directory.mkdir()

    marker_path = output_directory / "marker.txt"
    marker_path.write_text(
        "keep",
        encoding="utf-8",
    )

    paths = ReplayBundleWriter().write(
        create_replay(),
        output_directory,
    )

    assert marker_path.read_text(
        encoding="utf-8",
    ) == "keep"
    assert len(paths.all_paths) == 3


def test_written_replay_json_contains_events(
    tmp_path: Path,
) -> None:
    paths = ReplayBundleWriter().write(
        create_replay(),
        tmp_path,
    )

    data = json.loads(
        paths.replay_json_path.read_text(
            encoding="utf-8",
        )
    )

    assert data["event_count"] == 4
    assert [
        event["action"]
        for event in data["events"]
    ] == [
        "game_start",
        "draw",
        "activate_kinnan",
        "game_end",
    ]


def test_written_statistics_json_contains_counts(
    tmp_path: Path,
) -> None:
    paths = ReplayBundleWriter().write(
        create_replay(),
        tmp_path,
    )

    data = json.loads(
        paths.statistics_json_path.read_text(
            encoding="utf-8",
        )
    )

    assert data["event_count"] == 4
    assert data["turn_count"] == 3
    assert data["max_turn"] == 3
    assert data["game_start_count"] == 1
    assert data["game_end_count"] == 1
    assert data["action_counts"][
        "activate_kinnan"
    ] == 1


def test_written_html_contains_timeline(
    tmp_path: Path,
) -> None:
    paths = ReplayBundleWriter().write(
        create_replay(),
        tmp_path,
    )

    html = paths.replay_html_path.read_text(
        encoding="utf-8",
    )

    assert html.startswith("<!DOCTYPE html>")
    assert "Event Timeline" in html
    assert "<code>game_start</code>" in html
    assert "<code>activate_kinnan</code>" in html
    assert "<code>game_end</code>" in html


def test_write_supports_empty_replay(
    tmp_path: Path,
) -> None:
    paths = ReplayBundleWriter().write(
        Replay(),
        tmp_path,
    )

    replay_data = json.loads(
        paths.replay_json_path.read_text(
            encoding="utf-8",
        )
    )
    statistics_data = json.loads(
        paths.statistics_json_path.read_text(
            encoding="utf-8",
        )
    )
    html = paths.replay_html_path.read_text(
        encoding="utf-8",
    )

    assert replay_data == {
        "event_count": 0,
        "events": [],
    }
    assert statistics_data[
        "event_count"
    ] == 0
    assert statistics_data[
        "max_turn"
    ] is None
    assert (
        "No Replay events were recorded."
        in html
    )


def test_write_uses_custom_filenames(
    tmp_path: Path,
) -> None:
    writer = ReplayBundleWriter(
        replay_json_filename="events.json",
        statistics_json_filename="summary.json",
        replay_html_filename="viewer.htm",
    )

    paths = writer.write(
        create_replay(),
        tmp_path,
    )

    assert paths.replay_json_path == (
        tmp_path
        / "events.json"
    )
    assert paths.statistics_json_path == (
        tmp_path
        / "summary.json"
    )
    assert paths.replay_html_path == (
        tmp_path
        / "viewer.htm"
    )

    assert all(
        path.is_file()
        for path in paths.all_paths
    )


def test_write_delegates_to_all_reporters(
    tmp_path: Path,
) -> None:
    replay = create_replay()

    replay_json_reporter = Mock(
        spec=ReplayJsonReporter,
    )
    statistics_json_reporter = Mock(
        spec=ReplayStatisticsJsonReporter,
    )
    replay_html_reporter = Mock(
        spec=ReplayHtmlReporter,
    )

    replay_json_path = (
        tmp_path
        / "replay.json"
    )
    statistics_json_path = (
        tmp_path
        / "statistics.json"
    )
    replay_html_path = (
        tmp_path
        / "replay.html"
    )

    replay_json_reporter.write.return_value = (
        replay_json_path
    )
    statistics_json_reporter.write.return_value = (
        statistics_json_path
    )
    replay_html_reporter.write.return_value = (
        replay_html_path
    )

    writer = ReplayBundleWriter(
        replay_json_reporter=(
            replay_json_reporter
        ),
        statistics_json_reporter=(
            statistics_json_reporter
        ),
        replay_html_reporter=(
            replay_html_reporter
        ),
    )

    paths = writer.write(
        replay,
        tmp_path,
    )

    replay_json_reporter.write.assert_called_once_with(
        replay,
        replay_json_path,
    )
    statistics_json_reporter.write.assert_called_once_with(
        replay,
        statistics_json_path,
    )
    replay_html_reporter.write.assert_called_once_with(
        replay,
        replay_html_path,
    )

    assert paths == create_bundle_paths(
        tmp_path
    )


def test_reporters_are_called_in_stable_order(
    tmp_path: Path,
) -> None:
    replay = create_replay()
    calls: list[str] = []

    replay_json_reporter = Mock(
        spec=ReplayJsonReporter,
    )
    statistics_json_reporter = Mock(
        spec=ReplayStatisticsJsonReporter,
    )
    replay_html_reporter = Mock(
        spec=ReplayHtmlReporter,
    )

    def write_replay_json(
        current_replay: Replay,
        path: Path,
    ) -> Path:
        assert current_replay is replay
        calls.append("replay_json")
        return path

    def write_statistics_json(
        current_replay: Replay,
        path: Path,
    ) -> Path:
        assert current_replay is replay
        calls.append("statistics_json")
        return path

    def write_replay_html(
        current_replay: Replay,
        path: Path,
    ) -> Path:
        assert current_replay is replay
        calls.append("replay_html")
        return path

    replay_json_reporter.write.side_effect = (
        write_replay_json
    )
    statistics_json_reporter.write.side_effect = (
        write_statistics_json
    )
    replay_html_reporter.write.side_effect = (
        write_replay_html
    )

    ReplayBundleWriter(
        replay_json_reporter=(
            replay_json_reporter
        ),
        statistics_json_reporter=(
            statistics_json_reporter
        ),
        replay_html_reporter=(
            replay_html_reporter
        ),
    ).write(
        replay,
        tmp_path,
    )

    assert calls == [
        "replay_json",
        "statistics_json",
        "replay_html",
    ]


@pytest.mark.parametrize(
    (
        "reporter_field",
        "error_message",
    ),
    (
        (
            "replay_json_reporter",
            "Replay JSON failed.",
        ),
        (
            "statistics_json_reporter",
            "Statistics JSON failed.",
        ),
        (
            "replay_html_reporter",
            "Replay HTML failed.",
        ),
    ),
)
def test_write_propagates_reporter_exception(
    tmp_path: Path,
    reporter_field: str,
    error_message: str,
) -> None:
    replay_json_reporter = Mock(
        spec=ReplayJsonReporter,
    )
    statistics_json_reporter = Mock(
        spec=ReplayStatisticsJsonReporter,
    )
    replay_html_reporter = Mock(
        spec=ReplayHtmlReporter,
    )

    replay_json_reporter.write.side_effect = (
        lambda replay, path: path
    )
    statistics_json_reporter.write.side_effect = (
        lambda replay, path: path
    )
    replay_html_reporter.write.side_effect = (
        lambda replay, path: path
    )

    reporters = {
        "replay_json_reporter": (
            replay_json_reporter
        ),
        "statistics_json_reporter": (
            statistics_json_reporter
        ),
        "replay_html_reporter": (
            replay_html_reporter
        ),
    }

    reporters[
        reporter_field
    ].write.side_effect = RuntimeError(
        error_message
    )

    writer = ReplayBundleWriter(
        replay_json_reporter=(
            replay_json_reporter
        ),
        statistics_json_reporter=(
            statistics_json_reporter
        ),
        replay_html_reporter=(
            replay_html_reporter
        ),
    )

    with pytest.raises(
        RuntimeError,
        match=error_message,
    ):
        writer.write(
            create_replay(),
            tmp_path,
        )


def test_write_rejects_file_as_output_directory(
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "existing.txt"
    output_file.write_text(
        "content",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Replay bundle output path is not "
            "a directory"
        ),
    ):
        ReplayBundleWriter().write(
            create_replay(),
            output_file,
        )


def test_bundle_paths_all_paths_are_stable() -> None:
    output_directory = Path("replays/game-0001")
    paths = create_bundle_paths(
        output_directory
    )

    assert paths.all_paths == (
        output_directory / "replay.json",
        output_directory / "statistics.json",
        output_directory / "replay.html",
    )


def test_bundle_paths_json_paths_are_stable() -> None:
    output_directory = Path("replays/game-0001")
    paths = create_bundle_paths(
        output_directory
    )

    assert paths.json_paths == (
        output_directory / "replay.json",
        output_directory / "statistics.json",
    )


def test_bundle_paths_reject_duplicate_paths(
    tmp_path: Path,
) -> None:
    duplicate_path = tmp_path / "replay.json"

    with pytest.raises(
        ValueError,
        match=(
            "Replay bundle paths must be unique."
        ),
    ):
        ReplayBundlePaths(
            output_directory=tmp_path,
            replay_json_path=duplicate_path,
            statistics_json_path=duplicate_path,
            replay_html_path=(
                tmp_path
                / "replay.html"
            ),
        )


def test_bundle_paths_reject_output_directory_as_path(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Generated Replay path must not equal "
            "output_directory."
        ),
    ):
        ReplayBundlePaths(
            output_directory=tmp_path,
            replay_json_path=tmp_path,
            statistics_json_path=(
                tmp_path
                / "statistics.json"
            ),
            replay_html_path=(
                tmp_path
                / "replay.html"
            ),
        )


def test_bundle_paths_reject_outside_path(
    tmp_path: Path,
) -> None:
    output_directory = (
        tmp_path
        / "replays"
    )

    with pytest.raises(
        ValueError,
        match=(
            "Generated Replay paths must be inside "
            "output_directory."
        ),
    ):
        ReplayBundlePaths(
            output_directory=output_directory,
            replay_json_path=(
                tmp_path
                / "outside.json"
            ),
            statistics_json_path=(
                output_directory
                / "statistics.json"
            ),
            replay_html_path=(
                output_directory
                / "replay.html"
            ),
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "overrides",
    ),
    (
        (
            "replay_json_filename",
            {
                "replay_json_filename": "",
            },
        ),
        (
            "statistics_json_filename",
            {
                "statistics_json_filename": " ",
            },
        ),
        (
            "replay_html_filename",
            {
                "replay_html_filename": "\t",
            },
        ),
    ),
)
def test_writer_rejects_empty_filename(
    field_name: str,
    overrides: dict[str, str],
) -> None:
    with pytest.raises(
        ValueError,
        match=rf"{field_name} must not be empty.",
    ):
        ReplayBundleWriter(
            **overrides,
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "overrides",
    ),
    (
        (
            "replay_json_filename",
            {
                "replay_json_filename": (
                    "data/replay.json"
                ),
            },
        ),
        (
            "statistics_json_filename",
            {
                "statistics_json_filename": (
                    "data/statistics.json"
                ),
            },
        ),
        (
            "replay_html_filename",
            {
                "replay_html_filename": (
                    "html/replay.html"
                ),
            },
        ),
    ),
)
def test_writer_rejects_directory_in_filename(
    field_name: str,
    overrides: dict[str, str],
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            rf"{field_name} must not contain "
            r"a directory."
        ),
    ):
        ReplayBundleWriter(
            **overrides,
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "overrides",
    ),
    (
        (
            "replay_json_filename",
            {
                "replay_json_filename": (
                    "replay.txt"
                ),
            },
        ),
        (
            "statistics_json_filename",
            {
                "statistics_json_filename": (
                    "statistics.txt"
                ),
            },
        ),
        (
            "replay_html_filename",
            {
                "replay_html_filename": (
                    "replay.txt"
                ),
            },
        ),
    ),
)
def test_writer_rejects_invalid_extension(
    field_name: str,
    overrides: dict[str, str],
) -> None:
    with pytest.raises(
        ValueError,
        match=rf"{field_name} must use the",
    ):
        ReplayBundleWriter(
            **overrides,
        )


def test_writer_rejects_duplicate_filenames() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Replay bundle filenames must be unique."
        ),
    ):
        ReplayBundleWriter(
            replay_json_filename="replay.json",
            statistics_json_filename="REPLAY.JSON",
        )


def test_bundle_paths_are_immutable(
    tmp_path: Path,
) -> None:
    paths = create_bundle_paths(tmp_path)

    with pytest.raises(
        FrozenInstanceError,
    ):
        paths.replay_json_path = (  # type: ignore[misc]
            tmp_path
            / "changed.json"
        )


def test_bundle_writer_is_immutable() -> None:
    writer = ReplayBundleWriter()

    with pytest.raises(
        FrozenInstanceError,
    ):
        writer.replay_json_filename = (  # type: ignore[misc]
            "changed.json"
        )


def test_write_does_not_modify_replay(
    tmp_path: Path,
) -> None:
    replay = create_replay()
    original_events = replay.events
    original_count = replay.event_count

    ReplayBundleWriter().write(
        replay,
        tmp_path,
    )

    assert replay.events == original_events
    assert replay.event_count == original_count
    assert all(
        current is original
        for current, original in zip(
            replay.events,
            original_events,
            strict=True,
        )
    )