from __future__ import annotations

import json
from pathlib import Path

import pytest

from krs.decks.deck import Deck
from krs.simulation.monte_carlo import MonteCarloSimulator
from krs.simulation.simulation_config import SimulationConfig
from krs.simulation.simulation_factory import SimulationFactory
from krs.mana.mana import Mana


def write_card_cache(
    path: Path,
) -> None:
    cards = [
        {
            "id": "kinnan-printing-id",
            "oracle_id": "kinnan-oracle-id",
            "name": "Kinnan, Bonder Prodigy",
            "mana_cost": "{G}{U}",
            "cmc": 2,
            "oracle_text": (
                "Whenever you tap a nonland permanent for mana, "
                "add one mana of any type that permanent produced."
            ),
            "type_line": (
                "Legendary Creature — Human Druid"
            ),
            "power": "2",
            "toughness": "2",
            "keywords": [],
        },
        {
            "id": "sol-ring-printing-id",
            "oracle_id": "sol-ring-oracle-id",
            "name": "Sol Ring",
            "mana_cost": "{1}",
            "cmc": 1,
            "oracle_text": "{T}: Add {C}{C}.",
            "type_line": "Artifact",
            "keywords": [],
        },
        {
            "id": "forest-printing-id",
            "oracle_id": "forest-oracle-id",
            "name": "Forest",
            "mana_cost": "",
            "cmc": 0,
            "oracle_text": "({T}: Add {G}.)",
            "type_line": "Basic Land — Forest",
            "keywords": [],
        },
    ]

    path.write_text(
        json.dumps(cards),
        encoding="utf-8",
    )


def write_deck(
    path: Path,
) -> None:
    path.write_text(
        "\n".join(
            (
                "quantity,name,section",
                '1,"Kinnan, Bonder Prodigy",commander',
                "1,Sol Ring,main",
                "98,Forest,main",
            )
        ),
        encoding="utf-8",
    )


def write_card_configs(
    directory: Path,
) -> None:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        directory / "sol_ring.yaml"
    ).write_text(
        """
card_name: Sol Ring
abilities:
  mana:
    - cost:
        tap: true
      produces:
        colorless: 2
""".strip(),
        encoding="utf-8",
    )


def write_simulation_config(
    path: Path,
) -> None:
    path.write_text(
        """
strategy: balanced
games: 10
max_turns: 6
seed: 12345
workers: 1
mulligan:
  enabled: true
replay:
  enabled: false
""".strip(),
        encoding="utf-8",
    )


def test_factory_loads_deck_from_scryfall_cache(
    tmp_path: Path,
) -> None:
    cache_path = tmp_path / "cards.json"
    deck_path = tmp_path / "kinnan.csv"

    write_card_cache(cache_path)
    write_deck(deck_path)

    deck = SimulationFactory().load_deck(
        deck_path=deck_path,
        card_cache_path=cache_path,
    )

    assert isinstance(deck, Deck)
    assert deck.name == "kinnan"
    assert deck.commander.name == (
        "Kinnan, Bonder Prodigy"
    )
    assert deck.commander.id == "kinnan-printing-id"
    assert "Whenever you tap" in (
        deck.commander.oracle_text
    )
    assert len(deck.cards) == 99


def test_factory_applies_card_configs_to_loaded_deck(
    tmp_path: Path,
) -> None:
    cache_path = tmp_path / "cards.json"
    deck_path = tmp_path / "kinnan.csv"
    card_config_directory = tmp_path / "cards"

    write_card_cache(cache_path)
    write_deck(deck_path)
    write_card_configs(card_config_directory)

    deck = SimulationFactory().load_deck(
        deck_path=deck_path,
        card_cache_path=cache_path,
        card_config_directory=card_config_directory,
    )

    sol_ring = next(
        card
        for card in deck.cards
        if card.name == "Sol Ring"
    )

    assert sol_ring.oracle_text == "{T}: Add {C}{C}."
    assert len(sol_ring.mana_abilities) == 1
    assert sol_ring.mana_abilities[0].produced_mana == {
        Mana.COLORLESS: 2,
    }
    assert sol_ring.mana_abilities[0].requires_tap is True
    assert sol_ring.mana_abilities[0].total_produced == 2


def test_factory_can_override_deck_name(
    tmp_path: Path,
) -> None:
    cache_path = tmp_path / "cards.json"
    deck_path = tmp_path / "kinnan.csv"

    write_card_cache(cache_path)
    write_deck(deck_path)

    deck = SimulationFactory().load_deck(
        deck_path=deck_path,
        card_cache_path=cache_path,
        deck_name="Kinnan Production Deck",
    )

    assert deck.name == "Kinnan Production Deck"


def test_factory_loads_config_and_deck(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "simulation.yaml"
    cache_path = tmp_path / "cards.json"
    deck_path = tmp_path / "kinnan.csv"

    write_simulation_config(config_path)
    write_card_cache(cache_path)
    write_deck(deck_path)

    config, deck = (
        SimulationFactory().load_config_and_deck(
            simulation_config_path=config_path,
            deck_path=deck_path,
            card_cache_path=cache_path,
        )
    )

    assert isinstance(config, SimulationConfig)
    assert config.games == 10
    assert config.max_turns == 6
    assert deck.commander.name == (
        "Kinnan, Bonder Prodigy"
    )
    assert len(deck.cards) == 99


def test_factory_creates_complete_file_based_run(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "simulation.yaml"
    cache_path = tmp_path / "cards.json"
    deck_path = tmp_path / "kinnan.csv"

    write_simulation_config(config_path)
    write_card_cache(cache_path)
    write_deck(deck_path)

    config, deck, simulator = (
        SimulationFactory()
        .create_monte_carlo_run_from_files(
            simulation_config_path=config_path,
            deck_path=deck_path,
            card_cache_path=cache_path,
        )
    )

    assert isinstance(config, SimulationConfig)
    assert isinstance(deck, Deck)
    assert isinstance(simulator, MonteCarloSimulator)
    assert (
        simulator
        .experiment_manager
        .simulator
        .config
        is config
    )


def test_factory_rejects_missing_card_cache(
    tmp_path: Path,
) -> None:
    deck_path = tmp_path / "kinnan.csv"
    write_deck(deck_path)

    with pytest.raises(
        FileNotFoundError,
        match="Card cache file not found",
    ):
        SimulationFactory().load_deck(
            deck_path=deck_path,
            card_cache_path=tmp_path / "missing.json",
        )


def test_factory_rejects_unknown_deck_card(
    tmp_path: Path,
) -> None:
    cache_path = tmp_path / "cards.json"
    deck_path = tmp_path / "kinnan.csv"

    write_card_cache(cache_path)

    deck_path.write_text(
        "\n".join(
            (
                "quantity,name,section",
                '1,"Kinnan, Bonder Prodigy",commander',
                "1,Unknown Card,main",
            )
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Card not found in cache: Unknown Card",
    ):
        SimulationFactory().load_deck(
            deck_path=deck_path,
            card_cache_path=cache_path,
        )