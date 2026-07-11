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


def card_names(cards) -> list[str]:
    return [card.name for card in cards]


def test_start_game_draws_seven_cards() -> None:
    player = create_player_with_library()
    state = GameState(
        players=[player],
        seed=12345,
    )
    engine = GameEngine()

    engine.start_game(state)

    assert len(player.hand) == 7
    assert len(player.library) == 13


def test_start_game_preserves_total_card_count() -> None:
    player = create_player_with_library()
    state = GameState(
        players=[player],
        seed=12345,
    )
    engine = GameEngine()

    engine.start_game(state)

    total_cards = len(player.hand) + len(player.library)

    assert total_cards == 20


def test_start_game_is_reproducible_with_same_seed() -> None:
    first_player = create_player_with_library()
    second_player = create_player_with_library()

    first_state = GameState(
        players=[first_player],
        seed=12345,
    )
    second_state = GameState(
        players=[second_player],
        seed=12345,
    )

    first_engine = GameEngine()
    second_engine = GameEngine()

    first_engine.start_game(first_state)
    second_engine.start_game(second_state)

    assert card_names(first_player.hand) == card_names(
        second_player.hand
    )
    assert card_names(first_player.library) == card_names(
        second_player.library
    )


def test_start_game_usually_differs_with_different_seeds() -> None:
    first_player = create_player_with_library()
    second_player = create_player_with_library()

    first_state = GameState(
        players=[first_player],
        seed=12345,
    )
    second_state = GameState(
        players=[second_player],
        seed=54321,
    )

    first_engine = GameEngine()
    second_engine = GameEngine()

    first_engine.start_game(first_state)
    second_engine.start_game(second_state)

    assert card_names(first_player.hand) != card_names(
        second_player.hand
    )


def test_start_game_shuffles_before_drawing() -> None:
    player = create_player_with_library()
    original_order = card_names(player.library)

    state = GameState(
        players=[player],
        seed=12345,
    )
    engine = GameEngine()

    engine.start_game(state)

    resulting_order = [
        *card_names(player.hand),
        *card_names(player.library),
    ]

    assert resulting_order != original_order
    assert sorted(resulting_order) == sorted(original_order)


def test_start_game_increments_action_count_once_per_player() -> None:
    player = create_player_with_library()
    state = GameState(
        players=[player],
        seed=12345,
    )
    engine = GameEngine()

    engine.start_game(state)

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

    state = GameState(
        players=[first, second],
        seed=12345,
    )
    engine = GameEngine()

    engine.start_game(state)

    assert len(first.hand) == 7
    assert len(second.hand) == 7
    assert len(first.library) == 13
    assert len(second.library) == 13
    assert state.action_count == 2


def test_each_player_uses_different_derived_seed() -> None:
    first = create_player_with_library(
        player_id=0,
        library_size=20,
    )
    second = create_player_with_library(
        player_id=1,
        library_size=20,
    )

    state = GameState(
        players=[first, second],
        seed=12345,
    )
    engine = GameEngine()

    engine.start_game(state)

    assert card_names(first.hand) != card_names(second.hand)


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
        seed=12345,
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
    original_order = card_names(player.library)

    state = GameState(
        players=[player],
        seed=12345,
    )
    engine = GameEngine()

    with pytest.raises(
        IndexError,
        match="Not enough cards in library",
    ):
        engine.start_game(state)

    assert len(player.hand) == 0
    assert card_names(player.library) == original_order
    assert state.action_count == 0
    assert state.started is False


def test_start_game_is_atomic_across_multiple_players() -> None:
    valid_player = create_player_with_library(
        player_id=0,
        library_size=20,
    )
    invalid_player = create_player_with_library(
        player_id=1,
        library_size=6,
    )

    valid_original_order = card_names(valid_player.library)
    invalid_original_order = card_names(invalid_player.library)

    state = GameState(
        players=[valid_player, invalid_player],
        seed=12345,
    )
    engine = GameEngine()

    with pytest.raises(
        IndexError,
        match="Not enough cards in library",
    ):
        engine.start_game(state)

    assert len(valid_player.hand) == 0
    assert len(invalid_player.hand) == 0

    assert card_names(valid_player.library) == valid_original_order
    assert card_names(invalid_player.library) == invalid_original_order

    assert state.action_count == 0
    assert state.started is False


def test_start_game_marks_state_as_started() -> None:
    player = create_player_with_library()
    state = GameState(
        players=[player],
        seed=12345,
    )
    engine = GameEngine()

    engine.start_game(state)

    assert state.started is True


def test_start_game_cannot_be_called_twice() -> None:
    player = create_player_with_library()
    state = GameState(
        players=[player],
        seed=12345,
    )
    engine = GameEngine()

    engine.start_game(state)

    first_hand = card_names(player.hand)
    remaining_library = card_names(player.library)

    with pytest.raises(
        ValueError,
        match="Game has already started",
    ):
        engine.start_game(state)

    assert card_names(player.hand) == first_hand
    assert card_names(player.library) == remaining_library
    assert state.action_count == 1