from krs.cards.card import Card
from krs.game.permanent import Permanent


def create_kinnan() -> Card:
    return Card(
        id="kinnan-card-id",
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


def create_spark_double() -> Card:
    return Card(
        id="spark-double-card-id",
        name="Spark Double",
        mana_cost="{3}{U}",
        mana_value=4,
        oracle_text=(
            "You may have Spark Double enter as a copy "
            "of a creature or planeswalker you control."
        ),
        type_line="Creature — Illusion",
        power="0",
        toughness="0",
    )


def test_permanent_can_be_created() -> None:
    card = create_kinnan()

    permanent = Permanent(
        permanent_id=1,
        card=card,
        owner_id=0,
        controller_id=0,
    )

    assert permanent.permanent_id == 1
    assert permanent.card == card
    assert permanent.owner_id == 0
    assert permanent.controller_id == 0


def test_permanent_has_expected_default_state() -> None:
    permanent = Permanent(
        permanent_id=1,
        card=create_kinnan(),
        owner_id=0,
        controller_id=0,
    )

    assert permanent.tapped is False
    assert permanent.summoning_sick is True
    assert permanent.is_token is False
    assert permanent.copied_from is None
    assert permanent.entered_turn == 0
    assert permanent.counters == {}


def test_permanent_can_be_tapped_and_untapped() -> None:
    permanent = Permanent(
        permanent_id=1,
        card=create_kinnan(),
        owner_id=0,
        controller_id=0,
    )

    permanent.tapped = True
    assert permanent.tapped is True

    permanent.tapped = False
    assert permanent.tapped is False


def test_summoning_sickness_can_be_removed() -> None:
    permanent = Permanent(
        permanent_id=1,
        card=create_kinnan(),
        owner_id=0,
        controller_id=0,
    )

    permanent.summoning_sick = False

    assert permanent.summoning_sick is False


def test_permanent_can_store_counters() -> None:
    permanent = Permanent(
        permanent_id=1,
        card=create_kinnan(),
        owner_id=0,
        controller_id=0,
    )

    permanent.counters["+1/+1"] = 2
    permanent.counters["charge"] = 1

    assert permanent.counters["+1/+1"] == 2
    assert permanent.counters["charge"] == 1


def test_counter_dictionaries_are_not_shared() -> None:
    first = Permanent(
        permanent_id=1,
        card=create_kinnan(),
        owner_id=0,
        controller_id=0,
    )
    second = Permanent(
        permanent_id=2,
        card=create_kinnan(),
        owner_id=0,
        controller_id=0,
    )

    first.counters["+1/+1"] = 1

    assert first.counters == {"+1/+1": 1}
    assert second.counters == {}


def test_permanent_can_store_copy_source() -> None:
    kinnan = create_kinnan()

    permanent = Permanent(
        permanent_id=2,
        card=create_spark_double(),
        owner_id=0,
        controller_id=0,
        copied_from=kinnan,
    )

    assert permanent.card.name == "Spark Double"
    assert permanent.copied_from == kinnan


def test_permanents_with_different_ids_are_different() -> None:
    card = create_kinnan()

    first = Permanent(
        permanent_id=1,
        card=card,
        owner_id=0,
        controller_id=0,
    )
    second = Permanent(
        permanent_id=2,
        card=card,
        owner_id=0,
        controller_id=0,
    )

    assert first != second


def test_permanent_can_have_different_owner_and_controller() -> None:
    permanent = Permanent(
        permanent_id=1,
        card=create_kinnan(),
        owner_id=0,
        controller_id=1,
    )

    assert permanent.owner_id == 0
    assert permanent.controller_id == 1

def test_permanents_do_not_share_chosen_values() -> None:
    first = Permanent(
        permanent_id=1,
        card=create_kinnan(),
        owner_id=0,
        controller_id=0,
    )
    second = Permanent(
        permanent_id=2,
        card=create_kinnan(),
        owner_id=0,
        controller_id=0,
    )

    first.chosen_values["creature_type"] = "Human"

    assert first.chosen_values == {
        "creature_type": "Human",
    }
    assert second.chosen_values == {}


def test_permanent_returns_creature_types() -> None:
    permanent = Permanent(
        permanent_id=1,
        card=create_kinnan(),
        owner_id=0,
        controller_id=0,
    )

    assert permanent.creature_types == {
        "Human",
        "Druid",
    }


def test_noncreature_has_no_creature_types() -> None:
    card = Card(
        id="sol-ring-id",
        name="Sol Ring",
        mana_cost="{1}",
        mana_value=1,
        oracle_text="{T}: Add {C}{C}.",
        type_line="Artifact",
    )

    permanent = Permanent(
        permanent_id=1,
        card=card,
        owner_id=0,
        controller_id=0,
    )

    assert permanent.creature_types == set()

def test_noncreature_can_activate_tap_ability_while_new() -> None:
    card = Card(
        id="sol-ring-id",
        name="Sol Ring",
        mana_cost="{1}",
        mana_value=1,
        oracle_text="{T}: Add {C}{C}.",
        type_line="Artifact",
    )

    permanent = Permanent(
        permanent_id=1,
        card=card,
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
    )

    assert permanent.can_activate_tap_ability is True


def test_summoning_sick_creature_cannot_activate_tap_ability() -> None:
    permanent = Permanent(
        permanent_id=1,
        card=create_kinnan(),
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
    )

    assert permanent.can_activate_tap_ability is False


def test_creature_without_summoning_sickness_can_activate_tap_ability() -> None:
    permanent = Permanent(
        permanent_id=1,
        card=create_kinnan(),
        owner_id=0,
        controller_id=0,
        summoning_sick=False,
    )

    assert permanent.can_activate_tap_ability is True


def test_haste_allows_summoning_sick_creature_to_activate_tap_ability() -> None:
    card = Card(
        id="hasty-creature-id",
        name="Hasty Mana Creature",
        mana_cost="{G}",
        mana_value=1,
        oracle_text="Haste",
        type_line="Creature — Elf Druid",
        power="1",
        toughness="1",
        keywords=("Haste",),
    )

    permanent = Permanent(
        permanent_id=1,
        card=card,
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
    )

    assert permanent.has_haste is True
    assert permanent.can_activate_tap_ability is True


def test_as_though_haste_permission_allows_tap_ability() -> None:
    permanent = Permanent(
        permanent_id=1,
        card=create_kinnan(),
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
        can_activate_tap_abilities_as_though_haste=True,
    )

    assert permanent.can_activate_tap_ability is True