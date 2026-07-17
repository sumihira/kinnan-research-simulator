from __future__ import annotations

from types import MappingProxyType

import pytest

from krs.abilities.static import StaticAbility
from krs.cards.card import Card
from krs.commanders.kinnan_activation_cost import (
    kinnan_activation_cost,
)
from krs.game.permanent import Permanent
from krs.game.player import Player


def create_card(
    *,
    card_id: str,
    name: str,
    static_abilities: tuple[StaticAbility, ...] = (),
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line="Enchantment",
        static_abilities=static_abilities,
    )


def create_reducer(
    *,
    permanent_id: int,
    name: str,
    amount: int = 2,
    source_type: str = "creature",
) -> Permanent:
    card = create_card(
        card_id=f"{name.casefold()}-id",
        name=name,
        static_abilities=(
            StaticAbility(
                ability_type=(
                    "activated_ability_cost_reduction"
                ),
                parameters=MappingProxyType(
                    {
                        "source_type": source_type,
                        "amount": amount,
                        "minimum_total_mana": 1,
                    }
                ),
            ),
        ),
    )

    return Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=0,
        controller_id=0,
        summoning_sick=False,
    )


def create_player() -> Player:
    return Player(
        player_id=0,
    )


def test_default_kinnan_activation_cost() -> None:
    player = create_player()

    cost = kinnan_activation_cost(player)

    assert cost.generic == 5
    assert cost.green == 1
    assert cost.blue == 1
    assert cost.total == 7


def test_training_grounds_reduces_generic_cost_by_two() -> None:
    player = create_player()

    player.battlefield.add(
        create_reducer(
            permanent_id=1,
            name="Training Grounds",
        )
    )

    cost = kinnan_activation_cost(player)

    assert cost.generic == 3
    assert cost.green == 1
    assert cost.blue == 1
    assert cost.total == 5


def test_biomancers_familiar_reduces_generic_cost_by_two() -> None:
    player = create_player()

    player.battlefield.add(
        create_reducer(
            permanent_id=1,
            name="Biomancer's Familiar",
        )
    )

    cost = kinnan_activation_cost(player)

    assert cost.generic == 3
    assert cost.green == 1
    assert cost.blue == 1
    assert cost.total == 5


def test_cost_reductions_stack() -> None:
    player = create_player()

    player.battlefield.add(
        create_reducer(
            permanent_id=1,
            name="Training Grounds",
        )
    )
    player.battlefield.add(
        create_reducer(
            permanent_id=2,
            name="Biomancer's Familiar",
        )
    )

    cost = kinnan_activation_cost(player)

    assert cost.generic == 1
    assert cost.green == 1
    assert cost.blue == 1
    assert cost.total == 3


def test_generic_cost_does_not_become_negative() -> None:
    player = create_player()

    player.battlefield.add(
        create_reducer(
            permanent_id=1,
            name="First Reducer",
            amount=4,
        )
    )
    player.battlefield.add(
        create_reducer(
            permanent_id=2,
            name="Second Reducer",
            amount=4,
        )
    )

    cost = kinnan_activation_cost(player)

    assert cost.generic == 0
    assert cost.green == 1
    assert cost.blue == 1
    assert cost.total == 2


def test_noncreature_reduction_is_ignored() -> None:
    player = create_player()

    player.battlefield.add(
        create_reducer(
            permanent_id=1,
            name="Artifact Reducer",
            source_type="artifact",
        )
    )

    cost = kinnan_activation_cost(player)

    assert cost.generic == 5
    assert cost.total == 7


@pytest.mark.parametrize(
    "invalid_amount",
    (
        -1,
        True,
        "2",
    ),
)
def test_invalid_reduction_amount_is_rejected(
    invalid_amount: object,
) -> None:
    player = create_player()

    ability = StaticAbility(
        ability_type=(
            "activated_ability_cost_reduction"
        ),
        parameters={
            "source_type": "creature",
            "amount": invalid_amount,
        },
    )

    card = create_card(
        card_id="invalid-reducer-id",
        name="Invalid Reducer",
        static_abilities=(
            ability,
        ),
    )

    player.battlefield.add(
        Permanent(
            permanent_id=1,
            card=card,
            owner_id=0,
            controller_id=0,
            summoning_sick=False,
        )
    )

    with pytest.raises(
        ValueError,
        match=(
            "Activated ability cost reduction amount "
            "must be a non-negative integer"
        ),
    ):
        kinnan_activation_cost(player)