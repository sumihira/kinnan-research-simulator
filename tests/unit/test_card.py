import pytest
from dataclasses import FrozenInstanceError
from krs.cards.card import Card
from krs.abilities.static import StaticAbility

def create_kinnan() -> Card:
    return Card(
        id="kinnan-id",
        name="Kinnan, Bonder Prodigy",
        mana_cost="{G}{U}",
        mana_value=2,
        oracle_text=(
            "Whenever you tap a nonland permanent for mana, "
            "add one mana of any type that permanent produced."
        ),
        type_line="Legendary Creature — Human Druid",
        power="2",
        toughness="2",
    )


def test_card_can_be_created() -> None:
    card = create_kinnan()

    assert card.id == "kinnan-id"
    assert card.name == "Kinnan, Bonder Prodigy"
    assert card.mana_cost == "{G}{U}"
    assert card.mana_value == 2
    assert card.type_line == "Legendary Creature — Human Druid"
    assert card.power == "2"
    assert card.toughness == "2"


def test_card_without_power_and_toughness() -> None:
    card = Card(
        id="sol-ring-id",
        name="Sol Ring",
        mana_cost="{1}",
        mana_value=1,
        oracle_text="{T}: Add {C}{C}.",
        type_line="Artifact",
    )

    assert card.power is None
    assert card.toughness is None


def test_card_is_immutable() -> None:
    card = create_kinnan()

    with pytest.raises(FrozenInstanceError):
        card.name = "Changed Name"  # type: ignore[misc]


def test_card_equality_is_based_on_field_values() -> None:
    first = create_kinnan()
    second = create_kinnan()

    assert first == second


def test_cards_with_different_ids_are_not_equal() -> None:
    first = create_kinnan()

    second = Card(
        id="different-id",
        name=first.name,
        mana_cost=first.mana_cost,
        mana_value=first.mana_value,
        oracle_text=first.oracle_text,
        type_line=first.type_line,
        power=first.power,
        toughness=first.toughness,
    )

    assert first != second


def test_card_rejects_undefined_attributes() -> None:
    card = create_kinnan()

    with pytest.raises((AttributeError, FrozenInstanceError)):
        card.new_attribute = "invalid"  # type: ignore[attr-defined]

def test_card_keywords_default_to_empty_tuple() -> None:
    card = create_kinnan()

    assert card.keywords == ()


def test_card_can_store_keywords() -> None:
    card = Card(
        id="mana-dork-id",
        name="Hasty Mana Dork",
        mana_cost="{G}",
        mana_value=1,
        oracle_text="Haste",
        type_line="Creature — Elf Druid",
        power="1",
        toughness="1",
        keywords=("Haste",),
    )

    assert card.keywords == ("Haste",)

def test_card_can_store_non_numeric_power_and_toughness() -> None:
    card = Card(
        id="variable-creature-id",
        name="Variable Creature",
        mana_cost="{3}",
        mana_value=3,
        oracle_text="",
        type_line="Creature — Shapeshifter",
        power="*",
        toughness="1+*",
    )

    assert card.power == "*"
    assert card.toughness == "1+*"