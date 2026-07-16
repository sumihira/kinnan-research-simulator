from __future__ import annotations

from unittest.mock import Mock

from krs.actions.activate_kinnan import ActivateKinnanAction
from krs.actions.tap_permanent import TapPermanentAction
from krs.ai.kinnan_activation_plan_factory import (
    KinnanActivationPlan,
    KinnanActivationPlanFactory,
)
from krs.cards.card import Card
from krs.engine.action_executor import ActionExecutor
from krs.engine.game_engine import GameEngine
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player
from krs.mana.mana import Mana


def create_state() -> GameState:
    player = Player(
        player_id=0,
    )

    kinnan = Permanent(
        permanent_id=1,
        card=Card(
            id="kinnan-id",
            name="Kinnan, Bonder Prodigy",
            mana_cost="{G}{U}",
            mana_value=2,
            oracle_text="",
            type_line=(
                "Legendary Creature — Human Druid"
            ),
            power="2",
            toughness="2",
        ),
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
        entered_turn=2,
    )

    forest = Permanent(
        permanent_id=2,
        card=Card(
            id="forest-id",
            name="Forest",
            mana_cost="",
            mana_value=0,
            oracle_text="",
            type_line="Basic Land — Forest",
        ),
        owner_id=0,
        controller_id=0,
        summoning_sick=False,
        entered_turn=1,
    )

    player.battlefield.add(kinnan)
    player.battlefield.add(forest)

    return GameState(
        players=[player],
        started=True,
        phase=Phase.MAIN,
        turn_number=2,
    )


def test_game_engine_creates_activation_plan() -> None:
    state = create_state()

    expected_plan = KinnanActivationPlan(
        source_permanent_id=1,
        mana_actions=(),
    )

    factory = Mock(
        spec=KinnanActivationPlanFactory,
    )
    factory.create.return_value = expected_plan

    engine = GameEngine(
        kinnan_activation_plan_factory=factory,
    )

    plan = engine.create_kinnan_activation_plan(
        state,
        player_id=0,
    )

    assert plan is expected_plan
    factory.create.assert_called_once_with(
        state=state,
        player_id=0,
    )


def test_game_engine_returns_no_plan_outside_main() -> None:
    state = create_state()
    state.phase = Phase.UPKEEP

    factory = Mock(
        spec=KinnanActivationPlanFactory,
    )

    engine = GameEngine(
        kinnan_activation_plan_factory=factory,
    )

    plan = engine.create_kinnan_activation_plan(
        state,
        player_id=0,
    )

    assert plan is None
    factory.create.assert_not_called()


def test_game_engine_executes_mana_then_activation() -> None:
    state = create_state()
    forest = state.players[0].battlefield.cards[1]

    mana_action = TapPermanentAction(
        player_id=0,
        turn_number=2,
        permanent=forest,
        mana=Mana.GREEN,
    )
    plan = KinnanActivationPlan(
        source_permanent_id=1,
        mana_actions=(
            mana_action,
        ),
    )

    plan_factory = Mock(
        spec=KinnanActivationPlanFactory,
    )
    plan_factory.create.return_value = plan

    executor = Mock(
        spec=ActionExecutor,
    )

    expected_activation = ActivateKinnanAction(
        player_id=0,
        turn_number=2,
        source_permanent_id=1,
        selected_card_id=None,
    )

    engine = GameEngine(
        action_executor=executor,
        kinnan_activation_plan_factory=plan_factory,
    )
    engine.create_kinnan_activation_action = Mock(
        return_value=expected_activation,
    )

    executed = (
        engine
        .execute_kinnan_activation_if_available(
            state,
            player_id=0,
        )
    )

    assert executed is True
    assert executor.execute.call_args_list == [
        (
            (state, mana_action),
            {},
        ),
        (
            (state, expected_activation),
            {},
        ),
    ]


def test_game_engine_returns_false_without_plan() -> None:
    state = create_state()

    plan_factory = Mock(
        spec=KinnanActivationPlanFactory,
    )
    plan_factory.create.return_value = None

    executor = Mock(
        spec=ActionExecutor,
    )

    engine = GameEngine(
        action_executor=executor,
        kinnan_activation_plan_factory=plan_factory,
    )

    executed = (
        engine
        .execute_kinnan_activation_if_available(
            state,
            player_id=0,
        )
    )

    assert executed is False
    executor.execute.assert_not_called()