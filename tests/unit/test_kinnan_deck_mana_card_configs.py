from __future__ import annotations

from pathlib import Path

import pytest

from krs.cards.card import Card
from krs.cards.card_config_loader import CardConfigLoader
from krs.cards.card_enricher import CardEnricher
from krs.mana.mana import Mana


CARD_CONFIG_DIRECTORY = Path("config/cards")


def create_card(
    *,
    name: str,
    type_line: str = "Artifact",
) -> Card:
    return Card(
        id=name.casefold().replace(" ", "-"),
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line=type_line,
    )


def enrich_card(
    *,
    name: str,
    type_line: str = "Artifact",
) -> Card:
    enricher = CardEnricher(
        CardConfigLoader(
            CARD_CONFIG_DIRECTORY
        )
    )

    return enricher.enrich(
        create_card(
            name=name,
            type_line=type_line,
        )
    )


@pytest.mark.parametrize(
    (
        "card_name",
        "type_line",
        "expected_mana",
    ),
    (
        (
            "Arcane Signet",
            "Artifact",
            {
                Mana.BLUE: 1,
                Mana.GREEN: 1,
            },
        ),
        (
            "Birds of Paradise",
            "Creature — Bird",
            {
                Mana.WHITE: 1,
                Mana.BLUE: 1,
                Mana.BLACK: 1,
                Mana.RED: 1,
                Mana.GREEN: 1,
            },
        ),
        (
            "Botanical Sanctum",
            "Land",
            {
                Mana.BLUE: 1,
                Mana.GREEN: 1,
            },
        ),
        (
            "Breeding Pool",
            "Land — Forest Island",
            {
                Mana.BLUE: 1,
                Mana.GREEN: 1,
            },
        ),
        (
            "Delighted Halfling",
            "Creature — Halfling Citizen",
            {
                Mana.COLORLESS: 1,
            },
        ),
        (
            "Devoted Druid",
            "Creature — Elf Druid",
            {
                Mana.GREEN: 1,
            },
        ),
        (
            "Elvish Mystic",
            "Creature — Elf Druid",
            {
                Mana.GREEN: 1,
            },
        ),
        (
            "Fyndhorn Elves",
            "Creature — Elf Druid",
            {
                Mana.GREEN: 1,
            },
        ),
        (
            "Gilded Lotus",
            "Artifact",
            {
                Mana.WHITE: 3,
                Mana.BLUE: 3,
                Mana.BLACK: 3,
                Mana.RED: 3,
                Mana.GREEN: 3,
            },
        ),
        (
            "Grim Monolith",
            "Artifact",
            {
                Mana.COLORLESS: 3,
            },
        ),
        (
            "Island",
            "Basic Land — Island",
            {
                Mana.BLUE: 1,
            },
        ),
        (
            "Mana Vault",
            "Artifact",
            {
                Mana.COLORLESS: 3,
            },
        ),
        (
            "Rejuvenating Springs",
            "Land",
            {
                Mana.BLUE: 1,
                Mana.GREEN: 1,
            },
        ),
        (
            "Seat of the Synod",
            "Artifact Land",
            {
                Mana.BLUE: 1,
            },
        ),
        (
            "Snow-Covered Island",
            "Basic Snow Land — Island",
            {
                Mana.BLUE: 1,
            },
        ),
        (
            "Talisman of Curiosity",
            "Artifact",
            {
                Mana.BLUE: 1,
                Mana.GREEN: 1,
            },
        ),
        (
            "Thran Dynamo",
            "Artifact",
            {
                Mana.COLORLESS: 3,
            },
        ),
        (
            "Tropical Island",
            "Land — Forest Island",
            {
                Mana.BLUE: 1,
                Mana.GREEN: 1,
            },
        ),
    ),
)
def test_mana_card_config_creates_expected_mana_ability(
    card_name: str,
    type_line: str,
    expected_mana: dict[Mana, int],
) -> None:
    card = enrich_card(
        name=card_name,
        type_line=type_line,
    )

    assert len(card.mana_abilities) == 1

    ability = card.mana_abilities[0]

    assert dict(ability.produced_mana) == expected_mana
    assert ability.requires_tap is True


@pytest.mark.parametrize(
    (
        "card_name",
        "mana",
        "expected_amount",
    ),
    (
        (
            "Arcane Signet",
            Mana.BLUE,
            1,
        ),
        (
            "Arcane Signet",
            Mana.GREEN,
            1,
        ),
        (
            "Birds of Paradise",
            Mana.WHITE,
            1,
        ),
        (
            "Birds of Paradise",
            Mana.BLUE,
            1,
        ),
        (
            "Birds of Paradise",
            Mana.BLACK,
            1,
        ),
        (
            "Birds of Paradise",
            Mana.RED,
            1,
        ),
        (
            "Birds of Paradise",
            Mana.GREEN,
            1,
        ),
        (
            "Gilded Lotus",
            Mana.BLUE,
            3,
        ),
        (
            "Gilded Lotus",
            Mana.GREEN,
            3,
        ),
        (
            "Talisman of Curiosity",
            Mana.BLUE,
            1,
        ),
        (
            "Talisman of Curiosity",
            Mana.GREEN,
            1,
        ),
    ),
)
def test_configured_mana_ability_supports_expected_selection(
    card_name: str,
    mana: Mana,
    expected_amount: int,
) -> None:
    card = enrich_card(
        name=card_name,
    )

    ability = card.mana_abilities[0]

    assert ability.can_produce(mana) is True
    assert ability.produced_mana[mana] == expected_amount


