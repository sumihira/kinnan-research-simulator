from krs.cards.card import Card
from krs.decks.deck import Deck
from krs.simulation.game_state_factory import (
    GameStateFactory,
)


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


def create_deck() -> Deck:
    commander = create_card(
        "kinnan-id",
        "Kinnan, Bonder Prodigy",
        "Legendary Creature — Human Druid",
    )

    cards = [
        create_card(
            "sol-ring-id",
            "Sol Ring",
            "Artifact",
        ),
        create_card(
            "forest-id",
            "Forest",
            "Basic Land — Forest",
        ),
    ]

    return Deck(
        name="Kinnan Test",
        commander=commander,
        cards=cards,
    )


def test_creates_single_player_goldfish_state() -> None:
    deck = create_deck()

    state = GameStateFactory().create_goldfish_state(
        deck
    )

    assert len(state.players) == 1
    assert state.players[0].player_id == 0
    assert state.players[0].name == "Player"


def test_places_commander_in_command_zone() -> None:
    deck = create_deck()

    state = GameStateFactory().create_goldfish_state(
        deck
    )

    player = state.players[0]

    assert list(player.command) == [
        deck.commander,
    ]
    assert player.commander_card_id == (
        deck.commander.id
    )


def test_places_main_deck_in_library() -> None:
    deck = create_deck()

    state = GameStateFactory().create_goldfish_state(
        deck
    )

    player = state.players[0]

    assert list(player.library) == deck.cards
    assert len(player.hand) == 0
    assert len(player.battlefield) == 0


def test_preserves_game_id_and_seed() -> None:
    deck = create_deck()

    state = GameStateFactory().create_goldfish_state(
        deck,
        game_id=42,
        seed=12345,
    )

    assert state.game_id == 42
    assert state.seed == 12345


def test_custom_player_values_are_used() -> None:
    deck = create_deck()

    state = GameStateFactory().create_goldfish_state(
        deck,
        player_id=7,
        player_name="Junpei",
    )

    player = state.players[0]

    assert player.player_id == 7
    assert player.name == "Junpei"


def test_factory_does_not_shuffle_or_draw() -> None:
    deck = create_deck()

    state = GameStateFactory().create_goldfish_state(
        deck
    )

    player = state.players[0]

    assert list(player.library) == deck.cards
    assert len(player.hand) == 0
    assert state.started is False
    assert state.action_count == 0