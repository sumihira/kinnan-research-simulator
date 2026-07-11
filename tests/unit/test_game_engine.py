import pytest

from krs.cards.card import Card
from krs.engine.game_engine import GameEngine
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


def create_player_with_library(
    player_id: int = 0,
    library_size: int = 20,
) -> Player:
    player = Player(player_id=player_id)

    player.library.cards.extend(
        create_card(index)
        for index in range(library_size)
    )

    return player


def test_start_game_draws_seven_cards() -> None:
    player = create_player_with_library()
    state = GameState(players=[player])
    engine = GameEngine()

    engine.start_game(state)

    assert len(player.hand) == 7
    assert len(player.library) == 13


def test_start_game_draws_top_seven_cards_in_order() -> None:
    player = create_player_with_library()
    state = GameState(players=[player])
    engine = GameEngine()

    engine.start_game(state)

    assert [card.name for card in player.hand] == [
        "Card 0",
        "Card 1",
        "Card 2",
        "Card 3",
        "Card 4",
        "Card 5",
        "Card 6",
    ]

    assert [card.name for card in player.library][:3] == [
        "Card 7",
        "Card 8",
        "Card 9",
    ]


def test_start_game_increments_action_count_once_per_player() -> None:
    player = create_player_with_library()
    state = GameState(players=[player])
    engine = GameEngine()

    engine.start_game(state)

    # 7枚をまとめた1つのDrawActionとして数える
    assert state.action_count == 1


def test_start_game_draws_for_each_player() -> None:
    first = create_player_with_library(
        player_id=0,
        library_size=20,
    )
    second = create_player_with_library(
        player_id=1,
        library_size=20,
    )

    state = GameState(players=[first, second])
    engine = GameEngine()

    engine.start_game(state)

    assert len(first.hand) == 7
    assert len(second.hand) == 7
    assert len(first.library) == 13
    assert len(second.library) == 13
    assert state.action_count == 2


def test_start_game_rejects_state_without_players() -> None:
    state = GameState()
    engine = GameEngine()

    with pytest.raises(
        ValueError,
        match="Cannot start a game without players",
    ):
        engine.start_game(state)


def test_start_game_rejects_finished_game() -> None:
    player = create_player_with_library()
    state = GameState(
        players=[player],
        game_over=True,
    )
    engine = GameEngine()

    with pytest.raises(
        ValueError,
        match="Cannot start a finished game",
    ):
        engine.start_game(state)


def test_start_game_is_atomic_when_library_has_too_few_cards() -> None:
    player = create_player_with_library(
        library_size=6,
    )
    state = GameState(players=[player])
    engine = GameEngine()

    with pytest.raises(
        IndexError,
        match="Not enough cards in library",
    ):
        engine.start_game(state)

    assert len(player.hand) == 0
    assert len(player.library) == 6
    assert state.action_count == 0

def test_start_game_marks_state_as_started() -> None:
    player = create_player_with_library()
    state = GameState(players=[player])
    engine = GameEngine()

    engine.start_game(state)

    assert state.started is True


def test_start_game_cannot_be_called_twice() -> None:
    player = create_player_with_library()
    state = GameState(players=[player])
    engine = GameEngine()

    engine.start_game(state)

    with pytest.raises(
        ValueError,
        match="Game has already started",
    ):
        engine.start_game(state)

    assert len(player.hand) == 7
    assert len(player.library) == 13