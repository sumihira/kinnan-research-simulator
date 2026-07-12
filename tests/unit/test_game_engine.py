import pytest

from krs.cards.card import Card
from krs.engine.game_engine import GameEngine
from krs.game.game_state import GameState
from krs.game.player import Player
from krs.game.permanent import Permanent
from pathlib import Path
from krs.ai.strategy_factory import StrategyFactory


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

def add_kinnan_to_battlefield(
    player: Player,
) -> Permanent:
    kinnan = Card(
        id="kinnan-id",
        name="Kinnan, Bonder Prodigy",
        mana_cost="{G}{U}",
        mana_value=2,
        oracle_text="",
        type_line="Legendary Creature — Human Druid",
        power="2",
        toughness="2",
    )

    permanent = Permanent(
        permanent_id=1,
        card=kinnan,
        owner_id=player.player_id,
        controller_id=player.player_id,
        summoning_sick=True,
        entered_turn=1,
    )

    player.battlefield.add(permanent)

    return permanent

def test_create_kinnan_action_selects_highest_mana_value_hit() -> None:
    player = Player(player_id=0)
    kinnan = add_kinnan_to_battlefield(player)

    small = Card(
        id="small-id",
        name="Small Creature",
        mana_cost="{2}",
        mana_value=2,
        oracle_text="",
        type_line="Creature — Beast",
    )
    large = Card(
        id="large-id",
        name="Large Creature",
        mana_cost="{7}",
        mana_value=7,
        oracle_text="",
        type_line="Creature — Whale",
    )

    player.library.cards.extend(
        [
            small,
            large,
        ]
    )

    state = GameState(
        players=[player],
        started=True,
        turn_number=3,
    )

    action = GameEngine().create_kinnan_activation_action(
        state,
        player_id=0,
        source_permanent_id=kinnan.permanent_id,
    )

    assert action.player_id == 0
    assert action.turn_number == 3
    assert action.source_permanent_id == 1
    assert action.selected_card_id == large.id

def test_create_kinnan_action_selects_none_without_valid_hit() -> None:
    player = Player(player_id=0)
    kinnan = add_kinnan_to_battlefield(player)

    player.library.cards.extend(
        [
            Card(
                id="artifact-id",
                name="Artifact",
                mana_cost="{4}",
                mana_value=4,
                oracle_text="",
                type_line="Artifact",
            ),
            Card(
                id="human-id",
                name="Human",
                mana_cost="{6}",
                mana_value=6,
                oracle_text="",
                type_line="Creature — Human",
            ),
        ]
    )

    state = GameState(
        players=[player],
        started=True,
        turn_number=3,
    )

    action = GameEngine().create_kinnan_activation_action(
        state,
        player_id=0,
        source_permanent_id=kinnan.permanent_id,
    )

    assert action.selected_card_id is None

def test_create_kinnan_action_only_considers_top_five() -> None:
    player = Player(player_id=0)
    kinnan = add_kinnan_to_battlefield(player)

    top_five = [
        Card(
            id=f"artifact-{index}",
            name=f"Artifact {index}",
            mana_cost="{1}",
            mana_value=1,
            oracle_text="",
            type_line="Artifact",
        )
        for index in range(5)
    ]

    sixth = Card(
        id="sixth-creature",
        name="Sixth Creature",
        mana_cost="{10}",
        mana_value=10,
        oracle_text="",
        type_line="Creature — Beast",
    )

    player.library.cards.extend(
        [
            *top_five,
            sixth,
        ]
    )

    state = GameState(
        players=[player],
        started=True,
        turn_number=3,
    )

    action = GameEngine().create_kinnan_activation_action(
        state,
        player_id=0,
        source_permanent_id=kinnan.permanent_id,
    )

    assert action.selected_card_id is None

def test_create_kinnan_action_does_not_modify_game_state() -> None:
    player = Player(player_id=0)
    kinnan = add_kinnan_to_battlefield(player)

    creature = Card(
        id="creature-id",
        name="Creature",
        mana_cost="{5}",
        mana_value=5,
        oracle_text="",
        type_line="Creature — Beast",
    )

    player.library.cards.append(creature)

    state = GameState(
        players=[player],
        started=True,
        turn_number=3,
    )

    original_library = list(player.library)
    original_action_count = state.action_count

    GameEngine().create_kinnan_activation_action(
        state,
        player_id=0,
        source_permanent_id=kinnan.permanent_id,
    )

    assert list(player.library) == original_library
    assert state.action_count == original_action_count

def test_create_kinnan_action_rejects_unknown_player() -> None:
    state = GameState(
        players=[Player(player_id=0)],
        started=True,
    )

    with pytest.raises(
        ValueError,
        match="Player not found: 99",
    ):
        GameEngine().create_kinnan_activation_action(
            state,
            player_id=99,
            source_permanent_id=1,
        )

def write_test_strategy(
    directory: Path,
    *,
    name: str,
    preferred_card_id: str,
) -> None:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = directory / f"{name}.yaml"

    path.write_text(
        f"""
name: {name}

weights:
  mana_value: 1
  mana_ability: 0
  untap: 0
  copy: 0
  combo: 0

custom_scores:
  {preferred_card_id}: 20

combo_card_ids: []
""",
        encoding="utf-8",
    )

def test_game_engine_can_be_created_from_strategy(
    tmp_path: Path,
) -> None:
    strategy_directory = tmp_path / "strategies"

    write_test_strategy(
        strategy_directory,
        name="preferred",
        preferred_card_id="small-id",
    )

    factory = StrategyFactory(
        strategy_directory=strategy_directory
    )

    engine = GameEngine.from_strategy(
        "preferred",
        strategy_factory=factory,
    )

    player = Player(player_id=0)
    kinnan = add_kinnan_to_battlefield(player)

    large = Card(
        id="large-id",
        name="Large Creature",
        mana_cost="{8}",
        mana_value=8,
        oracle_text="",
        type_line="Creature — Beast",
    )
    small = Card(
        id="small-id",
        name="Preferred Creature",
        mana_cost="{2}",
        mana_value=2,
        oracle_text="",
        type_line="Creature — Beast",
    )

    player.library.cards.extend(
        [
            large,
            small,
        ]
    )

    state = GameState(
        players=[player],
        started=True,
        turn_number=3,
    )

    action = engine.create_kinnan_activation_action(
        state,
        player_id=0,
        source_permanent_id=kinnan.permanent_id,
    )

    assert action.selected_card_id == small.id

def test_game_engine_rejects_unknown_strategy(
    tmp_path: Path,
) -> None:
    factory = StrategyFactory(
        strategy_directory=tmp_path
    )

    with pytest.raises(
        FileNotFoundError,
        match="Strategy file not found",
    ):
        GameEngine.from_strategy(
            "missing",
            strategy_factory=factory,
        )