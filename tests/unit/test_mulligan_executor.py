import pytest

from krs.actions.bottom_cards import BottomCardsAction
from krs.actions.mulligan import MulliganAction
from krs.cards.card import Card
from krs.engine.action_executor import ActionExecutor
from krs.game.game_state import GameState
from krs.game.player import Player


def create_card(index: int) -> Card:
    return Card(
        id=f"card-{index}",
        name=f"Card {index}",
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line="Artifact",
    )


def create_started_state(
    *,
    hand_size: int = 7,
    library_size: int = 13,
    seed: int = 12345,
) -> GameState:
    player = Player(player_id=0)

    player.hand.cards.extend(
        create_card(index)
        for index in range(hand_size)
    )

    player.library.cards.extend(
        create_card(index)
        for index in range(
            hand_size,
            hand_size + library_size,
        )
    )

    return GameState(
        players=[player],
        started=True,
        seed=seed,
    )


def card_ids(cards) -> list[str]:
    return [card.id for card in cards]


def test_mulligan_draws_new_seven_card_hand() -> None:
    state = create_started_state()
    player = state.players[0]
    executor = ActionExecutor()

    executor.execute(
        state,
        MulliganAction(
            player_id=0,
            turn_number=1,
        ),
    )

    assert len(player.hand) == 7
    assert len(player.library) == 13
    assert player.mulligan_count == 1
    assert state.action_count == 1


def test_mulligan_preserves_total_card_count() -> None:
    state = create_started_state()
    player = state.players[0]
    executor = ActionExecutor()

    executor.execute(
        state,
        MulliganAction(
            player_id=0,
            turn_number=1,
        ),
    )

    assert len(player.hand) + len(player.library) == 20


def test_mulligan_is_reproducible_with_same_seed() -> None:
    first = create_started_state(seed=12345)
    second = create_started_state(seed=12345)

    first_executor = ActionExecutor()
    second_executor = ActionExecutor()

    action = MulliganAction(
        player_id=0,
        turn_number=1,
    )

    first_executor.execute(first, action)
    second_executor.execute(second, action)

    assert card_ids(first.players[0].hand) == card_ids(
        second.players[0].hand
    )


def test_second_mulligan_increments_count_again() -> None:
    state = create_started_state()
    player = state.players[0]
    executor = ActionExecutor()

    executor.execute(
        state,
        MulliganAction(
            player_id=0,
            turn_number=1,
        ),
    )
    executor.execute(
        state,
        MulliganAction(
            player_id=0,
            turn_number=1,
        ),
    )

    assert player.mulligan_count == 2
    assert len(player.hand) == 7


def test_bottom_one_card_after_one_mulligan() -> None:
    state = create_started_state()
    player = state.players[0]
    executor = ActionExecutor()

    executor.execute(
        state,
        MulliganAction(
            player_id=0,
            turn_number=1,
        ),
    )

    selected_card = player.hand.cards[0]

    executor.execute(
        state,
        BottomCardsAction(
            player_id=0,
            turn_number=1,
            card_ids=(selected_card.id,),
        ),
    )

    assert len(player.hand) == 6
    assert len(player.library) == 14
    assert player.library.cards[-1] == selected_card
    assert state.action_count == 2


def test_bottom_two_cards_after_two_mulligans() -> None:
    state = create_started_state()
    player = state.players[0]
    executor = ActionExecutor()

    for _ in range(2):
        executor.execute(
            state,
            MulliganAction(
                player_id=0,
                turn_number=1,
            ),
        )

    selected_cards = player.hand.cards[:2]

    executor.execute(
        state,
        BottomCardsAction(
            player_id=0,
            turn_number=1,
            card_ids=tuple(
                card.id
                for card in selected_cards
            ),
        ),
    )

    assert len(player.hand) == 5
    assert len(player.library) == 15
    assert player.library.cards[-2:] == selected_cards


def test_bottom_count_must_equal_mulligan_count() -> None:
    state = create_started_state()
    player = state.players[0]
    executor = ActionExecutor()

    executor.execute(
        state,
        MulliganAction(
            player_id=0,
            turn_number=1,
        ),
    )

    selected_cards = player.hand.cards[:2]

    with pytest.raises(
        ValueError,
        match="must equal mulligan count",
    ):
        executor.execute(
            state,
            BottomCardsAction(
                player_id=0,
                turn_number=1,
                card_ids=tuple(
                    card.id
                    for card in selected_cards
                ),
            ),
        )

    assert len(player.hand) == 7
    assert len(player.library) == 13


def test_bottom_rejects_card_not_in_hand() -> None:
    state = create_started_state()
    player = state.players[0]
    executor = ActionExecutor()

    executor.execute(
        state,
        MulliganAction(
            player_id=0,
            turn_number=1,
        ),
    )

    with pytest.raises(
        ValueError,
        match="Cards not found in hand",
    ):
        executor.execute(
            state,
            BottomCardsAction(
                player_id=0,
                turn_number=1,
                card_ids=("missing-card",),
            ),
        )

    assert len(player.hand) == 7
    assert len(player.library) == 13


def test_failed_mulligan_is_atomic() -> None:
    state = create_started_state(
        hand_size=3,
        library_size=3,
    )
    player = state.players[0]
    original_hand = card_ids(player.hand)
    original_library = card_ids(player.library)
    executor = ActionExecutor()

    with pytest.raises(
        IndexError,
        match="Not enough cards to draw a new opening hand",
    ):
        executor.execute(
            state,
            MulliganAction(
                player_id=0,
                turn_number=1,
            ),
        )

    assert card_ids(player.hand) == original_hand
    assert card_ids(player.library) == original_library
    assert player.mulligan_count == 0
    assert state.action_count == 0