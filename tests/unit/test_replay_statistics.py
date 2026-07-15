from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from krs.replay.replay import Replay
from krs.replay.replay_event import ReplayEvent
from krs.replay.replay_statistics import (
    ReplayCount,
    ReplayStatistics,
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


def create_statistics() -> ReplayStatistics:
    return ReplayStatistics.from_replay(
        create_replay()
    )


def test_from_replay_supports_empty_replay() -> None:
    statistics = ReplayStatistics.from_replay(
        Replay()
    )

    assert statistics.event_count == 0
    assert statistics.turn_count == 0
    assert statistics.max_turn is None
    assert statistics.game_start_count == 0
    assert statistics.game_end_count == 0
    assert statistics.action_counts == ()
    assert statistics.phase_counts == ()


def test_from_replay_calculates_event_count() -> None:
    statistics = create_statistics()

    assert statistics.event_count == 6


def test_from_replay_calculates_distinct_turn_count() -> None:
    statistics = create_statistics()

    assert statistics.turn_count == 3


def test_from_replay_calculates_max_turn() -> None:
    statistics = create_statistics()

    assert statistics.max_turn == 3


def test_from_replay_calculates_game_start_count() -> None:
    statistics = create_statistics()

    assert statistics.game_start_count == 1


def test_from_replay_calculates_game_end_count() -> None:
    statistics = create_statistics()

    assert statistics.game_end_count == 1


def test_from_replay_calculates_action_counts() -> None:
    statistics = create_statistics()

    assert statistics.action_counts == (
        ReplayCount(
            name="activate_kinnan",
            count=1,
        ),
        ReplayCount(
            name="cast_spell",
            count=1,
        ),
        ReplayCount(
            name="draw",
            count=2,
        ),
        ReplayCount(
            name="game_end",
            count=1,
        ),
        ReplayCount(
            name="game_start",
            count=1,
        ),
    )


def test_from_replay_calculates_phase_counts() -> None:
    statistics = create_statistics()

    assert statistics.phase_counts == (
        ReplayCount(
            name="draw",
            count=2,
        ),
        ReplayCount(
            name="main",
            count=3,
        ),
        ReplayCount(
            name="untap",
            count=1,
        ),
    )


@pytest.mark.parametrize(
    (
        "action",
        "expected",
    ),
    (
        (
            "game_start",
            1,
        ),
        (
            "draw",
            2,
        ),
        (
            "cast_spell",
            1,
        ),
        (
            "activate_kinnan",
            1,
        ),
        (
            "game_end",
            1,
        ),
        (
            "unknown_action",
            0,
        ),
    ),
)
def test_action_count_returns_expected_value(
    action: str,
    expected: int,
) -> None:
    statistics = create_statistics()

    assert statistics.action_count(
        action
    ) == expected


@pytest.mark.parametrize(
    (
        "phase",
        "expected",
    ),
    (
        (
            "untap",
            1,
        ),
        (
            "draw",
            2,
        ),
        (
            "main",
            3,
        ),
        (
            "unknown_phase",
            0,
        ),
    ),
)
def test_phase_count_returns_expected_value(
    phase: str,
    expected: int,
) -> None:
    statistics = create_statistics()

    assert statistics.phase_count(
        phase
    ) == expected


def test_action_count_strips_surrounding_whitespace() -> None:
    statistics = create_statistics()

    assert statistics.action_count(
        "  draw  "
    ) == 2


def test_phase_count_strips_surrounding_whitespace() -> None:
    statistics = create_statistics()

    assert statistics.phase_count(
        "  main  "
    ) == 3


@pytest.mark.parametrize(
    "action",
    (
        "",
        " ",
        "\t",
        "\n",
    ),
)
def test_action_count_rejects_empty_name(
    action: str,
) -> None:
    statistics = create_statistics()

    with pytest.raises(
        ValueError,
        match="action must not be empty.",
    ):
        statistics.action_count(action)


@pytest.mark.parametrize(
    "phase",
    (
        "",
        " ",
        "\t",
        "\n",
    ),
)
def test_phase_count_rejects_empty_name(
    phase: str,
) -> None:
    statistics = create_statistics()

    with pytest.raises(
        ValueError,
        match="phase must not be empty.",
    ):
        statistics.phase_count(phase)


def test_statistics_are_independent_of_event_order() -> None:
    first_replay = create_replay()
    second_replay = Replay()

    second_replay.extend(
        reversed(first_replay.events)
    )

    first = ReplayStatistics.from_replay(
        first_replay
    )
    second = ReplayStatistics.from_replay(
        second_replay
    )

    assert first == second


def test_turn_count_uses_distinct_turns() -> None:
    replay = Replay()

    for index in range(10):
        replay.add(
            create_event(
                turn=1,
                action=f"action_{index}",
            )
        )

    statistics = ReplayStatistics.from_replay(
        replay
    )

    assert statistics.event_count == 10
    assert statistics.turn_count == 1
    assert statistics.max_turn == 1


def test_max_turn_does_not_depend_on_event_order() -> None:
    replay = Replay()

    replay.add(
        create_event(
            turn=7,
        )
    )
    replay.add(
        create_event(
            turn=2,
        )
    )
    replay.add(
        create_event(
            turn=5,
        )
    )

    statistics = ReplayStatistics.from_replay(
        replay
    )

    assert statistics.max_turn == 7


def test_from_replay_supports_large_event_count() -> None:
    replay = Replay()

    for index in range(1_000):
        replay.add(
            create_event(
                turn=(index % 10) + 1,
                phase=(
                    "main"
                    if index % 2 == 0
                    else "draw"
                ),
                action=(
                    "draw"
                    if index % 3 == 0
                    else "cast_spell"
                ),
            )
        )

    statistics = ReplayStatistics.from_replay(
        replay
    )

    assert statistics.event_count == 1_000
    assert statistics.turn_count == 10
    assert statistics.max_turn == 10
    assert statistics.action_count(
        "draw"
    ) == 334
    assert statistics.action_count(
        "cast_spell"
    ) == 666
    assert statistics.phase_count(
        "main"
    ) == 500
    assert statistics.phase_count(
        "draw"
    ) == 500


def test_from_replay_does_not_modify_replay() -> None:
    replay = create_replay()

    original_events = replay.events
    original_count = replay.event_count

    ReplayStatistics.from_replay(replay)

    assert replay.events == original_events
    assert replay.event_count == original_count


def test_from_replay_does_not_modify_events() -> None:
    replay = create_replay()
    original_events = replay.events

    ReplayStatistics.from_replay(replay)

    assert replay.events == original_events
    assert all(
        current is original
        for current, original in zip(
            replay.events,
            original_events,
            strict=True,
        )
    )


def test_replay_count_is_immutable() -> None:
    count = ReplayCount(
        name="draw",
        count=2,
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        count.count = 3  # type: ignore[misc]


def test_replay_statistics_is_immutable() -> None:
    statistics = create_statistics()

    with pytest.raises(
        FrozenInstanceError,
    ):
        statistics.event_count = 0  # type: ignore[misc]


@pytest.mark.parametrize(
    "name",
    (
        "",
        " ",
        "\t",
        "\n",
    ),
)
def test_replay_count_rejects_empty_name(
    name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="name must not be empty.",
    ):
        ReplayCount(
            name=name,
            count=1,
        )


@pytest.mark.parametrize(
    "count",
    (
        0,
        -1,
        -100,
    ),
)
def test_replay_count_rejects_invalid_count(
    count: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="count must be at least 1.",
    ):
        ReplayCount(
            name="draw",
            count=count,
        )


def test_statistics_rejects_negative_event_count() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "event_count must not be negative."
        ),
    ):
        ReplayStatistics(
            event_count=-1,
            turn_count=0,
            max_turn=None,
            game_start_count=0,
            game_end_count=0,
            action_counts=(),
            phase_counts=(),
        )


