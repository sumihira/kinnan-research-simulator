import pytest

from krs.actions.return_commander import ReturnCommanderAction
from krs.cards.card import Card
from krs.engine.action_executor import ActionExecutor
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player


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
    kinnan = create_kinnan()

    player = Player(
        player_id=0,
        commander_card_id=kinnan.id,
    )

    player.battlefield.add(
        Permanent(
            permanent_id=1,
            card=kinnan,
            owner_id=0,
            controller_id=0,
            summoning_sick=True,
            entered_turn=1,
        )
    )

    return GameState(
        players=[player],
        started=True,
        phase=Phase.MAIN,
        turn_number=1,
        next_permanent_id=2,
    )


def test_return_commander_moves_card_to_command_zone() -> None:
    state = create_running_state()
    player = state.players[0]

    ActionExecutor().execute(
        state,
        ReturnCommanderAction(
            player_id=0,
            turn_number=1,
            permanent_id=1,
        ),
    )

    assert len(player.battlefield) == 0
    assert len(player.command) == 1
    assert player.command.cards[0].name == (
        "Kinnan, Bonder Prodigy"
    )


def test_return_commander_preserves_card_identity() -> None:
    state = create_running_state()
    player = state.players[0]

    permanent = player.battlefield.cards[0]
    original_card = permanent.card

    ActionExecutor().execute(
        state,
        ReturnCommanderAction(
            player_id=0,
            turn_number=1,
            permanent_id=1,
        ),
    )

    assert player.command.cards[0] is original_card


def test_return_commander_does_not_reset_cast_count() -> None:
    state = create_running_state()
    player = state.players[0]
    player.commander_cast_count = 1

    ActionExecutor().execute(
        state,
        ReturnCommanderAction(
            player_id=0,
            turn_number=1,
            permanent_id=1,
        ),
    )

    assert player.commander_cast_count == 1


def test_return_commander_increments_action_count() -> None:
    state = create_running_state()

    ActionExecutor().execute(
        state,
        ReturnCommanderAction(
            player_id=0,
            turn_number=1,
            permanent_id=1,
        ),
    )

    assert state.action_count == 1


def test_return_commander_does_not_reuse_permanent_id() -> None:
    state = create_running_state()

    ActionExecutor().execute(
        state,
        ReturnCommanderAction(
            player_id=0,
            turn_number=1,
            permanent_id=1,
        ),
    )

    assert state.next_permanent_id == 2

def test_noncommander_cannot_be_returned_to_command_zone() -> None:
    state = create_running_state()
    player = state.players[0]

    sol_ring = Card(
        id="sol-ring-id",
        name="Sol Ring",
        mana_cost="{1}",
        mana_value=1,
        oracle_text="",
        type_line="Artifact",
    )

    player.battlefield.add(
        Permanent(
            permanent_id=2,
            card=sol_ring,
            owner_id=0,
            controller_id=0,
            summoning_sick=False,
        )
    )

    with pytest.raises(
        ValueError,
        match="Permanent is not the player's commander: Sol Ring",
    ):
        ActionExecutor().execute(
            state,
            ReturnCommanderAction(
                player_id=0,
                turn_number=1,
                permanent_id=2,
            ),
        )

    assert len(player.battlefield) == 2
    assert len(player.command) == 0
    assert state.action_count == 0

def test_missing_permanent_cannot_be_returned() -> None:
    state = create_running_state()

    with pytest.raises(
        ValueError,
        match="Permanent not found on battlefield: 99",
    ):
        ActionExecutor().execute(
            state,
            ReturnCommanderAction(
                player_id=0,
                turn_number=1,
                permanent_id=99,
            ),
        )

def test_only_owner_can_return_commander() -> None:
    kinnan = create_kinnan()

    owner = Player(
        player_id=0,
        commander_card_id=kinnan.id,
    )
    controller = Player(player_id=1)

    controller.battlefield.add(
        Permanent(
            permanent_id=1,
            card=kinnan,
            owner_id=0,
            controller_id=1,
        )
    )

    state = GameState(
        players=[owner, controller],
        started=True,
        phase=Phase.MAIN,
    )

    with pytest.raises(
        ValueError,
        match="Only the commander owner may return it",
    ):
        ActionExecutor().execute(
            state,
            ReturnCommanderAction(
                player_id=1,
                turn_number=1,
                permanent_id=1,
            ),
        )

    ActionExecutor().execute(
        state,
        ReturnCommanderAction(
            player_id=0,
            turn_number=1,
            permanent_id=1,
        ),
    )

    assert len(controller.battlefield) == 0
    assert list(owner.command) == [kinnan]

def test_commander_cannot_return_before_game_start() -> None:
    state = create_running_state()
    state.started = False

    with pytest.raises(
        ValueError,
        match="Cannot return a commander before the game starts",
    ):
        ActionExecutor().execute(
            state,
            ReturnCommanderAction(
                player_id=0,
                turn_number=1,
                permanent_id=1,
            ),
        )


def test_commander_cannot_return_after_game_end() -> None:
    state = create_running_state()
    state.game_over = True

    with pytest.raises(
        ValueError,
        match="Cannot return a commander in a finished game",
    ):
        ActionExecutor().execute(
            state,
            ReturnCommanderAction(
                player_id=0,
                turn_number=1,
                permanent_id=1,
            ),
        )