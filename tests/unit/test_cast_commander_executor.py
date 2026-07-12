import pytest

from krs.actions.cast_commander import CastCommanderAction
from krs.cards.card import Card
from krs.engine.action_executor import ActionExecutor
from krs.game.game_state import GameState
from krs.game.phase import Phase
from krs.game.player import Player
from krs.mana.mana import Mana
from krs.mana.mana_cost import ManaCost


def create_kinnan() -> Card:
    return Card(
        id="kinnan-id",
        name="Kinnan, Bonder Prodigy",
        mana_cost="{G}{U}",
        mana_value=2,
        oracle_text="",
        type_line="Legendary Creature — Human Druid",
        power=2,
        toughness=2,
    )


def create_running_state() -> GameState:
    player = Player(player_id=0)
    player.command.add(create_kinnan())

    return GameState(
        players=[player],
        started=True,
        phase=Phase.MAIN,
        turn_number=1,
    )


def create_action(
    commander: Card,
) -> CastCommanderAction:
    return CastCommanderAction(
        player_id=0,
        turn_number=1,
        card=commander,
        base_cost=ManaCost(
            green=1,
            blue=1,
        ),
    )


def test_first_commander_cast_has_no_tax() -> None:
    state = create_running_state()
    player = state.players[0]
    commander = player.command.cards[0]

    player.mana_pool.add(Mana.GREEN)
    player.mana_pool.add(Mana.BLUE)

    ActionExecutor().execute(
        state,
        create_action(commander),
    )

    assert player.mana_pool.total() == 0
    assert player.commander_cast_count == 1
    assert state.mana_spent == 2


def test_cast_commander_moves_it_to_battlefield() -> None:
    state = create_running_state()
    player = state.players[0]
    commander = player.command.cards[0]

    player.mana_pool.add(Mana.GREEN)
    player.mana_pool.add(Mana.BLUE)

    ActionExecutor().execute(
        state,
        create_action(commander),
    )

    assert len(player.command) == 0
    assert len(player.battlefield) == 1

    permanent = player.battlefield.cards[0]

    assert permanent.card is commander
    assert permanent.summoning_sick is True
    assert permanent.entered_turn == 1
    assert permanent.permanent_id == 1
    assert state.next_permanent_id == 2


def test_second_commander_cast_requires_two_generic_tax() -> None:
    state = create_running_state()
    player = state.players[0]
    commander = player.command.cards[0]

    player.commander_cast_count = 1

    player.mana_pool.add(Mana.GREEN)
    player.mana_pool.add(Mana.BLUE)
    player.mana_pool.add(Mana.COLORLESS, 2)

    ActionExecutor().execute(
        state,
        create_action(commander),
    )

    assert player.mana_pool.total() == 0
    assert player.commander_cast_count == 2
    assert state.mana_spent == 4


def test_third_commander_cast_requires_four_generic_tax() -> None:
    state = create_running_state()
    player = state.players[0]
    commander = player.command.cards[0]

    player.commander_cast_count = 2

    player.mana_pool.add(Mana.GREEN)
    player.mana_pool.add(Mana.BLUE)
    player.mana_pool.add(Mana.COLORLESS, 4)

    ActionExecutor().execute(
        state,
        create_action(commander),
    )

    assert player.commander_cast_count == 3
    assert state.mana_spent == 6


def test_commander_tax_can_be_paid_with_colored_mana() -> None:
    state = create_running_state()
    player = state.players[0]
    commander = player.command.cards[0]

    player.commander_cast_count = 1

    player.mana_pool.add(Mana.GREEN, 2)
    player.mana_pool.add(Mana.BLUE, 2)

    ActionExecutor().execute(
        state,
        create_action(commander),
    )

    assert player.mana_pool.total() == 0
    assert state.mana_spent == 4


def test_commander_cast_fails_when_tax_cannot_be_paid() -> None:
    state = create_running_state()
    player = state.players[0]
    commander = player.command.cards[0]

    player.commander_cast_count = 1

    player.mana_pool.add(Mana.GREEN)
    player.mana_pool.add(Mana.BLUE)

    with pytest.raises(
        ValueError,
        match=(
            "Commander mana cost cannot be paid for: "
            "Kinnan, Bonder Prodigy"
        ),
    ):
        ActionExecutor().execute(
            state,
            create_action(commander),
        )

    assert len(player.command) == 1
    assert len(player.battlefield) == 0
    assert player.commander_cast_count == 1
    assert player.mana_pool.total() == 2
    assert state.mana_spent == 0
    assert state.action_count == 0
    assert state.next_permanent_id == 1


def test_card_not_in_command_zone_cannot_be_cast() -> None:
    state = create_running_state()
    state.players[0].command.clear()

    commander = create_kinnan()

    with pytest.raises(
        ValueError,
        match="Commander not found in command zone: kinnan-id",
    ):
        ActionExecutor().execute(
            state,
            create_action(commander),
        )


def test_commander_can_only_be_cast_in_main_phase() -> None:
    state = create_running_state()
    state.phase = Phase.DRAW

    player = state.players[0]
    commander = player.command.cards[0]

    player.mana_pool.add(Mana.GREEN)
    player.mana_pool.add(Mana.BLUE)

    with pytest.raises(
        ValueError,
        match="Commander can only be cast during the main phase",
    ):
        ActionExecutor().execute(
            state,
            create_action(commander),
        )

    assert len(player.command) == 1
    assert player.mana_pool.total() == 2


def test_commander_cannot_be_cast_before_game_start() -> None:
    state = create_running_state()
    state.started = False

    player = state.players[0]
    commander = player.command.cards[0]

    with pytest.raises(
        ValueError,
        match="Cannot cast a commander before the game starts",
    ):
        ActionExecutor().execute(
            state,
            create_action(commander),
        )


def test_commander_cannot_be_cast_after_game_end() -> None:
    state = create_running_state()
    state.game_over = True

    player = state.players[0]
    commander = player.command.cards[0]

    with pytest.raises(
        ValueError,
        match="Cannot cast a commander in a finished game",
    ):
        ActionExecutor().execute(
            state,
            create_action(commander),
        )