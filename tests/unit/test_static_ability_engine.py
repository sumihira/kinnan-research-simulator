from __future__ import annotations

import pytest

from krs.abilities.static import StaticAbility
from krs.cards.card import Card
from krs.engine.static_ability_engine import StaticAbilityEngine
from krs.game.permanent import Permanent
from krs.game.zone import Zone
from krs.mana.mana import Mana
from krs.abilities.static import StaticAbility


def create_permanent(
    *,
    permanent_id: int,
    name: str,
    type_line: str,
    controller_id: int = 0,
    static_abilities: tuple[StaticAbility, ...] = (),
) -> Permanent:
    card = Card(
        id=f"{name.casefold().replace(' ', '-')}-id",
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line=type_line,
        static_abilities=static_abilities,
    )

    return Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=controller_id,
        controller_id=controller_id,
        tapped=False,
        summoning_sick=False,
        entered_turn=1,
    )


def create_kinnan(
    *,
    permanent_id: int = 10,
    controller_id: int = 0,
    additional_amount: object = 1,
    mana_selection: object = "produced_type",
    permanent_type: object = "nonland",
) -> Permanent:
    return create_permanent(
        permanent_id=permanent_id,
        name="Kinnan, Bonder Prodigy",
        type_line="Legendary Creature — Human Druid",
        controller_id=controller_id,
        static_abilities=(
            StaticAbility(
                ability_type="additional_nonland_mana",
                parameters={
                    "source_filter": {
                        "permanent_type": permanent_type,
                    },
                    "additional_amount": additional_amount,
                    "mana_selection": mana_selection,
                },
            ),
        ),
    )


def test_returns_no_additional_mana_without_static_ability() -> None:
    source = create_permanent(
        permanent_id=1,
        name="Sol Ring",
        type_line="Artifact",
    )
    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)

    additional_mana = (
        StaticAbilityEngine()
        .calculate_additional_nonland_mana(
            source=source,
            produced_mana={
                Mana.COLORLESS: 2,
            },
            selected_mana=Mana.COLORLESS,
            battlefield=battlefield,
        )
    )

    assert additional_mana == {}


def test_kinnan_adds_one_colorless_mana_to_sol_ring() -> None:
    source = create_permanent(
        permanent_id=1,
        name="Sol Ring",
        type_line="Artifact",
    )
    kinnan = create_kinnan()

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(kinnan)

    additional_mana = (
        StaticAbilityEngine()
        .calculate_additional_nonland_mana(
            source=source,
            produced_mana={
                Mana.COLORLESS: 2,
            },
            selected_mana=Mana.COLORLESS,
            battlefield=battlefield,
        )
    )

    assert additional_mana == {
        Mana.COLORLESS: 1,
    }


def test_kinnan_adds_one_green_mana_to_mana_creature() -> None:
    source = create_permanent(
        permanent_id=1,
        name="Llanowar Elves",
        type_line="Creature — Elf Druid",
    )
    kinnan = create_kinnan()

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(kinnan)

    additional_mana = (
        StaticAbilityEngine()
        .calculate_additional_nonland_mana(
            source=source,
            produced_mana={
                Mana.GREEN: 1,
            },
            selected_mana=Mana.GREEN,
            battlefield=battlefield,
        )
    )

    assert additional_mana == {
        Mana.GREEN: 1,
    }


def test_multiple_static_abilities_accumulate() -> None:
    source = create_permanent(
        permanent_id=1,
        name="Sol Ring",
        type_line="Artifact",
    )
    first_kinnan = create_kinnan(
        permanent_id=10,
    )
    second_kinnan = create_kinnan(
        permanent_id=11,
    )

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(first_kinnan)
    battlefield.add(second_kinnan)

    additional_mana = (
        StaticAbilityEngine()
        .calculate_additional_nonland_mana(
            source=source,
            produced_mana={
                Mana.COLORLESS: 2,
            },
            selected_mana=Mana.COLORLESS,
            battlefield=battlefield,
        )
    )

    assert additional_mana == {
        Mana.COLORLESS: 2,
    }