def test_statistics_rejects_negative_turn_count() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "turn_count must not be negative."
        ),
    ):
        ReplayStatistics(
            event_count=0,
            turn_count=-1,
            max_turn=None,
            game_start_count=0,
            game_end_count=0,
            action_counts=(),
            phase_counts=(),
        )


def test_statistics_rejects_invalid_max_turn() -> None:
    with pytest.raises(
        ValueError,
        match="max_turn must be at least 1.",
    ):
        ReplayStatistics(
            event_count=0,
            turn_count=0,
            max_turn=0,
            game_start_count=0,
            game_end_count=0,
            action_counts=(),
            phase_counts=(),
        )


def test_statistics_rejects_duplicate_action_names() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "action_counts must not contain "
            "duplicate names."
        ),
    ):
        ReplayStatistics(
            event_count=2,
            turn_count=1,
            max_turn=1,
            game_start_count=0,
            game_end_count=0,
            action_counts=(
                ReplayCount(
                    name="draw",
                    count=1,
                ),
                ReplayCount(
                    name="draw",
                    count=1,
                ),
            ),
            phase_counts=(
                ReplayCount(
                    name="main",
                    count=2,
                ),
            ),
        )


def test_statistics_rejects_unsorted_action_counts() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "action_counts must be sorted by name."
        ),
    ):
        ReplayStatistics(
            event_count=2,
            turn_count=1,
            max_turn=1,
            game_start_count=0,
            game_end_count=0,
            action_counts=(
                ReplayCount(
                    name="draw",
                    count=1,
                ),
                ReplayCount(
                    name="cast_spell",
                    count=1,
                ),
            ),
            phase_counts=(
                ReplayCount(
                    name="main",
                    count=2,
                ),
            ),
        )


def test_statistics_rejects_action_total_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "action_counts total must equal "
            "event_count."
        ),
    ):
        ReplayStatistics(
            event_count=2,
            turn_count=1,
            max_turn=1,
            game_start_count=0,
            game_end_count=0,
            action_counts=(
                ReplayCount(
                    name="draw",
                    count=1,
                ),
            ),
            phase_counts=(
                ReplayCount(
                    name="main",
                    count=2,
                ),
            ),
        )


def test_statistics_rejects_phase_total_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "phase_counts total must equal "
            "event_count."
        ),
    ):
        ReplayStatistics(
            event_count=2,
            turn_count=1,
            max_turn=1,
            game_start_count=0,
            game_end_count=0,
            action_counts=(
                ReplayCount(
                    name="draw",
                    count=2,
                ),
            ),
            phase_counts=(
                ReplayCount(
                    name="main",
                    count=1,
                ),
            ),
        )


def test_statistics_rejects_game_start_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "game_start_count must match "
            "the game_start Action count."
        ),
    ):
        ReplayStatistics(
            event_count=1,
            turn_count=1,
            max_turn=1,
            game_start_count=1,
            game_end_count=0,
            action_counts=(
                ReplayCount(
                    name="draw",
                    count=1,
                ),
            ),
            phase_counts=(
                ReplayCount(
                    name="draw",
                    count=1,
                ),
            ),
        )


def test_statistics_rejects_non_empty_without_max_turn() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Non-empty Replay statistics must "
            "define max_turn."
        ),
    ):
        ReplayStatistics(
            event_count=1,
            turn_count=1,
            max_turn=None,
            game_start_count=0,
            game_end_count=0,
            action_counts=(
                ReplayCount(
                    name="draw",
                    count=1,
                ),
            ),
            phase_counts=(
                ReplayCount(
                    name="draw",
                    count=1,
                ),
            ),
        )