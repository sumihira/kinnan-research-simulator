from dataclasses import FrozenInstanceError
from uuid import UUID

import pytest

from krs.actions.activate_ability import ActivateAbilityAction
from krs.actions.cast_spell import CastSpellAction
from krs.actions.draw import DrawAction
from krs.actions.pass_priority import PassPriorityAction
from krs.actions.play_land import PlayLandAction
from krs.actions.tap_permanent import TapPermanentAction
from krs.cards.card import Card
from krs.game.permanent import Permanent
from krs.mana.mana_cost import ManaCost
from krs.mana.mana import Mana


def create_card(
    card_id: str = "card-id",
    name: str = "Test Card",
    type_line: str = "Artifact",
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="{1}",
        mana_value=1,
        oracle_text="",
        type_line=type_line,
    )


def create_permanent() -> Permanent:
    return Permanent(
        permanent_id=1,
        card=create_card(),
        owner_id=0,
        controller_id=0,
    )


def test_draw_action_can_be_created() -> None:
    action = DrawAction(
        player_id=0,
        turn_number=1,
        amount=1,
    )

    assert action.player_id == 0
    assert action.turn_number == 1
    assert action.amount == 1
    assert isinstance(action.action_id, UUID)


def test_each_action_gets_unique_id() -> None:
    first = DrawAction(
        player_id=0,
        turn_number=1,
        amount=1,
    )
    second = DrawAction(
        player_id=0,
        turn_number=1,
        amount=1,
    )

    assert first.action_id != second.action_id


def test_action_is_immutable() -> None:
    action = DrawAction(
        player_id=0,
        turn_number=1,
        amount=1,
    )

    with pytest.raises(FrozenInstanceError):
        action.amount = 2  # type: ignore[misc]


def test_play_land_action_stores_card() -> None:
    card = create_card(
        card_id="forest-id",
        name="Forest",
        type_line="Basic Land — Forest",
    )

    action = PlayLandAction(
        player_id=0,
        turn_number=1,
        card=card,
    )

    assert action.card is card


def test_cast_spell_action_stores_card_and_cost() -> None:
    card = create_card(
        card_id="sol-ring-id",
        name="Sol Ring",
    )
    cost = ManaCost(generic=1)

    action = CastSpellAction(
        player_id=0,
        turn_number=1,
        card=card,
        cost=cost,
    )

    assert action.card is card
    assert action.cost == cost


def test_activate_ability_action_stores_source_and_index() -> None:
    permanent = create_permanent()

    action = ActivateAbilityAction(
        player_id=0,
        turn_number=2,
        source=permanent,
        ability_index=1,
    )

    assert action.source is permanent
    assert action.ability_index == 1


def test_activate_ability_action_defaults_to_first_ability() -> None:
    permanent = create_permanent()

    action = ActivateAbilityAction(
        player_id=0,
        turn_number=2,
        source=permanent,
    )

    assert action.ability_index == 0


def test_tap_permanent_action_stores_permanent_and_mana() -> None:
    permanent = create_permanent()

    action = TapPermanentAction(
        player_id=0,
        turn_number=2,
        permanent=permanent,
        mana=Mana.BLUE,
    )

    assert action.permanent is permanent
    assert action.mana is Mana.BLUE


def test_pass_priority_action_can_be_created() -> None:
    action = PassPriorityAction(
        player_id=0,
        turn_number=3,
    )

    assert action.player_id == 0
    assert action.turn_number == 3
    assert isinstance(action.action_id, UUID)

def test_tap_permanent_action_stores_values() -> None:
    permanent = create_permanent()

    action = TapPermanentAction(
        player_id=0,
        turn_number=2,
        permanent=permanent,
        mana=Mana.COLORLESS,
        ability_index=1,
    )

    assert action.permanent is permanent
    assert action.mana is Mana.COLORLESS
    assert action.ability_index == 1

def test_tap_permanent_action_defaults_to_first_ability() -> None:
    permanent = create_permanent()

    action = TapPermanentAction(
        player_id=0,
        turn_number=2,
        permanent=permanent,
        mana=Mana.COLORLESS,
    )

    assert action.ability_index == 0