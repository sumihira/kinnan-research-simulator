from __future__ import annotations

from unittest.mock import Mock, call

import pytest

from krs.engine.game_engine import GameEngine
from krs.game.game_state import GameState
from krs.game.phase import Phase
from krs.game.player import Player
from krs.simulation.runner import (
    GoldfishRunner,
    GoldfishRunResult,
)


def create_state(
    *,
    started: bool = True,
    game_over: bool = False,
    phase: Phase = Phase.UNTAP,
    turn_number: int = 1,
) -> GameState:
    return GameState(
        players=[
            Player(player_id=0),
        ],
        started=started,
        game_over=game_over,
        phase=phase,
        turn_number=turn_number,
    )


def configure_phase_progression(
    engine: Mock,
) -> None:
    def advance_phase(state: GameState) -> None:
        phase_order = {
            Phase.UNTAP: Phase.UPKEEP,
            Phase.UPKEEP: Phase.DRAW,
            Phase.DRAW: Phase.MAIN,
            Phase.MAIN: Phase.END,
        }
        state.phase = phase_order[state.phase]

    engine.advance_phase.side_effect = advance_phase


def configure_end_turn(
    engine: Mock,
) -> None:
    def end_turn(state: GameState) -> None:
        state.turn_number += 1
        state.phase = Phase.UNTAP

    engine.end_turn.side_effect = end_turn


def create_engine_mock() -> Mock:
    engine = Mock(spec=GameEngine)
    configure_phase_progression(engine)
    configure_end_turn(engine)
    engine.execute_kinnan_activation_if_available.return_value = False
    return engine


def test_runner_starts_unstarted_game() -> None:
    state = create_state(
        started=False,
    )
    engine = create_engine_mock()

    def start_game(current_state: GameState) -> None:
        current_state.started = True

    def start_turn(current_state: GameState) -> None:
        current_state.phase = Phase.UNTAP

    engine.start_game.side_effect = start_game
    engine.start_turn.side_effect = start_turn

    runner = GoldfishRunner(
        game_engine=engine,
        max_turns=1,
    )

    result = runner.run(state)

    engine.start_game.assert_called_once_with(state)
    engine.start_turn.assert_called_once_with(state)
    assert result.turns_started == 1
    assert state.phase is Phase.END


def test_runner_does_not_restart_started_game() -> None:
    state = create_state(
        started=True,
    )
    engine = create_engine_mock()

    runner = GoldfishRunner(
        game_engine=engine,
        max_turns=1,
    )

    runner.run(state)

    engine.start_game.assert_not_called()
    engine.start_turn.assert_not_called()


def test_runner_advances_to_main_and_then_end() -> None:
    state = create_state(
        phase=Phase.UNTAP,
    )
    engine = create_engine_mock()

    runner = GoldfishRunner(
        game_engine=engine,
        max_turns=1,
    )

    runner.run(state)

    assert engine.advance_phase.call_args_list == [
        call(state),
        call(state),
        call(state),
        call(state),
    ]
    assert state.phase is Phase.END


def test_runner_executes_available_kinnan_activations() -> None:
    state = create_state(
        phase=Phase.MAIN,
    )
    engine = create_engine_mock()
    engine.execute_kinnan_activation_if_available.side_effect = [
        True,
        True,
        False,
    ]

    runner = GoldfishRunner(
        game_engine=engine,
        max_turns=1,
    )

    result = runner.run(state)

    assert (
        engine
        .execute_kinnan_activation_if_available
        .call_args_list
    ) == [
        call(state, player_id=0),
        call(state, player_id=0),
        call(state, player_id=0),
    ]
    assert result.kinnan_activations == 2


