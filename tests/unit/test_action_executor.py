import pytest

from krs.actions.draw import DrawAction
from krs.actions.pass_priority import PassPriorityAction
from krs.cards.card import Card
from krs.engine.action_executor import ActionExecutor
from krs.game.game_state import GameState
from krs.game.player import Player


def create_card(
    card_id: str,
    name: str,
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line="Artifact",
    )


def create_state_with_library() -> GameState:
    player = Player(player_id=0)
    player.library.cards.extend(
        [
            create_card("forest", "Forest"),
            create_card("island", "Island"),
            create_card("sol-ring", "Sol Ring"),
        ]
    )

    return GameState(players=[player])


def test_execute_draw_moves_top_card_to_hand() -> None:
    state = create_state_with_library()
    executor = ActionExecutor()

    executor.execute(
        state,
        DrawAction(
            player_id=0,
            turn_number=1,
            amount=1,
        ),
    )

    player = state.players[0]

    assert [card.name for card in player.hand] == [
        "Forest",
    ]
    assert [card.name for card in player.library] == [
        "Island",
        "Sol Ring",
    ]


def test_execute_draw_multiple_cards() -> None:
    state = create_state_with_library()
    executor = ActionExecutor()

    executor.execute(
        state,
        DrawAction(
            player_id=0,
            turn_number=1,
            amount=2,
        ),
    )

    player = state.players[0]

    assert [card.name for card in player.hand] == [
        "Forest",
        "Island",
    ]
    assert [card.name for card in player.library] == [
        "Sol Ring",
    ]


def test_execute_draw_increments_action_count() -> None:
    state = create_state_with_library()
    executor = ActionExecutor()

    executor.execute(
        state,
        DrawAction(
            player_id=0,
            turn_number=1,
        ),
    )

    assert state.action_count == 1


def test_execute_draw_for_correct_player() -> None:
    first = Player(player_id=0)
    second = Player(player_id=1)

    first.library.cards.append(
        create_card("forest", "Forest")
    )
    second.library.cards.append(
        create_card("island", "Island")
    )

    state = GameState(players=[first, second])
    executor = ActionExecutor()

    executor.execute(
        state,
        DrawAction(
            player_id=1,
            turn_number=1,
        ),
    )

    assert len(first.hand) == 0
    assert [card.name for card in second.hand] == [
        "Island",
    ]


def test_execute_draw_rejects_unknown_player() -> None:
    state = create_state_with_library()
    executor = ActionExecutor()

    with pytest.raises(
        ValueError,
        match="Player not found: 99",
    ):
        executor.execute(
            state,
            DrawAction(
                player_id=99,
                turn_number=1,
            ),
        )


def test_failed_draw_does_not_increment_action_count() -> None:
    state = GameState(
        players=[Player(player_id=0)]
    )
    executor = ActionExecutor()

    with pytest.raises(IndexError):
        executor.execute(
            state,
            DrawAction(
                player_id=0,
                turn_number=1,
            ),
        )

    assert state.action_count == 0
    assert len(state.players[0].hand) == 0


def test_unsupported_action_raises_error() -> None:
    state = create_state_with_library()
    executor = ActionExecutor()

    action = PassPriorityAction(
        player_id=0,
        turn_number=1,
    )

    with pytest.raises(
        NotImplementedError,
        match="Unsupported action type",
    ):
        executor.execute(state, action)