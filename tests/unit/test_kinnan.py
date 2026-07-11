import pytest

from krs.cards.card import Card
from krs.commanders.kinnan import (
    choose_kinnan_bonus_mana,
    count_active_kinnan_effects,
    is_kinnan,
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