from __future__ import annotations

from unittest.mock import Mock

from krs.actions.cast_commander import CastCommanderAction
from krs.actions.tap_permanent import TapPermanentAction
from krs.ai.kinnan_cast_plan_factory import (
    KinnanCastPlan,
    KinnanCastPlanFactory,
)
from krs.cards.card import Card
from krs.engine.action_executor import ActionExecutor
from krs.engine.game_engine import GameEngine
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player
from krs.mana.mana import Mana
from krs.mana.mana_cost import ManaCost
from krs.simulation.runner import GoldfishRunner


def create_kinnan() -> Card:
    return Card(
        id="kinnan-id",
        name="Kinnan, Bonder Prodigy",
        mana_cost="{G}{U}",
        mana_value=2,
        oracle_text="",
        type_line="Legendary Creature — Human Druid",
        power="2",
        toughness="2",
    )


def create_land(
    *,
    card_id: str,
    name: str,
    type_line: str,
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line=type_line,
    )


def create_permanent(
    *,
    permanent_id: int,
    card: Card,
) -> Permanent:
    return Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=0,
        controller_id=0,
        tapped=False,
        summoning_sick=False,
        entered_turn=1,
    )


def create_running_state() -> GameState:
    player = Player(
        player_id=0,
    )
    player.command.add(
        create_kinnan()
    )

    forest = create_permanent(
        permanent_id=1,
        card=create_land(
            card_id="forest-id",
            name="Forest",
            type_line="Basic Land — Forest",
        ),
    )
    island = create_permanent(
        permanent_id=2,
        card=create_land(
            card_id="island-id",
            name="Island",
            type_line="Basic Land — Island",
        ),
    )

    player.battlefield.add(forest)
    player.battlefield.add(island)

    return GameState(
        players=[player],
        started=True,
        phase=Phase.MAIN,
        turn_number=2,
        next_permanent_id=3,
    )


def create_plan(
    state: GameState,
) -> KinnanCastPlan:
    player = state.players[0]
    forest = player.battlefield.cards[0]
    island = player.battlefield.cards[1]
    kinnan = player.command.cards[0]

    return KinnanCastPlan(
        mana_actions=(
            TapPermanentAction(
                player_id=0,
                turn_number=2,
                permanent=forest,
                mana=Mana.GREEN,
            ),
            TapPermanentAction(
                player_id=0,
                turn_number=2,
                permanent=island,
                mana=Mana.BLUE,
            ),
        ),
        cast_action=CastCommanderAction(
            player_id=0,
            turn_number=2,
            card=kinnan,
            base_cost=ManaCost(
                green=1,
                blue=1,
            ),
        ),
    )


def test_game_engine_creates_kinnan_cast_plan() -> None:
    state = create_running_state()
    expected_plan = create_plan(state)

    factory = Mock(
        spec=KinnanCastPlanFactory,
    )
    factory.create.return_value = expected_plan

    engine = GameEngine(
        kinnan_cast_plan_factory=factory,
    )

    plan = engine.create_kinnan_cast_plan(
        state,
        player_id=0,
    )

    assert plan is expected_plan
    factory.create.assert_called_once_with(
        state=state,
        player_id=0,
    )


def test_game_engine_returns_no_plan_outside_main_phase() -> None:
    state = create_running_state()
    state.phase = Phase.UPKEEP

    factory = Mock(
        spec=KinnanCastPlanFactory,
    )

    engine = GameEngine(
        kinnan_cast_plan_factory=factory,
    )

    plan = engine.create_kinnan_cast_plan(
        state,
        player_id=0,
    )

    assert plan is None
    factory.create.assert_not_called()


