from __future__ import annotations

from types import MappingProxyType

import pytest

from krs.abilities.activated import ActivatedAbility
from krs.abilities.replacement import ReplacementAbility
from krs.abilities.static import StaticAbility
from krs.abilities.triggered import TriggeredAbility
from krs.cards.ability_factory import AbilityFactory
from krs.mana.mana import Mana


def test_creates_sol_ring_mana_ability() -> None:
    ability = AbilityFactory.create_mana_ability(
        {
            "produces": {
                "COLORLESS": 2,
            },
            "requires_tap": True,
        }
    )

    assert ability.produced_mana == {
        Mana.COLORLESS: 2,
    }
    assert ability.requires_tap is True
    assert ability.total_produced == 2


def test_creates_llanowar_elves_mana_ability() -> None:
    ability = AbilityFactory.create_mana_ability(
        {
            "produces": {
                "GREEN": 1,
            },
        }
    )

    assert ability.produced_mana == {
        Mana.GREEN: 1,
    }
    assert ability.requires_tap is True


def test_creates_multicolor_mana_ability() -> None:
    ability = AbilityFactory.create_mana_ability(
        {
            "produces": {
                "BLUE": 1,
                "GREEN": 1,
            },
            "requires_tap": False,
        }
    )

    assert ability.produced_mana == {
        Mana.BLUE: 1,
        Mana.GREEN: 1,
    }
    assert ability.requires_tap is False
    assert ability.total_produced == 2


def test_mana_name_is_case_insensitive() -> None:
    ability = AbilityFactory.create_mana_ability(
        {
            "produces": {
                "colorless": 2,
            },
        }
    )

    assert ability.produced_mana == {
        Mana.COLORLESS: 2,
    }


def test_rejects_missing_produces() -> None:
    with pytest.raises(
        ValueError,
        match="requires a produces mapping",
    ):
        AbilityFactory.create_mana_ability({})


@pytest.mark.parametrize(
    "produces",
    [
        None,
        [],
        "COLORLESS",
        2,
    ],
)
def test_rejects_non_mapping_produces(
    produces: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="requires a produces mapping",
    ):
        AbilityFactory.create_mana_ability(
            {
                "produces": produces,
            }
        )


def test_rejects_non_string_mana_name() -> None:
    with pytest.raises(
        ValueError,
        match="mana name must be a string",
    ):
        AbilityFactory.create_mana_ability(
            {
                "produces": {
                    1: 2,
                },
            }
        )


def test_rejects_unknown_mana_type() -> None:
    with pytest.raises(
        ValueError,
        match="Unknown mana type: ENERGY",
    ):
        AbilityFactory.create_mana_ability(
            {
                "produces": {
                    "ENERGY": 1,
                },
            }
        )


@pytest.mark.parametrize(
    "amount",
    [
        0,
        -1,
        -5,
    ],
)
def test_rejects_non_positive_mana_amount(
    amount: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="must be greater than zero",
    ):
        AbilityFactory.create_mana_ability(
            {
                "produces": {
                    "COLORLESS": amount,
                },
            }
        )


@pytest.mark.parametrize(
    "amount",
    [
        True,
        False,
        1.5,
        "2",
        None,
    ],
)
def test_rejects_non_integer_mana_amount(
    amount: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="must be an integer",
    ):
        AbilityFactory.create_mana_ability(
            {
                "produces": {
                    "COLORLESS": amount,
                },
            }
        )


@pytest.mark.parametrize(
    "requires_tap",
    [
        1,
        0,
        "true",
        None,
    ],
)
def test_rejects_non_boolean_requires_tap(
    requires_tap: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="requires_tap must be a boolean",
    ):
        AbilityFactory.create_mana_ability(
            {
                "produces": {
                    "COLORLESS": 2,
                },
                "requires_tap": requires_tap,
            }
        )


