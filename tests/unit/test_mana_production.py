from __future__ import annotations

from types import MappingProxyType

import pytest

from krs.abilities.static import StaticAbility
from krs.cards.card import Card
from krs.game.permanent import Permanent
from krs.mana.mana_production import (
    mana_production_multiplier,
)


def create_card(
    *,
    card_id: str,
    name: str,
    type_line: str,
    static_abilities: tuple[StaticAbility, ...] = (),
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line=type_line,
        static_abilities=static_abilities,
    )


def create_permanent(
    *,
    permanent_id: int,
    card: Card,
    controller_id: int = 0,
) -> Permanent:
    return Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=controller_id,
        controller_id=controller_id,
        summoning_sick=False,
    )


def create_multiplier(
    *,
    permanent_id: int,
    multiplier: object = 3,
    controller_id: int = 0,
    permanent_type: str | None = None,
) -> Permanent:
    source_filter: dict[str, object] = {}

    if permanent_type is not None:
        source_filter["permanent_type"] = (
            permanent_type
        )

    card = create_card(
        card_id=f"multiplier-{permanent_id}",
        name="Nyxbloom Ancient",
        type_line=(
            "Enchantment Creature — Elemental"
        ),
        static_abilities=(
            StaticAbility(
                ability_type=(
                    "mana_production_multiplier"
                ),
                parameters=MappingProxyType(
                    {
                        "multiplier": multiplier,
                        "source_filter": (
                            source_filter
                        ),
                    }
                ),
            ),
        ),
    )

    return create_permanent(
        permanent_id=permanent_id,
        card=card,
        controller_id=controller_id,
    )


def test_default_multiplier_is_one() -> None:
    source = create_permanent(
        permanent_id=1,
        card=create_card(
            card_id="forest",
            name="Forest",
            type_line="Basic Land — Forest",
        ),
    )

    assert mana_production_multiplier(
        source=source,
        battlefield=(source,),
    ) == 1


def test_nyxbloom_ancient_triples_mana() -> None:
    source = create_permanent(
        permanent_id=1,
        card=create_card(
            card_id="sol-ring",
            name="Sol Ring",
            type_line="Artifact",
        ),
    )
    nyxbloom = create_multiplier(
        permanent_id=2,
    )

    assert mana_production_multiplier(
        source=source,
        battlefield=(
            source,
            nyxbloom,
        ),
    ) == 3


def test_multiple_multipliers_are_multiplicative() -> None:
    source = create_permanent(
        permanent_id=1,
        card=create_card(
            card_id="forest",
            name="Forest",
            type_line="Basic Land — Forest",
        ),
    )

    assert mana_production_multiplier(
        source=source,
        battlefield=(
            source,
            create_multiplier(
                permanent_id=2,
            ),
            create_multiplier(
                permanent_id=3,
            ),
        ),
    ) == 9


def test_other_controller_multiplier_is_ignored() -> None:
    source = create_permanent(
        permanent_id=1,
        card=create_card(
            card_id="forest",
            name="Forest",
            type_line="Basic Land — Forest",
        ),
    )
    opponent_multiplier = create_multiplier(
        permanent_id=2,
        controller_id=1,
    )

    assert mana_production_multiplier(
        source=source,
        battlefield=(
            source,
            opponent_multiplier,
        ),
    ) == 1


@pytest.mark.parametrize(
    "invalid_multiplier",
    (
        0,
        -1,
        True,
        "3",
    ),
)
def test_invalid_multiplier_is_rejected(
    invalid_multiplier: object,
) -> None:
    source = create_permanent(
        permanent_id=1,
        card=create_card(
            card_id="forest",
            name="Forest",
            type_line="Basic Land — Forest",
        ),
    )
    modifier = create_multiplier(
        permanent_id=2,
        multiplier=invalid_multiplier,
    )

    with pytest.raises(
        ValueError,
        match=(
            "Mana production multiplier must be "
            "an integer of at least 1"
        ),
    ):
        mana_production_multiplier(
            source=source,
            battlefield=(
                source,
                modifier,
            ),
        )