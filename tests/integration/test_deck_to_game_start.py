from pathlib import Path

from krs.cards.card import Card
from krs.cards.card_loader import CardLoader
from krs.decks.deck_loader import DeckLoader
from krs.engine.game_engine import GameEngine
from krs.simulation.game_state_factory import (
    GameStateFactory,
)


def test_deck_csv_can_start_goldfish_game(
    tmp_path: Path,
) -> None:
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

    cards = {
        kinnan.name: kinnan,
    }

    csv_lines = [
        "quantity,name,section",
        '1,"Kinnan, Bonder Prodigy",commander',
    ]

    for index in range(10):
        card = Card(
            id=f"card-{index}",
            name=f"Card {index}",
            mana_cost="",
            mana_value=0,
            oracle_text="",
            type_line="Artifact",
        )

        cards[card.name] = card

        csv_lines.append(
            f"1,{card.name},main"
        )

    deck_path = tmp_path / "deck.csv"
    deck_path.write_text(
        "\n".join(csv_lines),
        encoding="utf-8",
    )

    deck = DeckLoader(
        CardLoader(cards)
    ).load_csv(deck_path)

    state = (
        GameStateFactory()
        .create_goldfish_state(
            deck,
            seed=12345,
        )
    )

    GameEngine().start_game(state)

    player = state.players[0]

    assert state.started is True
    assert len(player.hand) == 7
    assert len(player.library) == 3
    assert list(player.command) == [kinnan]