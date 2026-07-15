from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from pathlib import Path

import pytest

from krs.replay.replay import Replay
from krs.replay.replay_event import ReplayEvent
from krs.replay.replay_statistics import (
    ReplayStatistics,
)
from krs.replay.replay_statistics_json import (
    ReplayStatisticsJsonReporter,
)


def create_event(
    *,
    turn: int = 1,
    phase: str = "main",
    action: str = "draw",
    description: str = "Player 0 executed draw.",
) -> ReplayEvent:
    return ReplayEvent(
        turn=turn,
        phase=phase,
        action=action,
        description=description,
    )


def create_replay() -> Replay:
    replay = Replay()

    replay.add(
        create_event(
            turn=1,
            phase="untap",
            action="game_start",
            description=(
                "Started game 42 with 1 player(s)."
            ),
        )
    )
    replay.add(
        create_event(
            turn=1,
            phase="draw",
            action="draw",
        )
    )
    replay.add(
        create_event(
            turn=1,
            phase="main",
            action="cast_spell",
            description=(
                "Player 0 executed cast_spell."
            ),
        )
    )
    replay.add(
        create_event(
            turn=2,
            phase="draw",
            action="draw",
        )
    )
    replay.add(
        create_event(
            turn=2,
            phase="main",
            action="activate_kinnan",
            description=(
                "Player 0 executed activate_kinnan."
            ),
        )
    )
    replay.add(
        create_event(
            turn=3,
            phase="main",
            action="game_end",
            description=(
                "Game ended. Winner: Player."
            ),
        )
    )

    return replay


def expected_data() -> dict[
    str,
    int | None | dict[str, int],
]:
    return {
        "event_count": 6,
        "turn_count": 3,
        "max_turn": 3,
        "game_start_count": 1,
        "game_end_count": 1,
        "action_counts": {
            "activate_kinnan": 1,
            "cast_spell": 1,
            "draw": 2,
            "game_end": 1,
            "game_start": 1,
        },
        "phase_counts": {
            "draw": 2,
            "main": 3,
            "untap": 1,
        },
    }


def test_to_dict_supports_empty_replay() -> None:
    data = ReplayStatisticsJsonReporter().to_dict(
        Replay()
    )

    assert data == {
        "event_count": 0,
        "turn_count": 0,
        "max_turn": None,
        "game_start_count": 0,
        "game_end_count": 0,
        "action_counts": {},
        "phase_counts": {},
    }


def test_to_dict_returns_expected_data() -> None:
    data = ReplayStatisticsJsonReporter().to_dict(
        create_replay()
    )

    assert data == expected_data()


def test_statistics_to_dict_returns_expected_data() -> None:
    replay = create_replay()
    statistics = ReplayStatistics.from_replay(
        replay
    )

    data = (
        ReplayStatisticsJsonReporter()
        .statistics_to_dict(statistics)
    )

    assert data == expected_data()


def test_action_counts_preserve_sorted_order() -> None:
    data = ReplayStatisticsJsonReporter().to_dict(
        create_replay()
    )

    action_counts = data["action_counts"]

    assert isinstance(
        action_counts,
        dict,
    )
    assert tuple(action_counts) == (
        "activate_kinnan",
        "cast_spell",
        "draw",
        "game_end",
        "game_start",
    )


def test_phase_counts_preserve_sorted_order() -> None:
    data = ReplayStatisticsJsonReporter().to_dict(
        create_replay()
    )

    phase_counts = data["phase_counts"]

    assert isinstance(
        phase_counts,
        dict,
    )
    assert tuple(phase_counts) == (
        "draw",
        "main",
        "untap",
    )


def test_to_json_returns_valid_json() -> None:
    json_text = ReplayStatisticsJsonReporter().to_json(
        create_replay()
    )

    assert json.loads(json_text) == expected_data()


def test_statistics_to_json_returns_valid_json() -> None:
    statistics = ReplayStatistics.from_replay(
        create_replay()
    )

    json_text = (
        ReplayStatisticsJsonReporter()
        .statistics_to_json(statistics)
    )

    assert json.loads(json_text) == expected_data()


def test_to_json_uses_default_indentation() -> None:
    json_text = ReplayStatisticsJsonReporter().to_json(
        create_replay()
    )

    assert '\n  "event_count": 6,' in json_text
    assert '\n  "action_counts": {' in json_text
    assert '\n    "draw": 2,' in json_text


def test_to_json_supports_compact_output() -> None:
    json_text = ReplayStatisticsJsonReporter(
        indent=None,
    ).to_json(create_replay())

    assert "\n" not in json_text
    assert json.loads(json_text) == expected_data()


def test_to_json_supports_zero_indent() -> None:
    json_text = ReplayStatisticsJsonReporter(
        indent=0,
    ).to_json(create_replay())

    assert json.loads(json_text) == expected_data()


def test_write_creates_json_file(
    tmp_path: Path,
) -> None:
    replay = create_replay()
    reporter = ReplayStatisticsJsonReporter()
    output_path = (
        tmp_path
        / "replay-statistics.json"
    )

    returned_path = reporter.write(
        replay,
        output_path,
    )

    assert returned_path == output_path
    assert output_path.is_file()
    assert output_path.read_text(
        encoding="utf-8",
    ) == reporter.to_json(replay)


