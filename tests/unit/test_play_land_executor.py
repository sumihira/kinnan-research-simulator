import pytest

from krs.actions.play_land import PlayLandAction
from krs.cards.card import Card
from krs.engine.action_executor import ActionExecutor
from krs.game.game_state import GameState
from krs.game.phase import Phase
from krs.game.player import Player


def create_card(
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


def create_started_main_phase_state() -> GameState:
    player = Player(player_id=0)

    return GameState(
        players=[player],
        started=True,
        phase=Phase.MAIN,
        turn_number=1,
    )


def test_play_land_moves_card_from_hand_to_battlefield() -> None:
    state = create_started_main_phase_state()
    player = state.players[0]

    forest = create_card(
        "forest-id",
        "Forest",
        "Basic Land — Forest",
    )
    player.hand.add(forest)

    executor = ActionExecutor()
    executor.execute(
        state,
        PlayLandAction(
            player_id=0,
            turn_number=1,
            card=forest,
        ),
    )

    assert len(player.hand) == 0
    assert len(player.battlefield) == 1

    permanent = player.battlefield.cards[0]

    assert permanent.card is forest
    assert permanent.owner_id == 0
    assert permanent.controller_id == 0


def test_played_land_receives_unique_permanent_id() -> None:
    state = create_started_main_phase_state()
    player = state.players[0]

    forest = create_card(
        "forest-id",
        "Forest",
        "Basic Land — Forest",
    )
    player.hand.add(forest)

    ActionExecutor().execute(
        state,
        PlayLandAction(
            player_id=0,
            turn_number=1,
            card=forest,
        ),
    )

    permanent = player.battlefield.cards[0]

    assert permanent.permanent_id == 1
    assert state.next_permanent_id == 2


def test_played_land_is_untapped_and_not_summoning_sick() -> None:
    state = create_started_main_phase_state()
    player = state.players[0]

    island = create_card(
        "island-id",
        "Island",
        "Basic Land — Island",
    )
    player.hand.add(island)

    ActionExecutor().execute(
        state,
        PlayLandAction(
            player_id=0,
            turn_number=1,
            card=island,
        ),
    )

    permanent = player.battlefield.cards[0]

    assert permanent.tapped is False
    assert permanent.summoning_sick is False
    assert permanent.entered_turn == 1


def test_play_land_increments_land_count_and_action_count() -> None:
    state = create_started_main_phase_state()
    player = state.players[0]

    forest = create_card(
        "forest-id",
        "Forest",
        "Basic Land — Forest",
    )
    player.hand.add(forest)

    ActionExecutor().execute(
        state,
        PlayLandAction(
            player_id=0,
            turn_number=1,
            card=forest,
        ),
    )

    assert player.land_played_this_turn == 1
    assert state.action_count == 1


def test_second_land_cannot_be_played_in_same_turn() -> None:
    state = create_started_main_phase_state()
    player = state.players[0]

    forest = create_card(
        "forest-id",
        "Forest",
        "Basic Land — Forest",
    )
    island = create_card(
        "island-id",
        "Island",
        "Basic Land — Island",
    )

    player.hand.add(forest)
    player.hand.add(island)

    executor = ActionExecutor()

    executor.execute(
        state,
        PlayLandAction(
            player_id=0,
            turn_number=1,
            card=forest,
        ),
    )

    with pytest.raises(
        ValueError,
        match="A land has already been played this turn",
    ):
        executor.execute(
            state,
            PlayLandAction(
                player_id=0,
                turn_number=1,
                card=island,
            ),
        )

    assert len(player.hand) == 1
    assert player.hand.cards[0] is island
    assert len(player.battlefield) == 1
    assert state.action_count == 1
    assert state.next_permanent_id == 2


def test_nonland_card_cannot_be_played_as_land() -> None:
    state = create_started_main_phase_state()
    player = state.players[0]

    sol_ring = create_card(
        "sol-ring-id",
        "Sol Ring",
        "Artifact",
    )
    player.hand.add(sol_ring)

    with pytest.raises(
        ValueError,
        match="Card is not a land: Sol Ring",
    ):
        ActionExecutor().execute(
            state,
            PlayLandAction(
                player_id=0,
                turn_number=1,
                card=sol_ring,
            ),
        )

    assert len(player.hand) == 1
    assert len(player.battlefield) == 0
    assert player.land_played_this_turn == 0
    assert state.action_count == 0
    assert state.next_permanent_id == 1


def test_card_not_in_hand_cannot_be_played() -> None:
    state = create_started_main_phase_state()

    forest = create_card(
        "forest-id",
        "Forest",
        "Basic Land — Forest",
    )

    with pytest.raises(
        ValueError,
        match="Card not found in hand: forest-id",
    ):
        ActionExecutor().execute(
            state,
            PlayLandAction(
                player_id=0,
                turn_number=1,
                card=forest,
            ),
        )


def test_land_cannot_be_played_before_game_starts() -> None:
    player = Player(player_id=0)
    forest = create_card(
        "forest-id",
        "Forest",
        "Basic Land — Forest",
    )
    player.hand.add(forest)

    state = GameState(
        players=[player],
        started=False,
        phase=Phase.MAIN,
    )

    with pytest.raises(
        ValueError,
        match="Cannot play a land before the game starts",
    ):
        ActionExecutor().execute(
            state,
            PlayLandAction(
                player_id=0,
                turn_number=1,
                card=forest,
            ),
        )


def test_land_can_only_be_played_during_main_phase() -> None:
    state = create_started_main_phase_state()
    state.phase = Phase.DRAW

    player = state.players[0]
    forest = create_card(
        "forest-id",
        "Forest",
        "Basic Land — Forest",
    )
    player.hand.add(forest)

    with pytest.raises(
        ValueError,
        match="Lands can only be played during the main phase",
    ):
        ActionExecutor().execute(
            state,
            PlayLandAction(
                player_id=0,
                turn_number=1,
                card=forest,
            ),
        )

    assert len(player.hand) == 1
    assert len(player.battlefield) == 0


def test_land_cannot_be_played_after_game_is_finished() -> None:
    state = create_started_main_phase_state()
    state.game_over = True

    player = state.players[0]
    forest = create_card(
        "forest-id",
        "Forest",
        "Basic Land — Forest",
    )
    player.hand.add(forest)

    with pytest.raises(
        ValueError,
        match="Cannot play a land in a finished game",
    ):
        ActionExecutor().execute(
            state,
            PlayLandAction(
                player_id=0,
                turn_number=1,
                card=forest,
            ),
        )