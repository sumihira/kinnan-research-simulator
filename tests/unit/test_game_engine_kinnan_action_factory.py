from __future__ import annotations

from unittest.mock import Mock

from krs.actions.activate_kinnan import ActivateKinnanAction
from krs.ai.kinnan_action_factory import KinnanActionFactory
from krs.engine.game_engine import GameEngine
from krs.game.game_state import GameState
from krs.game.phase import Phase
from krs.game.player import Player


def create_running_state() -> GameState:
    return GameState(
        players=[
            Player(player_id=0),
        ],
        started=True,
        phase=Phase.MAIN,
        turn_number=4,
    )


def test_create_kinnan_activation_action_delegates_to_factory() -> None:
    state = create_running_state()

    expected_action = ActivateKinnanAction(
        player_id=0,
        turn_number=4,
        source_permanent_id=12,
        selected_card_id="selected-card-id",
    )

    kinnan_action_factory = Mock(spec=KinnanActionFactory)
    kinnan_action_factory.create.return_value = expected_action

    engine = GameEngine(
        kinnan_action_factory=kinnan_action_factory,
    )

    action = engine.create_kinnan_activation_action(
        state,
        player_id=0,
        source_permanent_id=12,
    )

    kinnan_action_factory.create.assert_called_once_with(
        state=state,
        player_id=0,
        source_permanent_id=12,
    )
    assert action is expected_action


def test_create_kinnan_activation_action_does_not_execute_action() -> None:
    state = create_running_state()

    expected_action = ActivateKinnanAction(
        player_id=0,
        turn_number=4,
        source_permanent_id=12,
        selected_card_id=None,
    )

    kinnan_action_factory = Mock(spec=KinnanActionFactory)
    kinnan_action_factory.create.return_value = expected_action

    action_executor = Mock()

    engine = GameEngine(
        action_executor=action_executor,
        kinnan_action_factory=kinnan_action_factory,
    )

    action = engine.create_kinnan_activation_action(
        state,
        player_id=0,
        source_permanent_id=12,
    )

    action_executor.execute.assert_not_called()
    assert state.action_count == 0
    assert action is expected_action