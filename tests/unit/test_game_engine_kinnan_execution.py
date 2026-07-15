from __future__ import annotations

from unittest.mock import Mock

import pytest

from krs.actions.activate_kinnan import ActivateKinnanAction
from krs.ai.kinnan_action_factory import KinnanActionFactory
from krs.cards.card import Card
from krs.commanders.kinnan_ability import KINNAN_ACTIVATION_COST
from krs.engine.action_executor import ActionExecutor
from krs.engine.game_engine import GameEngine
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player


def create_card(
    *,
    card_id: str,
    name: str,
    type_line: str = "Legendary Creature — Human Druid",
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=2,
        oracle_text="",
        type_line=type_line,
    )


def create_kinnan_permanent(
    *,
    permanent_id: int = 10,
    controller_id: int = 0,
    tapped: bool = False,
    summoning_sick: bool = False,
) -> Permanent:
    return Permanent(
        permanent_id=permanent_id,
        card=create_card(
            card_id="kinnan-id",
            name="Kinnan, Bonder Prodigy",
        ),
        owner_id=controller_id,
        controller_id=controller_id,
        tapped=tapped,
        summoning_sick=summoning_sick,
        entered_turn=3,
    )


def create_non_kinnan_permanent(
    *,
    permanent_id: int = 20,
    controller_id: int = 0,
) -> Permanent:
    return Permanent(
        permanent_id=permanent_id,
        card=create_card(
            card_id="other-id",
            name="Llanowar Elves",
            type_line="Creature — Elf Druid",
        ),
        owner_id=controller_id,
        controller_id=controller_id,
        entered_turn=3,
    )


def create_running_state() -> GameState:
    return GameState(
        players=[
            Player(player_id=0),
        ],
        started=True,
        game_over=False,
        phase=Phase.MAIN,
        turn_number=4,
    )


def configure_mana_payment(
    player: Player,
    *,
    can_pay: bool,
) -> Mock:
    mana_pool = Mock()
    mana_pool.can_pay.return_value = can_pay
    player.mana_pool = mana_pool
    return mana_pool


def test_find_activatable_kinnan_returns_controlled_kinnan() -> None:
    state = create_running_state()
    player = state.players[0]
    kinnan = create_kinnan_permanent()

    player.battlefield.add(
        create_non_kinnan_permanent(),
    )
    player.battlefield.add(kinnan)

    mana_pool = configure_mana_payment(
        player,
        can_pay=True,
    )

    engine = GameEngine()

    result = engine.find_activatable_kinnan(
        state,
        player_id=0,
    )

    mana_pool.can_pay.assert_called_once_with(
        KINNAN_ACTIVATION_COST,
    )
    assert result is kinnan


def test_find_activatable_kinnan_returns_none_without_kinnan() -> None:
    state = create_running_state()
    player = state.players[0]

    player.battlefield.add(
        create_non_kinnan_permanent(),
    )

    configure_mana_payment(
        player,
        can_pay=True,
    )

    engine = GameEngine()

    result = engine.find_activatable_kinnan(
        state,
        player_id=0,
    )

    assert result is None


def test_find_activatable_kinnan_returns_none_without_enough_mana() -> None:
    state = create_running_state()
    player = state.players[0]
    kinnan = create_kinnan_permanent()

    player.battlefield.add(kinnan)

    mana_pool = configure_mana_payment(
        player,
        can_pay=False,
    )

    engine = GameEngine()

    result = engine.find_activatable_kinnan(
        state,
        player_id=0,
    )

    mana_pool.can_pay.assert_called_once_with(
        KINNAN_ACTIVATION_COST,
    )
    assert result is None


def test_find_activatable_kinnan_ignores_uncontrolled_kinnan() -> None:
    state = create_running_state()
    player = state.players[0]

    uncontrolled_kinnan = create_kinnan_permanent(
        controller_id=1,
    )
    player.battlefield.add(uncontrolled_kinnan)

    configure_mana_payment(
        player,
        can_pay=True,
    )

    engine = GameEngine()

    result = engine.find_activatable_kinnan(
        state,
        player_id=0,
    )

    assert result is None


