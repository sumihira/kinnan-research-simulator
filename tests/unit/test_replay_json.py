from __future__ import annotations

import json
from pathlib import Path

import pytest

from krs.replay.replay import Replay
from krs.replay.replay_event import ReplayEvent
from krs.replay.replay_json import ReplayJsonReporter


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
            description=(
                "Player 0 executed draw."
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


def test_to_dict_supports_empty_replay() -> None:
    replay = Replay()

    data = ReplayJsonReporter().to_dict(
        replay
    )

    assert data == {
        "event_count": 0,
        "events": [],
    }


def test_to_dict_contains_event_count() -> None:
    replay = create_replay()

    data = ReplayJsonReporter().to_dict(
        replay
    )

    assert data["event_count"] == 3


def test_to_dict_contains_expected_events() -> None:
    replay = create_replay()

    data = ReplayJsonReporter().to_dict(
        replay
    )

    assert data["events"] == [
        {
            "turn": 1,
            "phase": "untap",
            "action": "game_start",
            "description": (
                "Started game 42 with 1 player(s)."
            ),
        },
        {
            "turn": 1,
            "phase": "draw",
            "action": "draw",
            "description": (
                "Player 0 executed draw."
            ),
        },
        {
            "turn": 3,
            "phase": "main",
            "action": "game_end",
            "description": (
                "Game ended. Winner: Player."
            ),
        },
    ]


def test_to_dict_preserves_event_order() -> None:
    replay = create_replay()

    data = ReplayJsonReporter().to_dict(
        replay
    )

    events = data["events"]

    assert isinstance(events, list)

    assert [
        event["action"]
        for event in events
    ] == [
        "game_start",
        "draw",
        "game_end",
    ]


def test_to_json_returns_valid_json() -> None:
    replay = create_replay()

    json_text = ReplayJsonReporter().to_json(
        replay
    )

    parsed = json.loads(json_text)

    assert parsed["event_count"] == 3
    assert len(parsed["events"]) == 3


def test_to_json_uses_default_indentation() -> None:
    replay = create_replay()

    json_text = ReplayJsonReporter().to_json(
        replay
    )

    assert '\n  "event_count": 3,' in json_text
    assert '\n  "events": [' in json_text
    assert '\n    {' in json_text


def test_to_json_supports_compact_output() -> None:
    replay = create_replay()

    json_text = ReplayJsonReporter(
        indent=None,
    ).to_json(replay)

    assert "\n" not in json_text
    assert json.loads(json_text)[
        "event_count"
    ] == 3


def test_to_json_supports_zero_indent() -> None:
    replay = create_replay()

    json_text = ReplayJsonReporter(
        indent=0,
    ).to_json(replay)

    assert json.loads(json_text)[
        "event_count"
    ] == 3


def test_to_json_preserves_unicode() -> None:
    replay = Replay()
    replay.add(
        create_event(
            description="キナンの能力を起動しました。",
        )
    )

    json_text = ReplayJsonReporter().to_json(
        replay
    )

    assert "キナンの能力を起動しました。" in json_text
    assert "\\u30ad" not in json_text


def test_event_to_dict_returns_expected_data() -> None:
    event = create_event(
        turn=4,
        phase="main",
        action="activate_kinnan",
        description=(
            "Player 0 executed activate_kinnan."
        ),
    )

    data = ReplayJsonReporter._event_to_dict(
        event
    )

    assert data == {
        "turn": 4,
        "phase": "main",
        "action": "activate_kinnan",
        "description": (
            "Player 0 executed activate_kinnan."
        ),
    }


def test_write_creates_json_file(
    tmp_path: Path,
) -> None:
    replay = create_replay()
    reporter = ReplayJsonReporter()
    output_path = tmp_path / "replay.json"

    returned_path = reporter.write(
        replay,
        output_path,
    )

    assert returned_path == output_path
    assert output_path.is_file()

    content = output_path.read_text(
        encoding="utf-8",
    )

    assert content == reporter.to_json(replay)


def test_write_creates_parent_directories(
    tmp_path: Path,
) -> None:
    output_path = (
        tmp_path
        / "replays"
        / "game-001"
        / "replay.json"
    )

    ReplayJsonReporter().write(
        create_replay(),
        output_path,
    )

    assert output_path.is_file()


def test_write_uses_utf_8(
    tmp_path: Path,
) -> None:
    replay = Replay()
    replay.add(
        create_event(
            description="キナンを起動しました。",
        )
    )

    output_path = tmp_path / "replay.json"

    ReplayJsonReporter().write(
        replay,
        output_path,
    )

    content = output_path.read_text(
        encoding="utf-8",
    )

    assert "キナンを起動しました。" in content


def test_write_overwrites_existing_file(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "replay.json"
    output_path.write_text(
        "old content",
        encoding="utf-8",
    )

    ReplayJsonReporter().write(
        create_replay(),
        output_path,
    )

    content = output_path.read_text(
        encoding="utf-8",
    )

    assert content != "old content"
    assert json.loads(content)[
        "event_count"
    ] == 3


@pytest.mark.parametrize(
    "filename",
    (
        "replay.json",
        "REPLAY.JSON",
        "game-replay.json",
    ),
)
def test_write_accepts_json_extension(
    tmp_path: Path,
    filename: str,
) -> None:
    output_path = tmp_path / filename

    ReplayJsonReporter().write(
        create_replay(),
        output_path,
    )

    assert output_path.is_file()


@pytest.mark.parametrize(
    "filename",
    (
        "replay.txt",
        "replay.html",
        "replay",
        "replay.json.txt",
    ),
)
def test_write_rejects_invalid_extension(
    tmp_path: Path,
    filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Replay JSON path must use "
            "the .json extension."
        ),
    ):
        ReplayJsonReporter().write(
            create_replay(),
            tmp_path / filename,
        )


def test_write_rejects_directory_path(
    tmp_path: Path,
) -> None:
    output_directory = (
        tmp_path
        / "replay.json"
    )
    output_directory.mkdir()

    with pytest.raises(
        ValueError,
        match="Replay JSON path is a directory",
    ):
        ReplayJsonReporter().write(
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
        ReplayJsonReporter(
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
    reporter = ReplayJsonReporter(
        indent=indent,
    )

    assert reporter.indent == indent


def test_reporter_is_immutable() -> None:
    reporter = ReplayJsonReporter()

    with pytest.raises(AttributeError):
        reporter.indent = 4  # type: ignore[misc]


def test_to_dict_does_not_modify_replay() -> None:
    replay = create_replay()

    original_events = replay.events
    original_count = replay.event_count

    ReplayJsonReporter().to_dict(replay)

    assert replay.events == original_events
    assert replay.event_count == original_count


def test_to_json_does_not_modify_replay() -> None:
    replay = create_replay()

    original_events = replay.events
    original_count = replay.event_count

    ReplayJsonReporter().to_json(replay)

    assert replay.events == original_events
    assert replay.event_count == original_count


def test_write_does_not_modify_replay(
    tmp_path: Path,
) -> None:
    replay = create_replay()

    original_events = replay.events
    original_count = replay.event_count

    ReplayJsonReporter().write(
        replay,
        tmp_path / "replay.json",
    )

    assert replay.events == original_events
    assert replay.event_count == original_count


def test_serialized_data_is_independent_from_replay() -> None:
    replay = create_replay()

    data = ReplayJsonReporter().to_dict(
        replay
    )

    events = data["events"]

    assert isinstance(events, list)

    events.clear()

    assert replay.event_count == 3
    assert len(replay.events) == 3