@pytest.mark.parametrize(
    "card_name",
    (
        "Birds of Paradise",
        "Delighted Halfling",
        "Devoted Druid",
        "Elvish Mystic",
        "Fyndhorn Elves",
    ),
)
def test_mana_creatures_are_configured_as_creatures(
    card_name: str,
) -> None:
    card = enrich_card(
        name=card_name,
        type_line="Creature — Elf Druid",
    )

    assert "Creature" in card.type_line
    assert len(card.mana_abilities) == 1


def test_grim_monolith_has_untap_ability() -> None:
    card = enrich_card(
        name="Grim Monolith",
    )

    assert len(card.activated_abilities) == 1

    ability = card.activated_abilities[0]

    assert ability.ability_type == "untap_self"
    assert ability.mana_cost == "{4}"
    assert ability.requires_tap is False
    assert ability.parameters == {}


def test_grim_monolith_skips_normal_untap() -> None:
    card = enrich_card(
        name="Grim Monolith",
    )

    assert len(card.static_abilities) == 1

    ability = card.static_abilities[0]

    assert ability.ability_type == "skip_normal_untap"
    assert ability.parameters == {
        "applies_during": "untap_step",
    }

def test_mana_vault_has_untap_ability() -> None:
    card = enrich_card(
        name="Mana Vault",
    )

    assert len(card.activated_abilities) == 1

    ability = card.activated_abilities[0]

    assert ability.ability_type == "untap_self"
    assert ability.mana_cost == "{4}"
    assert ability.requires_tap is False
    assert ability.parameters == {}


def test_mana_vault_skips_normal_untap() -> None:
    card = enrich_card(
        name="Mana Vault",
    )

    assert len(card.static_abilities) == 1

    ability = card.static_abilities[0]

    assert ability.ability_type == "skip_normal_untap"
    assert ability.parameters == {
        "applies_during": "untap_step",
    }

def test_mana_vault_has_untap_ability() -> None:
    card = enrich_card(
        name="Mana Vault",
    )

    assert len(card.activated_abilities) == 1

    ability = card.activated_abilities[0]

    assert ability.ability_type == "untap_self"
    assert ability.mana_cost == "{4}"
    assert ability.requires_tap is False
    assert ability.parameters == {}


def test_mana_vault_skips_normal_untap() -> None:
    card = enrich_card(
        name="Mana Vault",
    )

    assert len(card.static_abilities) == 1

    ability = card.static_abilities[0]

    assert ability.ability_type == "skip_normal_untap"
    assert ability.parameters == {
        "applies_during": "untap_step",
    }

def test_existing_mana_configs_remain_loadable() -> None:
    loader = CardConfigLoader(
        CARD_CONFIG_DIRECTORY
    )

    existing_cards = (
        "Sol Ring",
        "Basalt Monolith",
        "Llanowar Elves",
    )

    for card_name in existing_cards:
        config = loader.load_by_card_name(
            card_name
        )

        assert config is not None
        assert config.card_name == card_name


def test_all_new_card_configs_use_snake_case_filenames() -> None:
    expected_paths = (
        CARD_CONFIG_DIRECTORY / "arcane_signet.yaml",
        CARD_CONFIG_DIRECTORY / "birds_of_paradise.yaml",
        CARD_CONFIG_DIRECTORY / "botanical_sanctum.yaml",
        CARD_CONFIG_DIRECTORY / "breeding_pool.yaml",
        CARD_CONFIG_DIRECTORY / "delighted_halfling.yaml",
        CARD_CONFIG_DIRECTORY / "devoted_druid.yaml",
        CARD_CONFIG_DIRECTORY / "elvish_mystic.yaml",
        CARD_CONFIG_DIRECTORY / "fyndhorn_elves.yaml",
        CARD_CONFIG_DIRECTORY / "gilded_lotus.yaml",
        CARD_CONFIG_DIRECTORY / "grim_monolith.yaml",
        CARD_CONFIG_DIRECTORY / "island.yaml",
        CARD_CONFIG_DIRECTORY / "mana_vault.yaml",
        CARD_CONFIG_DIRECTORY / "rejuvenating_springs.yaml",
        CARD_CONFIG_DIRECTORY / "seat_of_the_synod.yaml",
        CARD_CONFIG_DIRECTORY / "snow_covered_island.yaml",
        CARD_CONFIG_DIRECTORY / "talisman_of_curiosity.yaml",
        CARD_CONFIG_DIRECTORY / "thran_dynamo.yaml",
        CARD_CONFIG_DIRECTORY / "tropical_island.yaml",
    )

    for path in expected_paths:
        assert path.exists()
        assert path.name == path.name.casefold()
        assert " " not in path.name