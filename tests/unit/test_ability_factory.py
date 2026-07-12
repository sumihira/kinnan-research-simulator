import pytest

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

    assert ability.produced_mana[Mana.COLORLESS] == 2
    assert ability.requires_tap is True


def test_rejects_unknown_mana_type() -> None:
    with pytest.raises(
        ValueError,
        match="Unknown mana type",
    ):
        AbilityFactory.create_mana_ability(
            {
                "produces": {
                    "UNKNOWN": 1,
                },
            }
        )