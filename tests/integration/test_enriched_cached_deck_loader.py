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
    mana_cost: str,
    mana_value: int,
    type_line: str,
    oracle_text: str,
) -> dict[str, object]:
    """Create a minimal Scryfall-style card definition."""

    return {
        "id": card_id,
        "name": name,
        "mana_cost": mana_cost,
        "cmc": mana_value,
        "type_line": type_line,
        "oracle_text": oracle_text,
        "keywords": [],
    }


def write_card_cache(
    cache_path: Path,
) -> None:
    """Write the local Scryfall cache used by the integration test."""

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
                    oracle_text=(
                        "Whenever you tap a nonland permanent "
                        "for mana, add one mana of any type "
                        "that permanent produced."
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
                    mana_cost="",
                    mana_value=0,
                    type_line="Basic Land — Forest",
                    oracle_text="",
                ),
            ]
        ),
        encoding="utf-8",
    )


def write_deck_csv(
    deck_path: Path,
) -> None:
    """Write the deck list used by the integration test."""

    deck_path.write_text(
        (
            "quantity,name,section\n"
            '1,"Kinnan, Bonder Prodigy",commander\n'
            "1,Sol Ring,main\n"
            "2,Forest,main\n"
        ),
        encoding="utf-8",
    )


def write_sol_ring_config(
    config_directory: Path,
) -> None:
    """Write the card-specific Sol Ring ability definition."""

    config_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    config_path = config_directory / "Sol_Ring.yaml"
    config_path.write_text(
        (
            "card_name: Sol Ring\n"
            "\n"
            "abilities:\n"
            "  mana:\n"
            "    - produces:\n"
            "        COLORLESS: 2\n"
            "      requires_tap: true\n"
        ),
        encoding="utf-8",
    )


def test_cached_deck_loader_applies_card_enrichment(
    tmp_path: Path,
) -> None:
    """Load a cached deck and enrich Sol Ring from YAML."""

    cache_path = tmp_path / "cards.json"
    deck_path = tmp_path / "kinnan.csv"
    config_directory = tmp_path / "card_configs"

    write_card_cache(cache_path)
    write_deck_csv(deck_path)
    write_sol_ring_config(config_directory)

    cache = CardCache.load_json(cache_path)
    config_loader = CardConfigLoader(config_directory)
    card_enricher = CardEnricher(config_loader)

    card_loader = CardLoader.from_cache(
        cache,
        enricher=card_enricher,
    )
    deck_loader = DeckLoader(card_loader)

    deck = deck_loader.load_csv(deck_path)

    assert deck.commander.name == "Kinnan, Bonder Prodigy"

    assert [card.name for card in deck.cards] == [
        "Sol Ring",
        "Forest",
        "Forest",
    ]

    sol_ring = deck.cards[0]

    assert len(sol_ring.mana_abilities) == 1

    mana_ability = sol_ring.mana_abilities[0]

    assert mana_ability.requires_tap is True
    assert mana_ability.total_produced == 2
    assert mana_ability.produced_mana == {
        Mana.COLORLESS: 2,
    }


def test_cached_deck_loader_leaves_unconfigured_cards_unchanged(
    tmp_path: Path,
) -> None:
    """Leave cards without individual YAML definitions unchanged."""

    cache_path = tmp_path / "cards.json"
    deck_path = tmp_path / "kinnan.csv"
    config_directory = tmp_path / "card_configs"

    write_card_cache(cache_path)
    write_deck_csv(deck_path)
    write_sol_ring_config(config_directory)

    cache = CardCache.load_json(cache_path)
    config_loader = CardConfigLoader(config_directory)
    card_enricher = CardEnricher(config_loader)

    card_loader = CardLoader.from_cache(
        cache,
        enricher=card_enricher,
    )
    deck = DeckLoader(card_loader).load_csv(deck_path)

    commander = deck.commander
    forests = [
        card
        for card in deck.cards
        if card.name == "Forest"
    ]

    assert commander.mana_abilities == ()
    assert len(forests) == 2
    assert all(
        forest.mana_abilities == ()
        for forest in forests
    )