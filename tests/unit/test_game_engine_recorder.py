from __future__ import annotations

from unittest.mock import Mock

import pytest

from krs.engine.game_engine import GameEngine
from krs.game.game_state import GameState
from krs.game.phase import Phase
from krs.game.player import Player
from krs.replay.game_engine_recorder import (
    ReplayGameEngineRecorder,
)
from krs.replay.replay import Replay


def create_state(
    *,
    started: bool = True,
    game_over: bool = False,
    winner: str | None = None,
    turn_number: int = 1,
    phase: Phase = Phase.UNTAP,
) -> GameState:
    return GameState(
        game_id=42,
        players=[
            Player(
                player_id=0,
            ),
        ],
        started=started,
        game_over=game_over,
        winner=winner,
        turn_number=turn_number,
        phase=phase,
        active_player_index=0,
    )


def create_engine_mock() -> Mock:
    return Mock(
        spec=GameEngine,
    )


def test_recorder_creates_replay_by_default() -> None:
    recorder = ReplayGameEngineRecorder(
        engine=create_engine_mock(),
    )

    assert isinstance(
        recorder.replay,
        Replay,
    )
    assert recorder.replay.is_empty is True


def test_recorder_uses_supplied_replay() -> None:
    replay = Replay()

    recorder = ReplayGameEngineRecorder(
        engine=create_engine_mock(),
        replay=replay,
    )

    assert recorder.replay is replay


def test_start_game_delegates_to_engine() -> None:
    state = create_state(
        started=False,
    )
    engine = create_engine_mock()

    def start_game(
        current_state: GameState,
    ) -> None:
        current_state.started = True

    engine.start_game.side_effect = start_game

    recorder = ReplayGameEngineRecorder(
        engine=engine,
    )

    recorder.start_game(state)

    engine.start_game.assert_called_once_with(
        state
    )


def test_successful_start_game_is_recorded() -> None:
    state = create_state(
        started=False,
    )
    engine = create_engine_mock()

    def start_game(
        current_state: GameState,
    ) -> None:
        current_state.started = True

    engine.start_game.side_effect = start_game

    recorder = ReplayGameEngineRecorder(
        engine=engine,
    )

    recorder.start_game(state)

    assert recorder.replay.event_count == 1

    event = recorder.replay.events[0]

    assert event.turn == 1
    assert event.phase == "untap"
    assert event.action == "game_start"
    assert event.description == (
        "Started game 42 with 1 player(s)."
    )


def test_failed_start_game_is_not_recorded() -> None:
    state = create_state(
        started=False,
    )
    engine = create_engine_mock()
    engine.start_game.side_effect = ValueError(
        "Game start failed."
    )

    recorder = ReplayGameEngineRecorder(
        engine=engine,
    )

    with pytest.raises(
        ValueError,
        match="Game start failed.",
    ):
        recorder.start_game(state)

    assert recorder.replay.is_empty is True


def test_start_turn_delegates_to_engine() -> None:
    state = create_state(
        phase=Phase.MAIN,
    )
    engine = create_engine_mock()

    def start_turn(
        current_state: GameState,
    ) -> None:
        current_state.phase = Phase.UNTAP

    engine.start_turn.side_effect = start_turn

    recorder = ReplayGameEngineRecorder(
        engine=engine,
    )

    recorder.start_turn(state)

    engine.start_turn.assert_called_once_with(
        state
    )


def test_successful_start_turn_is_recorded() -> None:
    state = create_state(
        turn_number=3,
        phase=Phase.MAIN,
    )
    engine = create_engine_mock()

    def start_turn(
        current_state: GameState,
    ) -> None:
        current_state.phase = Phase.UNTAP

    engine.start_turn.side_effect = start_turn

    recorder = ReplayGameEngineRecorder(
        engine=engine,
    )

    recorder.start_turn(state)

    assert recorder.replay.event_count == 1

    event = recorder.replay.events[0]

    assert event.turn == 3
    assert event.phase == "untap"
    assert event.action == "turn_start"
    assert event.description == (
        "Started turn 3 for player 0."
    )


def test_failed_start_turn_is_not_recorded() -> None:
    state = create_state()
    engine = create_engine_mock()
    engine.start_turn.side_effect = ValueError(
        "Turn start failed."
    )

    recorder = ReplayGameEngineRecorder(
        engine=engine,
    )

    with pytest.raises(
        ValueError,
        match="Turn start failed.",
    ):
        recorder.start_turn(state)

    assert recorder.replay.is_empty is True


def test_advance_phase_only_delegates() -> None:
    state = create_state()
    engine = create_engine_mock()

    recorder = ReplayGameEngineRecorder(
        engine=engine,
    )

    recorder.advance_phase(state)

    engine.advance_phase.assert_called_once_with(
        state
    )
    assert recorder.replay.is_empty is True


