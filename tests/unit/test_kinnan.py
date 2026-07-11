import pytest

from krs.cards.card import Card
from krs.commanders.kinnan import (
    choose_kinnan_bonus_mana,
    count_active_kinnan_effects,
    count_kinnan_bonus_triggers,
    count_kinnan_trigger_multipliers,
    is_kinnan,
    is_roaming_throne,
    roaming_throne_applies_to_kinnan,
)
from krs.game.permanent import Permanent
from krs.game.zone import Zone
from krs.mana.mana import Mana


def create_permanent(
    *,
    permanent_id: int,
    name: str,
    type_line: str = "Creature",
    copied_from: Card | None = None,
) -> Permanent:
    card = Card(
        id=f"card-{permanent_id}",
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line=type_line,
    )

    return Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=0,
        controller_id=0,
        copied_from=copied_from,
    )

def create_roaming_throne(
    *,
    permanent_id: int,
    chosen_type: str | None,
) -> Permanent:
    card = Card(
        id=f"roaming-throne-{permanent_id}",
        name="Roaming Throne",
        mana_cost="{4}",
        mana_value=4,
        oracle_text="",
        type_line="Artifact Creature — Golem",
        power=4,
        toughness=4,
    )

    chosen_values: dict[str, str] = {}

    if chosen_type is not None:
        chosen_values["creature_type"] = chosen_type

    return Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=0,
        controller_id=0,
        chosen_values=chosen_values,
    )

def test_is_kinnan_returns_true_for_kinnan() -> None:
    permanent = create_permanent(
        permanent_id=1,
        name="Kinnan, Bonder Prodigy",
        type_line="Legendary Creature — Human Druid",
    )

    assert is_kinnan(permanent) is True


def test_is_kinnan_returns_false_for_other_card() -> None:
    permanent = create_permanent(
        permanent_id=1,
        name="Llanowar Elves",
        type_line="Creature — Elf Druid",
    )

    assert is_kinnan(permanent) is False


def test_is_kinnan_recognizes_copy() -> None:
    kinnan_card = Card(
        id="kinnan-id",
        name="Kinnan, Bonder Prodigy",
        mana_cost="{G}{U}",
        mana_value=2,
        oracle_text="",
        type_line="Legendary Creature — Human Druid",
        power=2,
        toughness=2,
    )

    spark_double = create_permanent(
        permanent_id=2,
        name="Spark Double",
        copied_from=kinnan_card,
    )

    assert is_kinnan(spark_double) is True


def test_count_active_kinnan_effects() -> None:
    battlefield: Zone[Permanent] = Zone()

    battlefield.add(
        create_permanent(
            permanent_id=1,
            name="Kinnan, Bonder Prodigy",
        )
    )
    battlefield.add(
        create_permanent(
            permanent_id=2,
            name="Sol Ring",
            type_line="Artifact",
        )
    )

    assert count_active_kinnan_effects(battlefield) == 1


def test_count_multiple_kinnan_effects() -> None:
    kinnan_card = Card(
        id="kinnan-id",
        name="Kinnan, Bonder Prodigy",
        mana_cost="{G}{U}",
        mana_value=2,
        oracle_text="",
        type_line="Legendary Creature — Human Druid",
        power=2,
        toughness=2,
    )

    battlefield: Zone[Permanent] = Zone()

    battlefield.add(
        create_permanent(
            permanent_id=1,
            name="Kinnan, Bonder Prodigy",
        )
    )
    battlefield.add(
        create_permanent(
            permanent_id=2,
            name="Spark Double",
            copied_from=kinnan_card,
        )
    )

    assert count_active_kinnan_effects(battlefield) == 2


def test_choose_kinnan_bonus_mana_returns_selected_type() -> None:
    produced = {
        Mana.BLUE: 1,
        Mana.GREEN: 1,
    }

    result = choose_kinnan_bonus_mana(
        produced_mana=produced,
        selected_mana=Mana.GREEN,
    )

    assert result is Mana.GREEN


def test_choose_kinnan_bonus_mana_rejects_unproduced_type() -> None:
    produced = {
        Mana.COLORLESS: 2,
    }

    with pytest.raises(
        ValueError,
        match="must match a produced mana type",
    ):
        choose_kinnan_bonus_mana(
            produced_mana=produced,
            selected_mana=Mana.BLUE,
        )