def test_write_statistics_creates_json_file(
    tmp_path: Path,
) -> None:
    statistics = ReplayStatistics.from_replay(
        create_replay()
    )
    reporter = ReplayStatisticsJsonReporter()
    output_path = (
        tmp_path
        / "replay-statistics.json"
    )

    returned_path = reporter.write_statistics(
        statistics,
        output_path,
    )

    assert returned_path == output_path
    assert json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    ) == expected_data()


def test_write_creates_parent_directories(
    tmp_path: Path,
) -> None:
    output_path = (
        tmp_path
        / "replays"
        / "game-001"
        / "statistics.json"
    )

    ReplayStatisticsJsonReporter().write(
        create_replay(),
        output_path,
    )

    assert output_path.is_file()


def test_write_overwrites_existing_file(
    tmp_path: Path,
) -> None:
    output_path = (
        tmp_path
        / "statistics.json"
    )
    output_path.write_text(
        "old content",
        encoding="utf-8",
    )

    ReplayStatisticsJsonReporter().write(
        create_replay(),
        output_path,
    )

    content = output_path.read_text(
        encoding="utf-8",
    )

    assert content != "old content"
    assert json.loads(content) == expected_data()


@pytest.mark.parametrize(
    "filename",
    (
        "statistics.json",
        "STATISTICS.JSON",
        "replay-statistics.json",
    ),
)
def test_write_accepts_json_extension(
    tmp_path: Path,
    filename: str,
) -> None:
    output_path = tmp_path / filename

    ReplayStatisticsJsonReporter().write(
        create_replay(),
        output_path,
    )

    assert output_path.is_file()


@pytest.mark.parametrize(
    "filename",
    (
        "statistics.txt",
        "statistics.html",
        "statistics",
        "statistics.json.txt",
    ),
)
def test_write_rejects_invalid_extension(
    tmp_path: Path,
    filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Replay statistics JSON path must use "
            "the .json extension."
        ),
    ):
        ReplayStatisticsJsonReporter().write(
            create_replay(),
            tmp_path / filename,
        )


def test_write_statistics_rejects_invalid_extension(
    tmp_path: Path,
) -> None:
    statistics = ReplayStatistics.from_replay(
        create_replay()
    )

    with pytest.raises(
        ValueError,
        match=(
            "Replay statistics JSON path must use "
            "the .json extension."
        ),
    ):
        (
            ReplayStatisticsJsonReporter()
            .write_statistics(
                statistics,
                tmp_path / "statistics.txt",
            )
        )


def test_write_rejects_directory_path(
    tmp_path: Path,
) -> None:
    output_directory = (
        tmp_path
        / "statistics.json"
    )
    output_directory.mkdir()

    with pytest.raises(
        ValueError,
        match=(
            "Replay statistics JSON path "
            "is a directory"
        ),
    ):
        ReplayStatisticsJsonReporter().write(
            create_replay(),
            output_directory,
        )


@pytest.mark.parametrize(
    "indent",
    (
        -1,
        -2,
        -100,
    ),
)
def test_reporter_rejects_negative_indent(
    indent: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="indent must not be negative.",
    ):
        ReplayStatisticsJsonReporter(
            indent=indent,
        )


@pytest.mark.parametrize(
    "indent",
    (
        None,
        0,
        1,
        2,
        4,
    ),
)
def test_reporter_accepts_valid_indent(
    indent: int | None,
) -> None:
    reporter = ReplayStatisticsJsonReporter(
        indent=indent,
    )

    assert reporter.indent == indent


def test_reporter_is_immutable() -> None:
    reporter = ReplayStatisticsJsonReporter()

    with pytest.raises(
        FrozenInstanceError,
    ):
        reporter.indent = 4  # type: ignore[misc]


def test_to_dict_does_not_modify_replay() -> None:
    replay = create_replay()
    original_events = replay.events
    original_count = replay.event_count

    ReplayStatisticsJsonReporter().to_dict(
        replay
    )

    assert replay.events == original_events
    assert replay.event_count == original_count


def test_to_json_does_not_modify_replay() -> None:
    replay = create_replay()
    original_events = replay.events
    original_count = replay.event_count

    ReplayStatisticsJsonReporter().to_json(
        replay
    )

    assert replay.events == original_events
    assert replay.event_count == original_count


def test_statistics_to_dict_does_not_modify_statistics() -> None:
    statistics = ReplayStatistics.from_replay(
        create_replay()
    )

    original_actions = statistics.action_counts
    original_phases = statistics.phase_counts

    (
        ReplayStatisticsJsonReporter()
        .statistics_to_dict(statistics)
    )

    assert (
        statistics.action_counts
        is original_actions
    )
    assert (
        statistics.phase_counts
        is original_phases
    )


def test_serialized_data_is_independent() -> None:
    replay = create_replay()

    data = ReplayStatisticsJsonReporter().to_dict(
        replay
    )

    action_counts = data["action_counts"]

    assert isinstance(
        action_counts,
        dict,
    )

    action_counts.clear()

    statistics = ReplayStatistics.from_replay(
        replay
    )

    assert statistics.action_count(
        "draw"
    ) == 2
    assert replay.event_count == 6