def test_kinnan_does_not_add_mana_for_land_source() -> None:
    source = create_permanent(
        permanent_id=1,
        name="Forest",
        type_line="Basic Land — Forest",
    )
    kinnan = create_kinnan()

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(kinnan)

    additional_mana = (
        StaticAbilityEngine()
        .calculate_additional_nonland_mana(
            source=source,
            produced_mana={
                Mana.GREEN: 1,
            },
            selected_mana=Mana.GREEN,
            battlefield=battlefield,
        )
    )

    assert additional_mana == {}


def test_static_ability_requires_same_controller() -> None:
    source = create_permanent(
        permanent_id=1,
        name="Sol Ring",
        type_line="Artifact",
        controller_id=0,
    )
    opposing_kinnan = create_kinnan(
        controller_id=1,
    )

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(opposing_kinnan)

    additional_mana = (
        StaticAbilityEngine()
        .calculate_additional_nonland_mana(
            source=source,
            produced_mana={
                Mana.COLORLESS: 2,
            },
            selected_mana=Mana.COLORLESS,
            battlefield=battlefield,
        )
    )

    assert additional_mana == {}


def test_configured_additional_amount_is_applied() -> None:
    source = create_permanent(
        permanent_id=1,
        name="Sol Ring",
        type_line="Artifact",
    )
    modifier = create_kinnan(
        additional_amount=2,
    )

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(modifier)

    additional_mana = (
        StaticAbilityEngine()
        .calculate_additional_nonland_mana(
            source=source,
            produced_mana={
                Mana.COLORLESS: 2,
            },
            selected_mana=Mana.COLORLESS,
            battlefield=battlefield,
        )
    )

    assert additional_mana == {
        Mana.COLORLESS: 2,
    }


@pytest.mark.parametrize(
    "additional_amount",
    [
        True,
        1.5,
        "1",
        None,
    ],
)
def test_rejects_invalid_additional_amount(
    additional_amount: object,
) -> None:
    source = create_permanent(
        permanent_id=1,
        name="Sol Ring",
        type_line="Artifact",
    )
    modifier = create_kinnan(
        additional_amount=additional_amount,
    )

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(modifier)

    with pytest.raises(
        ValueError,
        match="additional_amount must be an integer",
    ):
        (
            StaticAbilityEngine()
            .calculate_additional_nonland_mana(
                source=source,
                produced_mana={
                    Mana.COLORLESS: 2,
                },
                selected_mana=Mana.COLORLESS,
                battlefield=battlefield,
            )
        )


def test_rejects_negative_additional_amount() -> None:
    source = create_permanent(
        permanent_id=1,
        name="Sol Ring",
        type_line="Artifact",
    )
    modifier = create_kinnan(
        additional_amount=-1,
    )

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(modifier)

    with pytest.raises(
        ValueError,
        match="additional_amount must not be negative",
    ):
        (
            StaticAbilityEngine()
            .calculate_additional_nonland_mana(
                source=source,
                produced_mana={
                    Mana.COLORLESS: 2,
                },
                selected_mana=Mana.COLORLESS,
                battlefield=battlefield,
            )
        )


def test_rejects_unsupported_mana_selection() -> None:
    source = create_permanent(
        permanent_id=1,
        name="Sol Ring",
        type_line="Artifact",
    )
    modifier = create_kinnan(
        mana_selection="any_color",
    )

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(modifier)

    with pytest.raises(
        ValueError,
        match="Unsupported mana selection mode",
    ):
        (
            StaticAbilityEngine()
            .calculate_additional_nonland_mana(
                source=source,
                produced_mana={
                    Mana.COLORLESS: 2,
                },
                selected_mana=Mana.COLORLESS,
                battlefield=battlefield,
            )
        )


def test_rejects_selected_mana_not_produced_by_source() -> None:
    source = create_permanent(
        permanent_id=1,
        name="Test Mana Source",
        type_line="Artifact",
    )
    modifier = create_kinnan()

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(modifier)

    with pytest.raises(
        ValueError,
        match="Selected mana was not produced by the source",
    ):
        (
            StaticAbilityEngine()
            .calculate_additional_nonland_mana(
                source=source,
                produced_mana={
                    Mana.GREEN: 1,
                },
                selected_mana=Mana.BLUE,
                battlefield=battlefield,
            )
        )