def test_game_engine_executes_cast_plan_in_order() -> None:
    state = create_running_state()
    plan = create_plan(state)

    factory = Mock(
        spec=KinnanCastPlanFactory,
    )
    factory.create.return_value = plan

    executor = Mock(
        spec=ActionExecutor,
    )

    engine = GameEngine(
        action_executor=executor,
        kinnan_cast_plan_factory=factory,
    )

    executed = engine.execute_kinnan_cast_if_available(
        state,
        player_id=0,
    )

    assert executed is True
    assert executor.execute.call_args_list == [
        (
            (state, plan.mana_actions[0]),
            {},
        ),
        (
            (state, plan.mana_actions[1]),
            {},
        ),
        (
            (state, plan.cast_action),
            {},
        ),
    ]


def test_game_engine_returns_false_without_cast_plan() -> None:
    state = create_running_state()

    factory = Mock(
        spec=KinnanCastPlanFactory,
    )
    factory.create.return_value = None

    executor = Mock(
        spec=ActionExecutor,
    )

    engine = GameEngine(
        action_executor=executor,
        kinnan_cast_plan_factory=factory,
    )

    executed = engine.execute_kinnan_cast_if_available(
        state,
        player_id=0,
    )

    assert executed is False
    executor.execute.assert_not_called()


def test_game_engine_casts_kinnan_with_real_executor() -> None:
    state = create_running_state()
    player = state.players[0]

    executed = GameEngine().execute_kinnan_cast_if_available(
        state,
        player_id=0,
    )

    assert executed is True
    assert len(player.command) == 0
    assert len(player.battlefield) == 3

    kinnan_permanent = next(
        permanent
        for permanent in player.battlefield
        if permanent.effective_card.name
        == "Kinnan, Bonder Prodigy"
    )

    assert kinnan_permanent.permanent_id == 3
    assert kinnan_permanent.summoning_sick is True

    assert player.battlefield.cards[0].tapped is True
    assert player.battlefield.cards[1].tapped is True
    assert player.mana_pool.total() == 0
    assert player.commander_cast_count == 1

    assert state.next_permanent_id == 4
    assert state.mana_generated == 2
    assert state.mana_spent == 2
    assert state.action_count == 3


def test_game_engine_does_not_cast_without_enough_mana() -> None:
    state = create_running_state()
    player = state.players[0]

    island = player.battlefield.cards[1]
    player.battlefield.remove(island)

    executed = GameEngine().execute_kinnan_cast_if_available(
        state,
        player_id=0,
    )

    assert executed is False
    assert len(player.command) == 1
    assert len(player.battlefield) == 1
    assert player.battlefield.cards[0].tapped is False
    assert player.commander_cast_count == 0
    assert state.action_count == 0


def test_runner_executes_land_cast_and_activation_in_order() -> None:
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

    def execute_cast(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert current_state is state
        assert player_id == 0
        execution_order.append("cast")
        return True

    def execute_activation(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert current_state is state
        assert player_id == 0
        execution_order.append("activation")
        return False

    def advance_phase(
        current_state: GameState,
    ) -> None:
        current_state.phase = Phase.END

    engine.execute_land_play_if_available.side_effect = (
        execute_land
    )
    engine.execute_kinnan_cast_if_available.side_effect = (
        execute_cast
    )
    engine.execute_kinnan_activation_if_available.side_effect = (
        execute_activation
    )
    engine.advance_phase.side_effect = advance_phase

    result = GoldfishRunner(
        game_engine=engine,
        max_turns=2,
    ).run(state)

    assert execution_order == [
        "land",
        "cast",
        "activation",
    ]
    assert result.kinnan_activations == 0


def test_runner_skips_cast_after_game_ends_during_land_play() -> None:
    state = create_running_state()

    engine = Mock(
        spec=GameEngine,
    )

    def execute_land(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert player_id == 0
        current_state.game_over = True
        current_state.winner = "Player"
        return True

    engine.execute_land_play_if_available.side_effect = (
        execute_land
    )

    result = GoldfishRunner(
        game_engine=engine,
        max_turns=2,
    ).run(state)

    assert result.game_over is True
    assert result.winner == "Player"

    engine.execute_kinnan_cast_if_available.assert_not_called()
    (
        engine
        .execute_kinnan_activation_if_available
        .assert_not_called()
    )