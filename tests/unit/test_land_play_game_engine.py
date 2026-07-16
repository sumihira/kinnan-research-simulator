from __future__ import annotations

from unittest.mock import Mock, call

from krs.actions.play_land import PlayLandAction
from krs.ai.land_action_factory import LandActionFactory
from krs.cards.card import Card
from krs.engine.action_executor import ActionExecutor
from krs.engine.game_engine import GameEngine
from krs.game.game_state import GameState
from krs.game.phase import Phase
from krs.game.player import Player
from krs.simulation.runner import GoldfishRunner


def create_land() -> Card:
    return Card(
        id="forest-id",
        name="Forest",
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line="Basic Land — Forest",
    )


def create_running_state(
    *,
    phase: Phase = Phase.MAIN,
) -> GameState:
    return GameState(
        players=[
            Player(player_id=0),
        ],
        started=True,
        phase=phase,
        turn_number=2,
    )


def test_game_engine_creates_land_play_action() -> None:
    state = create_running_state()
    land = create_land()
    state.players[0].hand.add(land)

    action = GameEngine().create_land_play_action(
        state,
        player_id=0,
    )

    assert action is not None
    assert action.player_id == 0
    assert action.turn_number == 2
    assert action.card is land


def test_game_engine_returns_none_without_land() -> None:
    state = create_running_state()

    action = GameEngine().create_land_play_action(
        state,
        player_id=0,
    )

    assert action is None


def test_game_engine_executes_land_play_action() -> None:
    state = create_running_state()
    player = state.players[0]
    land = create_land()
    player.hand.add(land)

    executed = (
        GameEngine()
        .execute_land_play_if_available(
            state,
            player_id=0,
        )
    )

    assert executed is True
    assert len(player.hand) == 0
    assert len(player.battlefield) == 1
    assert (
        player.battlefield.cards[0].card
        is land
    )
    assert player.land_played_this_turn == 1
    assert state.action_count == 1


def test_game_engine_does_not_execute_without_land() -> None:
    state = create_running_state()

    executed = (
        GameEngine()
        .execute_land_play_if_available(
            state,
            player_id=0,
        )
    )

    assert executed is False
    assert state.action_count == 0


def test_game_engine_uses_injected_land_factory() -> None:
    state = create_running_state()
    land = create_land()

    action = PlayLandAction(
        player_id=0,
        turn_number=2,
        card=land,
    )

    factory = Mock(
        spec=LandActionFactory,
    )
    factory.create.return_value = action

    executor = Mock(
        spec=ActionExecutor,
    )

    engine = GameEngine(
        action_executor=executor,
        land_action_factory=factory,
    )

    executed = (
        engine
        .execute_land_play_if_available(
            state,
            player_id=0,
        )
    )

    assert executed is True

    factory.create.assert_called_once_with(
        state=state,
        player_id=0,
    )
    executor.execute.assert_called_once_with(
        state,
        action,
    )


def test_game_engine_does_not_call_executor_for_no_action() -> None:
    state = create_running_state()

    factory = Mock(
        spec=LandActionFactory,
    )
    factory.create.return_value = None

    executor = Mock(
        spec=ActionExecutor,
    )

    engine = GameEngine(
        action_executor=executor,
        land_action_factory=factory,
    )

    executed = (
        engine
        .execute_land_play_if_available(
            state,
            player_id=0,
        )
    )

    assert executed is False
    executor.execute.assert_not_called()


def test_runner_plays_land_before_kinnan_activation() -> None:
    state = create_running_state()

    engine = Mock(
        spec=GameEngine,
    )
    execution_order: list[str] = []

    def execute_land(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert current_state is state
        assert player_id == 0
        execution_order.append("land")
        return True

    def execute_kinnan(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert current_state is state
        assert player_id == 0
        execution_order.append("kinnan")
        return False

    def advance_phase(
        current_state: GameState,
    ) -> None:
        assert current_state is state
        current_state.phase = Phase.END

    engine.execute_land_play_if_available.side_effect = (
        execute_land
    )
    engine.execute_kinnan_activation_if_available.side_effect = (
        execute_kinnan
    )
    engine.advance_phase.side_effect = advance_phase

    runner = GoldfishRunner(
        game_engine=engine,
        max_turns=2,
    )

    result = runner.run(state)

    assert execution_order == [
        "land",
        "kinnan",
    ]
    assert result.kinnan_activations == 0

    engine.execute_land_play_if_available.assert_called_once_with(
        state,
        player_id=0,
    )
    engine.execute_kinnan_activation_if_available.assert_called_once_with(
        state,
        player_id=0,
    )


def test_runner_attempts_one_land_per_turn() -> None:
    state = create_running_state(
        phase=Phase.UNTAP,
    )

    engine = Mock(
        spec=GameEngine,
    )

    def advance_phase(
        current_state: GameState,
    ) -> None:
        phase_order = {
            Phase.UNTAP: Phase.UPKEEP,
            Phase.UPKEEP: Phase.DRAW,
            Phase.DRAW: Phase.MAIN,
            Phase.MAIN: Phase.END,
        }
        current_state.phase = phase_order[
            current_state.phase
        ]

    def end_turn(
        current_state: GameState,
    ) -> None:
        current_state.turn_number += 1
        current_state.phase = Phase.UNTAP

    engine.advance_phase.side_effect = advance_phase
    engine.end_turn.side_effect = end_turn
    engine.execute_land_play_if_available.return_value = False
    engine.execute_kinnan_activation_if_available.return_value = False

    runner = GoldfishRunner(
        game_engine=engine,
        max_turns=3,
    )

    runner.run(state)

    assert (
        engine
        .execute_land_play_if_available
        .call_args_list
    ) == [
        call(state, player_id=0),
        call(state, player_id=0),
    ]