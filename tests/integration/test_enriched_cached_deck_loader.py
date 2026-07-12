from __future__ import annotations

import json
from pathlib import Path

from krs.cards.cache import CardCache
from krs.cards.card_config_loader import CardConfigLoader
from krs.cards.card_enricher import CardEnricher
from krs.cards.card_loader import CardLoader
from krs.decks.deck_loader import DeckLoader
from krs.mana.mana import Mana


def create_raw_card(
    *,
    card_id: str,
    name: str,
    type_line: str,
    mana_cost: str = "",
    mana_value: int = 0,
    oracle_text: str = "",
) -> dict[str, object]:
    return {
        "id": card_id,
        "name": name,
        "mana_cost": mana_cost,
        "cmc": mana_value,
        "type_line": type_line,
        "oracle_text": oracle_text,
        "keywords": [],
    }


def test_cached_deck_loader_applies_card_config(
    tmp_path: Path,
) -> None:
    cache_path = tmp_path / "cards.json"
    cache_path.write_text(
        json.dumps(
            [
                create_raw_card(
                    card_id="kinnan-id",
                    name="Kinnan, Bonder Prodigy",
                    mana_cost="{G}{U}",
                    mana_value=2,
                    type_line=(
                        "Legendary Creature — Human Druid"
                    ),
                ),
                create_raw_card(
                    card_id="sol-ring-id",
                    name="Sol Ring",
                    mana_cost="{1}",
                    mana_value=1,
                    type_line="Artifact",
                    oracle_text="{T}: Add {C}{C}.",
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

    config_directory = tmp_path / "cards"
    config_directory.mkdir()

    config_directory.joinpath("sol_ring.yaml").write_text(
        """
card_name: Sol Ring

abilities:
  mana:
    - produces:
        COLORLESS: 2
      requires_tap: true
""".strip(),
        encoding="utf-8",
    )

    cache = CardCache.load_json(cache_path)
    enricher = CardEnricher(
        CardConfigLoader(config_directory)
    )
    card_loader = CardLoader.from_cache(
        cache,
        enricher=enricher,
    )

    deck = DeckLoader(card_loader).load_csv(deck_path)

    assert deck.commander.name == "Kinnan, Bonder Prodigy"
    assert deck.commander.mana_abilities == ()

    assert [card.name for card in deck.cards] == [
        "Sol Ring",
        "Forest",
        "Forest",
    ]

    sol_ring = deck.cards[0]

    assert len(sol_ring.mana_abilities) == 1
    assert sol_ring.mana_abilities[0].produced_mana == {
        Mana.COLORLESS: 2,
    }
    assert sol_ring.mana_abilities[0].total_produced == 2

    forests = [
        card
        for card in deck.cards
        if card.name == "Forest"
    ]

    assert len(forests) == 2
    assert all(
        forest.mana_abilities == ()
        for forest in forests
    )