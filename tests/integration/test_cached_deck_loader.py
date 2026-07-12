import json
from pathlib import Path

from krs.cards.cache import CardCache
from krs.cards.card_loader import CardLoader
from krs.decks.deck_loader import DeckLoader


def create_raw_card(
    *,
    card_id: str,
    name: str,
    type_line: str,
) -> dict[str, object]:
    return {
        "id": card_id,
        "name": name,
        "mana_cost": "",
        "cmc": 0,
        "type_line": type_line,
        "oracle_text": "",
        "keywords": [],
    }


def test_scryfall_cache_can_load_deck_csv(
    tmp_path: Path,
) -> None:
    cache_path = tmp_path / "cards.json"

    cache_path.write_text(
        json.dumps(
            [
                create_raw_card(
                    card_id="kinnan-id",
                    name="Kinnan, Bonder Prodigy",
                    type_line=(
                        "Legendary Creature — Human Druid"
                    ),
                ),
                create_raw_card(
                    card_id="sol-ring-id",
                    name="Sol Ring",
                    type_line="Artifact",
                ),
                create_raw_card(
                    card_id="forest-id",
                    name="Forest",
                    type_line="Basic Land — Forest",
                ),
            ]
        ),
        encoding="utf-8",
    )

    deck_path = tmp_path / "kinnan.csv"
    deck_path.write_text(
        '''quantity,name,section
1,"Kinnan, Bonder Prodigy",commander
1,Sol Ring,main
2,Forest,main
''',
        encoding="utf-8",
    )

    cache = CardCache.load_json(
        cache_path
    )
    card_loader = CardLoader.from_cache(
        cache
    )
    deck = DeckLoader(
        card_loader
    ).load_csv(deck_path)

    assert deck.commander.name == (
        "Kinnan, Bonder Prodigy"
    )
    assert [
        card.name
        for card in deck.cards
    ] == [
        "Sol Ring",
        "Forest",
        "Forest",
    ]