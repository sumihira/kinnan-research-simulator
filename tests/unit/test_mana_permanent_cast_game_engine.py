from __future__ import annotations

from types import MappingProxyType
from unittest.mock import Mock

import pytest

from krs.abilities.mana_ability import ManaAbility
from krs.actions.cast_spell import CastSpellAction
from krs.actions.tap_permanent import TapPermanentAction
from krs.ai.mana_permanent_cast_plan_factory import (
    ManaPermanentCastPlan,
    ManaPermanentCastPlanFactory,
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


def create_card(
    *,
    card_id: str,
    name: str,
    mana_cost: str,
    type_line: str,
    mana_abilities: tuple[ManaAbility, ...] = (),
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost=mana_cost,
        mana_value=0,
        oracle_text="",
        type_line=type_line,
        mana_abilities=mana_abilities,
    )


def create_sol_ring() -> Card:
    return create_card(
        card_id="sol-ring-id",
        name="Sol Ring",
        mana_cost="{1}",
        type_line="Artifact",
        mana_abilities=(
            ManaAbility(
                produced_mana=MappingProxyType(
                    {
                        Mana.COLORLESS: 2,
                    }
                ),
                requires_tap=True,
            ),
        ),
    )


def create_forest_permanent() -> Permanent:
    return Permanent(
        permanent_id=1,
        card=create_card(
            card_id="forest-id",
            name="Forest",
            mana_cost="",
            type_line="Basic Land — Forest",
        ),
        owner_id=0,
        controller_id=0,
        summoning_sick=False,
        entered_turn=1,
    )


def create_running_state() -> GameState:
    return GameState(
        players=[
            Player(player_id=0),
        ],
        started=True,
        phase=Phase.MAIN,
        turn_number=2,
        next_permanent_id=2,
    )


def create_plan(
    state: GameState,
) -> ManaPermanentCastPlan:
    player = state.players[0]
    forest = player.battlefield.cards[0]
    sol_ring = player.hand.cards[0]

    mana_action = TapPermanentAction(
        player_id=0,
        turn_number=2,
        permanent=forest,
        mana=Mana.GREEN,
    )

    cast_action = CastSpellAction(
        player_id=0,
        turn_number=2,
        card=sol_ring,
        cost=ManaCost(
            generic=1,
        ),
    )

    return ManaPermanentCastPlan(
        mana_actions=(
            mana_action,
        ),
        cast_action=cast_action,
    )


def test_game_engine_creates_mana_permanent_plan() -> None:
    state = create_running_state()
    expected_plan = Mock(
        spec=ManaPermanentCastPlan,
    )

    factory = Mock(
        spec=ManaPermanentCastPlanFactory,
    )
    factory.create.return_value = expected_plan

    engine = GameEngine(
        mana_permanent_cast_plan_factory=factory,
    )

    plan = engine.create_mana_permanent_cast_plan(
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
        spec=ManaPermanentCastPlanFactory,
    )

    engine = GameEngine(
        mana_permanent_cast_plan_factory=factory,
    )

    plan = engine.create_mana_permanent_cast_plan(
        state,
        player_id=0,
    )

    assert plan is None
    factory.create.assert_not_called()


def test_game_engine_executes_mana_actions_before_spell() -> None:
    state = create_running_state()
    player = state.players[0]
    player.battlefield.add(
        create_forest_permanent()
    )
    player.hand.add(
        create_sol_ring()
    )

    plan = create_plan(state)

    factory = Mock(
        spec=ManaPermanentCastPlanFactory,
    )
    factory.create.return_value = plan

    executor = Mock(
        spec=ActionExecutor,
    )

    engine = GameEngine(
        action_executor=executor,
        mana_permanent_cast_plan_factory=factory,
    )

    executed = (
        engine
        .execute_mana_permanent_cast_if_available(
            state,
            player_id=0,
        )
    )

    assert executed is True
    assert executor.execute.call_args_list == [
        (
            (state, plan.mana_actions[0]),
            {},
        ),
        (
            (state, plan.cast_action),
            {},
        ),
    ]


def test_game_engine_returns_false_without_plan() -> None:
    state = create_running_state()

    factory = Mock(
        spec=ManaPermanentCastPlanFactory,
    )
    factory.create.return_value = None

    executor = Mock(
        spec=ActionExecutor,
    )

    engine = GameEngine(
        action_executor=executor,
        mana_permanent_cast_plan_factory=factory,
    )

    executed = (
        engine
        .execute_mana_permanent_cast_if_available(
            state,
            player_id=0,
        )
    )

    assert executed is False
    executor.execute.assert_not_called()


def test_game_engine_casts_sol_ring_with_real_executor() -> None:
    state = create_running_state()
    player = state.players[0]

    forest = create_forest_permanent()
    sol_ring = create_sol_ring()

    player.battlefield.add(forest)
    player.hand.add(sol_ring)

    executed = (
        GameEngine()
        .execute_mana_permanent_cast_if_available(
            state,
            player_id=0,
        )
    )

    assert executed is True
    assert forest.tapped is True
    assert len(player.hand) == 0
    assert len(player.battlefield) == 2

    sol_ring_permanent = next(
        permanent
        for permanent in player.battlefield
        if permanent.effective_card.name == "Sol Ring"
    )

    assert sol_ring_permanent.permanent_id == 2
    assert sol_ring_permanent.tapped is False
    assert sol_ring_permanent.summoning_sick is False
    assert player.mana_pool.total() == 0
    assert state.next_permanent_id == 3
    assert state.mana_generated == 1
    assert state.mana_spent == 1
    assert state.action_count == 2


def test_runner_executes_mana_permanent_before_kinnan() -> None:
    state = create_running_state()

    engine = Mock(
        spec=GameEngine,
    )
    execution_order: list[str] = []
    mana_cast_results = iter(
        (
            True,
            True,
            False,
        )
    )

    def execute_land(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert current_state is state
        assert player_id == 0
        execution_order.append("land")
        return True

    def execute_mana_permanent(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert current_state is state
        assert player_id == 0
        execution_order.append("mana_permanent")
        return next(mana_cast_results)

    def execute_kinnan_cast(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert current_state is state
        assert player_id == 0
        execution_order.append("kinnan_cast")
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
    (
        engine
        .execute_mana_permanent_cast_if_available
        .side_effect
    ) = execute_mana_permanent
    engine.execute_kinnan_cast_if_available.side_effect = (
        execute_kinnan_cast
    )
    (
        engine
        .execute_kinnan_activation_if_available
        .side_effect
    ) = execute_activation
    engine.advance_phase.side_effect = advance_phase

    result = GoldfishRunner(
        game_engine=engine,
        max_turns=2,
    ).run(state)

    assert execution_order == [
        "land",
        "mana_permanent",
        "mana_permanent",
        "mana_permanent",
        "kinnan_cast",
        "activation",
    ]
    assert result.kinnan_activations == 0


def test_runner_limits_mana_permanent_casts() -> None:
    state = create_running_state()

    engine = Mock(
        spec=GameEngine,
    )
    engine.execute_land_play_if_available.return_value = False
    (
        engine
        .execute_mana_permanent_cast_if_available
        .return_value
    ) = True
    engine.execute_kinnan_cast_if_available.return_value = False
    (
        engine
        .execute_kinnan_activation_if_available
        .return_value
    ) = False

    def advance_phase(
        current_state: GameState,
    ) -> None:
        current_state.phase = Phase.END

    engine.advance_phase.side_effect = advance_phase

    GoldfishRunner(
        game_engine=engine,
        max_turns=2,
        max_mana_permanent_casts_per_turn=3,
    ).run(state)

    assert (
        engine
        .execute_mana_permanent_cast_if_available
        .call_count
        == 3
    )


def test_runner_rejects_invalid_mana_cast_limit() -> None:
    engine = Mock(
        spec=GameEngine,
    )

    with pytest.raises(
        ValueError,
        match=(
            "max_mana_permanent_casts_per_turn "
            "must be at least 1"
        ),
    ):
        GoldfishRunner(
            game_engine=engine,
            max_mana_permanent_casts_per_turn=0,
        )