def test_creates_activated_ability() -> None:
    ability = AbilityFactory.create_activated_ability(
        {
            "ability_type": "untap_self",
            "mana_cost": "{3}",
            "requires_tap": False,
            "parameters": {
                "target": "self",
            },
        }
    )

    assert isinstance(ability, ActivatedAbility)
    assert ability.ability_type == "untap_self"
    assert ability.mana_cost == "{3}"
    assert ability.requires_tap is False
    assert ability.parameters == {
        "target": "self",
    }


def test_activated_ability_uses_defaults() -> None:
    ability = AbilityFactory.create_activated_ability(
        {
            "ability_type": "activate_kinnan",
        }
    )

    assert ability.mana_cost == ""
    assert ability.requires_tap is False
    assert ability.parameters == {}


def test_creates_static_ability() -> None:
    ability = AbilityFactory.create_static_ability(
        {
            "ability_type": "additional_nonland_mana",
            "parameters": {
                "additional_amount": 1,
            },
        }
    )

    assert isinstance(ability, StaticAbility)
    assert ability.ability_type == "additional_nonland_mana"
    assert ability.parameters == {
        "additional_amount": 1,
    }


def test_creates_triggered_ability() -> None:
    ability = AbilityFactory.create_triggered_ability(
        {
            "ability_type": "draw_card",
            "event": "enters_battlefield",
            "parameters": {
                "amount": 1,
            },
        }
    )

    assert isinstance(ability, TriggeredAbility)
    assert ability.ability_type == "draw_card"
    assert ability.event == "enters_battlefield"
    assert ability.parameters == {
        "amount": 1,
    }


def test_creates_replacement_ability() -> None:
    ability = AbilityFactory.create_replacement_ability(
        {
            "ability_type": "choose_creature_type",
            "event": "enters_battlefield",
            "parameters": {
                "choice_type": "creature_type",
            },
        }
    )

    assert isinstance(ability, ReplacementAbility)
    assert ability.ability_type == "choose_creature_type"
    assert ability.event == "enters_battlefield"
    assert ability.parameters == {
        "choice_type": "creature_type",
    }


@pytest.mark.parametrize(
    "creator",
    [
        AbilityFactory.create_activated_ability,
        AbilityFactory.create_static_ability,
        AbilityFactory.create_triggered_ability,
        AbilityFactory.create_replacement_ability,
    ],
)
def test_rejects_missing_ability_type(
    creator: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="ability_type must be a non-empty string",
    ):
        creator({})  # type: ignore[operator]


@pytest.mark.parametrize(
    "creator",
    [
        AbilityFactory.create_triggered_ability,
        AbilityFactory.create_replacement_ability,
    ],
)
def test_rejects_missing_event(
    creator: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="event must be a non-empty string",
    ):
        creator(  # type: ignore[operator]
            {
                "ability_type": "test_ability",
            }
        )


def test_rejects_non_string_mana_cost() -> None:
    with pytest.raises(
        ValueError,
        match="mana_cost must be a string",
    ):
        AbilityFactory.create_activated_ability(
            {
                "ability_type": "untap_self",
                "mana_cost": 3,
            }
        )


def test_rejects_non_mapping_parameters() -> None:
    with pytest.raises(
        ValueError,
        match="parameters must be a mapping",
    ):
        AbilityFactory.create_static_ability(
            {
                "ability_type": "test_ability",
                "parameters": [],
            }
        )


@pytest.mark.parametrize(
    "ability",
    [
        ActivatedAbility(
            ability_type="test_activated",
            parameters={"value": 1},
        ),
        StaticAbility(
            ability_type="test_static",
            parameters={"value": 1},
        ),
        TriggeredAbility(
            ability_type="test_triggered",
            event="test_event",
            parameters={"value": 1},
        ),
        ReplacementAbility(
            ability_type="test_replacement",
            event="test_event",
            parameters={"value": 1},
        ),
    ],
)
def test_ability_parameters_are_immutable(
    ability: object,
) -> None:
    parameters = getattr(ability, "parameters")

    assert isinstance(parameters, MappingProxyType)

    with pytest.raises(TypeError):
        parameters["value"] = 2