from __future__ import annotations

import json
from pathlib import Path

from krs.cards.cache import CardCache
from krs.cards.card import Card
from krs.cards.card_config_loader import CardConfigLoader
from krs.cards.card_enricher import CardEnricher
from krs.cards.card_loader import CardLoader
from krs.decks.deck import Deck
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
    power: str | None = None,
    toughness: str | None = None,
) -> dict[str, object]:
    raw_card: dict[str, object] = {
        "id": card_id,
        "name": name,
        "mana_cost": mana_cost,
        "cmc": mana_value,
        "type_line": type_line,
        "oracle_text": oracle_text,
        "keywords": [],
    }

    if power is not None:
        raw_card["power"] = power

    if toughness is not None:
        raw_card["toughness"] = toughness

    return raw_card


def write_card_cache(
    cache_path: Path,
) -> None:
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
                        "that permanent produced.\n"
                        "{5}{G}{U}: Look at the top five cards "
                        "of your library. You may put a non-Human "
                        "creature card from among them onto the "
                        "battlefield. Put the rest on the bottom "
                        "of your library in a random order."
                    ),
                    power="2",
                    toughness="2",
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
                    card_id="basalt-monolith-id",
                    name="Basalt Monolith",
                    mana_cost="{3}",
                    mana_value=3,
                    type_line="Artifact",
                    oracle_text=(
                        "Basalt Monolith doesn't untap during "
                        "your untap step.\n"
                        "{T}: Add {C}{C}{C}.\n"
                        "{3}: Untap Basalt Monolith."
                    ),
                ),
                create_raw_card(
                    card_id="llanowar-elves-id",
                    name="Llanowar Elves",
                    mana_cost="{G}",
                    mana_value=1,
                    type_line="Creature — Elf Druid",
                    oracle_text="{T}: Add {G}.",
                    power="1",
                    toughness="1",
                ),
                create_raw_card(
                    card_id="roaming-throne-id",
                    name="Roaming Throne",
                    mana_cost="{4}",
                    mana_value=4,
                    type_line="Artifact Creature — Golem",
                    oracle_text=(
                        "Ward {2}\n"
                        "As Roaming Throne enters, choose a "
                        "creature type.\n"
                        "Roaming Throne is the chosen type in "
                        "addition to its other types.\n"
                        "If a triggered ability of another "
                        "creature you control of the chosen type "
                        "triggers, it triggers an additional time."
                    ),
                    power="4",
                    toughness="4",
                ),
                create_raw_card(
                    card_id="forest-id",
                    name="Forest",
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
    deck_path.write_text(
        '''quantity,name,section
1,"Kinnan, Bonder Prodigy",commander
1,Sol Ring,main
1,Basalt Monolith,main
1,Llanowar Elves,main
1,Roaming Throne,main
2,Forest,main
''',
        encoding="utf-8",
    )


def write_card_configs(
    config_directory: Path,
) -> None:
    config_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

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

    config_directory.joinpath(
        "basalt_monolith.yaml"
    ).write_text(
        """
card_name: Basalt Monolith

abilities:
  mana:
    - produces:
        COLORLESS: 3
      requires_tap: true

  activated:
    - ability_type: untap_self
      mana_cost: "{3}"
      requires_tap: false
      parameters: {}

  static:
    - ability_type: skip_normal_untap
      parameters:
        applies_during: untap_step
""".strip(),
        encoding="utf-8",
    )

    config_directory.joinpath(
        "llanowar_elves.yaml"
    ).write_text(
        """
card_name: Llanowar Elves

abilities:
  mana:
    - produces:
        GREEN: 1
      requires_tap: true
""".strip(),
        encoding="utf-8",
    )

    config_directory.joinpath("kinnan.yaml").write_text(
        """
card_name: Kinnan, Bonder Prodigy

abilities:
  static:
    - ability_type: additional_nonland_mana
      parameters:
        source_filter:
          permanent_type: nonland
        additional_amount: 1
        mana_selection: produced_type

  activated:
    - ability_type: activate_kinnan
      mana_cost: "{5}{G}{U}"
      requires_tap: false
      parameters:
        look_at: 5
        hit_filter:
          permanent: true
          creature: true
          non_human: true
        hit_destination: battlefield
        miss_destination: library_bottom_random
""".strip(),
        encoding="utf-8",
    )

    config_directory.joinpath(
        "roaming_throne.yaml"
    ).write_text(
        """
card_name: Roaming Throne

abilities:
  replacement:
    - ability_type: choose_creature_type
      event: enters_battlefield
      parameters:
        choice_type: creature_type

  static:
    - ability_type: additional_trigger
      parameters:
        additional_trigger_count: 1
        source_filter:
          other_creature: true
          chosen_creature_type: true
        controller_only: true
""".strip(),
        encoding="utf-8",
    )


def find_card(
    deck: Deck,
    card_name: str,
) -> Card:
    return next(
        card
        for card in deck.cards
        if card.name == card_name
    )


def test_cached_deck_loader_applies_card_configs(
    tmp_path: Path,
) -> None:
    cache_path = tmp_path / "cards.json"
    deck_path = tmp_path / "kinnan.csv"
    config_directory = tmp_path / "cards"

    write_card_cache(cache_path)
    write_deck_csv(deck_path)
    write_card_configs(config_directory)

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
    assert [card.name for card in deck.cards] == [
        "Sol Ring",
        "Basalt Monolith",
        "Llanowar Elves",
        "Roaming Throne",
        "Forest",
        "Forest",
    ]

    assert_sol_ring(find_card(deck, "Sol Ring"))
    assert_basalt_monolith(
        find_card(deck, "Basalt Monolith")
    )
    assert_llanowar_elves(
        find_card(deck, "Llanowar Elves")
    )
    assert_kinnan(deck.commander)
    assert_roaming_throne(
        find_card(deck, "Roaming Throne")
    )

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
    assert all(
        forest.activated_abilities == ()
        for forest in forests
    )
    assert all(
        forest.static_abilities == ()
        for forest in forests
    )


def assert_sol_ring(
    card: Card,
) -> None:
    assert len(card.mana_abilities) == 1
    assert card.mana_abilities[0].produced_mana == {
        Mana.COLORLESS: 2,
    }
    assert card.mana_abilities[0].requires_tap is True
    assert card.mana_abilities[0].total_produced == 2


def assert_basalt_monolith(
    card: Card,
) -> None:
    assert len(card.mana_abilities) == 1
    assert card.mana_abilities[0].produced_mana == {
        Mana.COLORLESS: 3,
    }
    assert card.mana_abilities[0].requires_tap is True
    assert card.mana_abilities[0].total_produced == 3

    assert len(card.activated_abilities) == 1
    assert (
        card.activated_abilities[0].ability_type
        == "untap_self"
    )
    assert card.activated_abilities[0].mana_cost == "{3}"
    assert (
        card.activated_abilities[0].requires_tap
        is False
    )

    assert len(card.static_abilities) == 1
    assert (
        card.static_abilities[0].ability_type
        == "skip_normal_untap"
    )
    assert card.static_abilities[0].parameters == {
        "applies_during": "untap_step",
    }


def assert_llanowar_elves(
    card: Card,
) -> None:
    assert len(card.mana_abilities) == 1
    assert card.mana_abilities[0].produced_mana == {
        Mana.GREEN: 1,
    }
    assert card.mana_abilities[0].requires_tap is True
    assert card.mana_abilities[0].total_produced == 1


def assert_kinnan(
    card: Card,
) -> None:
    assert len(card.static_abilities) == 1
    assert (
        card.static_abilities[0].ability_type
        == "additional_nonland_mana"
    )
    assert card.static_abilities[0].parameters == {
        "source_filter": {
            "permanent_type": "nonland",
        },
        "additional_amount": 1,
        "mana_selection": "produced_type",
    }

    assert len(card.activated_abilities) == 1
    assert (
        card.activated_abilities[0].ability_type
        == "activate_kinnan"
    )
    assert (
        card.activated_abilities[0].mana_cost
        == "{5}{G}{U}"
    )
    assert (
        card.activated_abilities[0].requires_tap
        is False
    )
    assert card.activated_abilities[0].parameters == {
        "look_at": 5,
        "hit_filter": {
            "permanent": True,
            "creature": True,
            "non_human": True,
        },
        "hit_destination": "battlefield",
        "miss_destination": "library_bottom_random",
    }


def assert_roaming_throne(
    card: Card,
) -> None:
    assert len(card.replacement_abilities) == 1
    assert (
        card.replacement_abilities[0].ability_type
        == "choose_creature_type"
    )
    assert (
        card.replacement_abilities[0].event
        == "enters_battlefield"
    )
    assert card.replacement_abilities[0].parameters == {
        "choice_type": "creature_type",
    }

    assert len(card.static_abilities) == 1
    assert (
        card.static_abilities[0].ability_type
        == "additional_trigger"
    )
    assert card.static_abilities[0].parameters == {
        "additional_trigger_count": 1,
        "source_filter": {
            "other_creature": True,
            "chosen_creature_type": True,
        },
        "controller_only": True,
    }