def test_find_activatable_kinnan_allows_tapped_kinnan() -> None:
    state = create_running_state()
    player = state.players[0]

    tapped_kinnan = create_kinnan_permanent(
        tapped=True,
    )
    player.battlefield.add(tapped_kinnan)

    configure_mana_payment(
        player,
        can_pay=True,
    )

    engine = GameEngine()

    result = engine.find_activatable_kinnan(
        state,
        player_id=0,
    )

    assert result is tapped_kinnan


def test_find_activatable_kinnan_allows_summoning_sick_kinnan() -> None:
    state = create_running_state()
    player = state.players[0]

    summoning_sick_kinnan = create_kinnan_permanent(
        summoning_sick=True,
    )
    player.battlefield.add(summoning_sick_kinnan)

    configure_mana_payment(
        player,
        can_pay=True,
    )

    engine = GameEngine()

    result = engine.find_activatable_kinnan(
        state,
        player_id=0,
    )

    assert result is summoning_sick_kinnan


def test_execute_kinnan_activation_if_available_executes_action() -> None:
    state = create_running_state()
    player = state.players[0]
    kinnan = create_kinnan_permanent(
        permanent_id=15,
    )

    player.battlefield.add(kinnan)

    configure_mana_payment(
        player,
        can_pay=True,
    )

    expected_action = ActivateKinnanAction(
        player_id=0,
        turn_number=4,
        source_permanent_id=15,
        selected_card_id=None,
    )

    action_factory = Mock(
        spec=KinnanActionFactory,
    )
    action_factory.create.return_value = expected_action

    action_executor = Mock(
        spec=ActionExecutor,
    )

    engine = GameEngine(
        action_executor=action_executor,
        kinnan_action_factory=action_factory,
    )

    executed = engine.execute_kinnan_activation_if_available(
        state,
        player_id=0,
    )

    action_factory.create.assert_called_once_with(
        state=state,
        player_id=0,
        source_permanent_id=15,
    )
    action_executor.execute.assert_called_once_with(
        state,
        expected_action,
    )
    assert executed is True


def test_execute_kinnan_activation_if_available_does_nothing_without_mana(
) -> None:
    state = create_running_state()
    player = state.players[0]

    player.battlefield.add(
        create_kinnan_permanent(),
    )

    configure_mana_payment(
        player,
        can_pay=False,
    )

    action_factory = Mock(
        spec=KinnanActionFactory,
    )
    action_executor = Mock(
        spec=ActionExecutor,
    )

    engine = GameEngine(
        action_executor=action_executor,
        kinnan_action_factory=action_factory,
    )

    executed = engine.execute_kinnan_activation_if_available(
        state,
        player_id=0,
    )

    action_factory.create.assert_not_called()
    action_executor.execute.assert_not_called()
    assert executed is False


def test_execute_kinnan_activation_if_available_does_nothing_without_kinnan(
) -> None:
    state = create_running_state()
    player = state.players[0]

    configure_mana_payment(
        player,
        can_pay=True,
    )

    action_factory = Mock(
        spec=KinnanActionFactory,
    )
    action_executor = Mock(
        spec=ActionExecutor,
    )

    engine = GameEngine(
        action_executor=action_executor,
        kinnan_action_factory=action_factory,
    )

    executed = engine.execute_kinnan_activation_if_available(
        state,
        player_id=0,
    )

    action_factory.create.assert_not_called()
    action_executor.execute.assert_not_called()
    assert executed is False


def test_find_activatable_kinnan_rejects_unknown_player() -> None:
    state = create_running_state()
    engine = GameEngine()

    with pytest.raises(
        ValueError,
        match="Player not found: 99",
    ):
        engine.find_activatable_kinnan(
            state,
            player_id=99,
        )


def test_find_activatable_kinnan_rejects_unstarted_game() -> None:
    state = create_running_state()
    state.started = False

    engine = GameEngine()

    with pytest.raises(
        ValueError,
        match="Game has not started.",
    ):
        engine.find_activatable_kinnan(
            state,
            player_id=0,
        )


def test_find_activatable_kinnan_rejects_finished_game() -> None:
    state = create_running_state()
    state.game_over = True

    engine = GameEngine()

    with pytest.raises(
        ValueError,
        match="Game has already finished.",
    ):
        engine.find_activatable_kinnan(
            state,
            player_id=0,
        )