def test_end_turn_records_new_turn_once() -> None:
    state = create_state(
        turn_number=1,
        phase=Phase.END,
    )
    engine = create_engine_mock()

    def end_turn(
        current_state: GameState,
    ) -> None:
        current_state.turn_number = 2
        current_state.phase = Phase.UNTAP

    engine.end_turn.side_effect = end_turn

    recorder = ReplayGameEngineRecorder(
        engine=engine,
    )

    recorder.end_turn(state)

    engine.end_turn.assert_called_once_with(
        state
    )
    assert recorder.replay.event_count == 1

    event = recorder.replay.events[0]

    assert event.turn == 2
    assert event.phase == "untap"
    assert event.action == "turn_start"
    assert event.description == (
        "Started turn 2 for player 0."
    )


def test_failed_end_turn_is_not_recorded() -> None:
    state = create_state(
        phase=Phase.END,
    )
    engine = create_engine_mock()
    engine.end_turn.side_effect = ValueError(
        "Turn end failed."
    )

    recorder = ReplayGameEngineRecorder(
        engine=engine,
    )

    with pytest.raises(
        ValueError,
        match="Turn end failed.",
    ):
        recorder.end_turn(state)

    assert recorder.replay.is_empty is True


def test_record_game_end_with_winner() -> None:
    state = create_state(
        game_over=True,
        winner="Player",
        turn_number=4,
        phase=Phase.MAIN,
    )

    recorder = ReplayGameEngineRecorder(
        engine=create_engine_mock(),
    )

    recorder.record_game_end(state)

    event = recorder.replay.events[0]

    assert event.turn == 4
    assert event.phase == "main"
    assert event.action == "game_end"
    assert event.description == (
        "Game ended. Winner: Player."
    )


def test_record_game_end_without_winner() -> None:
    state = create_state(
        game_over=True,
        winner=None,
        turn_number=8,
        phase=Phase.END,
    )

    recorder = ReplayGameEngineRecorder(
        engine=create_engine_mock(),
    )

    recorder.record_game_end(state)

    event = recorder.replay.events[0]

    assert event.description == (
        "Game ended without a winner."
    )


def test_record_game_end_rejects_unstarted_game() -> None:
    state = create_state(
        started=False,
        game_over=True,
    )

    recorder = ReplayGameEngineRecorder(
        engine=create_engine_mock(),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Cannot record the end of "
            "an unstarted game."
        ),
    ):
        recorder.record_game_end(state)

    assert recorder.replay.is_empty is True


def test_record_game_end_rejects_running_game() -> None:
    state = create_state(
        started=True,
        game_over=False,
    )

    recorder = ReplayGameEngineRecorder(
        engine=create_engine_mock(),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Cannot record game end before "
            "the game is finished."
        ),
    ):
        recorder.record_game_end(state)

    assert recorder.replay.is_empty is True


def test_lifecycle_events_preserve_order() -> None:
    state = create_state(
        started=False,
    )
    engine = create_engine_mock()

    def start_game(
        current_state: GameState,
    ) -> None:
        current_state.started = True

    def start_turn(
        current_state: GameState,
    ) -> None:
        current_state.phase = Phase.UNTAP

    engine.start_game.side_effect = start_game
    engine.start_turn.side_effect = start_turn

    recorder = ReplayGameEngineRecorder(
        engine=engine,
    )

    recorder.start_game(state)
    recorder.start_turn(state)

    state.game_over = True
    state.winner = "Player"

    recorder.record_game_end(state)

    assert tuple(
        event.action
        for event in recorder.replay.events
    ) == (
        "game_start",
        "turn_start",
        "game_end",
    )


def test_unknown_api_is_delegated_to_engine() -> None:
    engine = create_engine_mock()

    engine.execute_kinnan_activation_if_available = Mock(
        return_value=True,
    )

    recorder = ReplayGameEngineRecorder(
        engine=engine,
    )
    state = create_state()

    result = (
        recorder.execute_kinnan_activation_if_available(
            state,
            player_id=0,
        )
    )

    assert result is True

    engine.execute_kinnan_activation_if_available.assert_called_once_with(
        state,
        player_id=0,
    )


def test_kinnan_action_factory_api_remains_available() -> None:
    engine = create_engine_mock()
    expected = object()

    engine.create_kinnan_activation_action = Mock(
        return_value=expected,
    )

    recorder = ReplayGameEngineRecorder(
        engine=engine,
    )
    state = create_state()

    result = recorder.create_kinnan_activation_action(
        state,
        player_id=0,
        source_permanent_id=12,
    )

    assert result is expected

    engine.create_kinnan_activation_action.assert_called_once_with(
        state,
        player_id=0,
        source_permanent_id=12,
    )


def test_recorder_does_not_replace_wrapped_engine() -> None:
    engine = create_engine_mock()

    recorder = ReplayGameEngineRecorder(
        engine=engine,
    )

    assert recorder.engine is engine