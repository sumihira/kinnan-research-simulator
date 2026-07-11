import pytest

from krs.abilities.mana_ability import ManaAbility
from krs.mana.mana import Mana


def test_mana_ability_can_be_created() -> None:
    ability = ManaAbility(
        produced_mana={
            Mana.COLORLESS: 2,
        }
    )

    assert ability.produced_mana[Mana.COLORLESS] == 2
    assert ability.requires_tap is True
    assert ability.total_produced == 2


def test_mana_ability_can_produce_expected_type() -> None:
    ability = ManaAbility(
        produced_mana={
            Mana.BLUE: 1,
            Mana.GREEN: 1,
        }
    )

    assert ability.can_produce(Mana.BLUE) is True
    assert ability.can_produce(Mana.GREEN) is True
    assert ability.can_produce(Mana.RED) is False


def test_mana_ability_rejects_empty_output() -> None:
    with pytest.raises(
        ValueError,
        match="must produce at least one mana",
    ):
        ManaAbility(produced_mana={})


@pytest.mark.parametrize("amount", [0, -1, -5])
def test_mana_ability_rejects_non_positive_output(
    amount: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="must be greater than zero",
    ):
        ManaAbility(
            produced_mana={
                Mana.COLORLESS: amount,
            }
        )


def test_produced_mana_mapping_cannot_be_modified() -> None:
    ability = ManaAbility(
        produced_mana={
            Mana.COLORLESS: 2,
        }
    )

    with pytest.raises(TypeError):
        ability.produced_mana[Mana.COLORLESS] = 3  # type: ignore[index]