def test_is_roaming_throne() -> None:
    throne = create_roaming_throne(
        permanent_id=1,
        chosen_type="Human",
    )

    assert is_roaming_throne(throne) is True


def test_roaming_throne_applies_when_human_is_chosen() -> None:
    throne = create_roaming_throne(
        permanent_id=1,
        chosen_type="Human",
    )

    assert roaming_throne_applies_to_kinnan(
        throne
    ) is True


def test_roaming_throne_applies_when_druid_is_chosen() -> None:
    throne = create_roaming_throne(
        permanent_id=1,
        chosen_type="Druid",
    )

    assert roaming_throne_applies_to_kinnan(
        throne
    ) is True


def test_roaming_throne_does_not_apply_for_unrelated_type() -> None:
    throne = create_roaming_throne(
        permanent_id=1,
        chosen_type="Golem",
    )

    assert roaming_throne_applies_to_kinnan(
        throne
    ) is False


def test_roaming_throne_without_chosen_type_does_not_apply() -> None:
    throne = create_roaming_throne(
        permanent_id=1,
        chosen_type=None,
    )

    assert roaming_throne_applies_to_kinnan(
        throne
    ) is False


def test_trigger_multiplier_is_one_without_throne() -> None:
    battlefield: Zone[Permanent] = Zone()

    assert count_kinnan_trigger_multipliers(
        battlefield
    ) == 1


def test_one_applicable_throne_doubles_each_kinnan_trigger() -> None:
    battlefield: Zone[Permanent] = Zone()

    battlefield.add(
        create_roaming_throne(
            permanent_id=1,
            chosen_type="Human",
        )
    )

    assert count_kinnan_trigger_multipliers(
        battlefield
    ) == 2


def test_two_applicable_thrones_triple_each_kinnan_trigger() -> None:
    battlefield: Zone[Permanent] = Zone()

    battlefield.add(
        create_roaming_throne(
            permanent_id=1,
            chosen_type="Human",
        )
    )
    battlefield.add(
        create_roaming_throne(
            permanent_id=2,
            chosen_type="Druid",
        )
    )

    assert count_kinnan_trigger_multipliers(
        battlefield
    ) == 3


def test_one_kinnan_without_throne_has_one_bonus_trigger() -> None:
    battlefield: Zone[Permanent] = Zone()

    battlefield.add(
        create_permanent(
            permanent_id=1,
            name="Kinnan, Bonder Prodigy",
        )
    )

    assert count_kinnan_bonus_triggers(
        battlefield
    ) == 1


def test_one_kinnan_and_one_throne_have_two_bonus_triggers() -> None:
    battlefield: Zone[Permanent] = Zone()

    battlefield.add(
        create_permanent(
            permanent_id=1,
            name="Kinnan, Bonder Prodigy",
        )
    )
    battlefield.add(
        create_roaming_throne(
            permanent_id=2,
            chosen_type="Human",
        )
    )

    assert count_kinnan_bonus_triggers(
        battlefield
    ) == 2


def test_two_kinnans_and_one_throne_have_four_bonus_triggers() -> None:
    kinnan_card = Card(
        id="kinnan-id",
        name="Kinnan, Bonder Prodigy",
        mana_cost="{G}{U}",
        mana_value=2,
        oracle_text="",
        type_line="Legendary Creature — Human Druid",
        power=2,
        toughness=2,
    )

    battlefield: Zone[Permanent] = Zone()

    battlefield.add(
        create_permanent(
            permanent_id=1,
            name="Kinnan, Bonder Prodigy",
        )
    )
    battlefield.add(
        create_permanent(
            permanent_id=2,
            name="Spark Double",
            copied_from=kinnan_card,
        )
    )
    battlefield.add(
        create_roaming_throne(
            permanent_id=3,
            chosen_type="Druid",
        )
    )

    assert count_kinnan_bonus_triggers(
        battlefield
    ) == 4


def test_throne_without_kinnan_produces_no_bonus_triggers() -> None:
    battlefield: Zone[Permanent] = Zone()

    battlefield.add(
        create_roaming_throne(
            permanent_id=1,
            chosen_type="Human",
        )
    )

    assert count_kinnan_bonus_triggers(
        battlefield
    ) == 0