def test_runner_stops_kinnan_loop_at_per_turn_limit() -> None:
    state = create_state(
        phase=Phase.MAIN,
    )
    engine = create_engine_mock()
    engine.execute_kinnan_activation_if_available.return_value = True

    runner = GoldfishRunner(
        game_engine=engine,
        max_turns=1,
        max_kinnan_activations_per_turn=3,
    )

    result = runner.run(state)

    assert (
        engine
        .execute_kinnan_activation_if_available
        .call_count
        == 3
    )
    assert result.kinnan_activations == 3


def test_runner_executes_multiple_turns() -> None:
    state = create_state()
    engine = create_engine_mock()

    runner = GoldfishRunner(
        game_engine=engine,
        max_turns=3,
    )

    result = runner.run(state)

    assert result.turns_started == 3
    assert result.reached_turn_limit is True
    assert state.turn_number == 3
    assert state.phase is Phase.END
    assert engine.end_turn.call_count == 2


def test_runner_does_not_advance_beyond_max_turns() -> None:
    state = create_state(
        turn_number=3,
    )
    engine = create_engine_mock()

    runner = GoldfishRunner(
        game_engine=engine,
        max_turns=3,
    )

    runner.run(state)

    engine.end_turn.assert_not_called()
    assert state.turn_number == 3
    assert state.phase is Phase.END


def test_runner_stops_when_game_ends_during_kinnan_activation() -> None:
    state = create_state(
        phase=Phase.MAIN,
    )
    engine = create_engine_mock()

    def execute_kinnan(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert player_id == 0
        current_state.game_over = True
        current_state.winner = "Player"
        return True

    engine.execute_kinnan_activation_if_available.side_effect = (
        execute_kinnan
    )

    runner = GoldfishRunner(
        game_engine=engine,
        max_turns=10,
    )

    result = runner.run(state)

    assert result == GoldfishRunResult(
        turns_started=1,
        kinnan_activations=1,
        reached_turn_limit=False,
        game_over=True,
        winner="Player",
    )
    engine.advance_phase.assert_not_called()
    engine.end_turn.assert_not_called()


def test_runner_returns_result_without_kinnan_activation() -> None:
    state = create_state(
        phase=Phase.MAIN,
    )
    engine = create_engine_mock()

    runner = GoldfishRunner(
        game_engine=engine,
        max_turns=1,
    )

    result = runner.run(state)

    assert result == GoldfishRunResult(
        turns_started=1,
        kinnan_activations=0,
        reached_turn_limit=True,
        game_over=False,
        winner=None,
    )


def test_runner_rejects_state_without_players() -> None:
    state = GameState()
    engine = create_engine_mock()

    runner = GoldfishRunner(
        game_engine=engine,
    )

    with pytest.raises(
        ValueError,
        match="Cannot run a Goldfish game without players.",
    ):
        runner.run(state)


def test_runner_rejects_finished_game() -> None:
    state = create_state(
        game_over=True,
    )
    engine = create_engine_mock()

    runner = GoldfishRunner(
        game_engine=engine,
    )

    with pytest.raises(
        ValueError,
        match=(
            "Cannot run a Goldfish game that has "
            "already finished."
        ),
    ):
        runner.run(state)


def test_runner_rejects_resume_from_end_phase() -> None:
    state = create_state(
        phase=Phase.END,
    )
    engine = create_engine_mock()

    runner = GoldfishRunner(
        game_engine=engine,
    )

    with pytest.raises(
        ValueError,
        match="Cannot resume a Goldfish turn from END phase.",
    ):
        runner.run(state)


def test_runner_rejects_max_turns_below_one() -> None:
    engine = create_engine_mock()

    with pytest.raises(
        ValueError,
        match="max_turns must be at least 1.",
    ):
        GoldfishRunner(
            game_engine=engine,
            max_turns=0,
        )


def test_runner_rejects_activation_limit_below_one() -> None:
    engine = create_engine_mock()

    with pytest.raises(
        ValueError,
        match=(
            "max_kinnan_activations_per_turn "
            "must be at least 1."
        ),
    ):
        GoldfishRunner(
            game_engine=engine,
            max_kinnan_activations_per_turn=0,
        )