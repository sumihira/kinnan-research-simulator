from __future__ import annotations

import pytest

from krs.abilities.activated import ActivatedAbility
from krs.cards.card import Card
from krs.engine.ability_executor import AbilityExecutor
from krs.game.permanent import Permanent


def create_permanent(
    *,
    tapped: bool,
    ability: ActivatedAbility,
    type_line: str = "Artifact",
    summoning_sick: bool = False,
) -> Permanent:
    card = Card(
        id="ability-source-id",
        name="Ability Source",
        mana_cost="{3}",
        mana_value=3,
        oracle_text="",
        type_line=type_line,
        activated_abilities=(
            ability,
        ),
    )

    return Permanent(
        permanent_id=1,
        card=card,
        owner_id=0,
        controller_id=0,
        tapped=tapped,
        summoning_sick=summoning_sick,
        entered_turn=1,
    )


def create_untap_self_ability() -> ActivatedAbility:
    return ActivatedAbility(
        ability_type="untap_self",
        mana_cost="{3}",
        requires_tap=False,
        parameters={},
    )


def test_validates_untap_self_for_tapped_permanent() -> None:
    source = create_permanent(
        tapped=True,
        ability=create_untap_self_ability(),
    )

    AbilityExecutor().validate(
        source=source,
        ability=source.effective_card.activated_abilities[0],
    )

    assert source.tapped is True


def test_executes_untap_self() -> None:
    source = create_permanent(
        tapped=True,
        ability=create_untap_self_ability(),
    )
    ability = source.effective_card.activated_abilities[0]
    executor = AbilityExecutor()

    executor.validate(
        source=source,
        ability=ability,
    )
    executor.execute(
        source=source,
        ability=ability,
    )

    assert source.tapped is False


def test_rejects_untap_self_for_untapped_permanent() -> None:
    source = create_permanent(
        tapped=False,
        ability=create_untap_self_ability(),
    )
    ability = source.effective_card.activated_abilities[0]

    with pytest.raises(
        ValueError,
        match="Permanent is already untapped",
    ):
        AbilityExecutor().validate(
            source=source,
            ability=ability,
        )

    assert source.tapped is False


def test_rejects_unsupported_activated_ability() -> None:
    ability = ActivatedAbility(
        ability_type="unsupported_effect",
        mana_cost="",
        requires_tap=False,
        parameters={},
    )
    source = create_permanent(
        tapped=False,
        ability=ability,
    )

    with pytest.raises(
        NotImplementedError,
        match="Unsupported activated ability type",
    ):
        AbilityExecutor().validate(
            source=source,
            ability=ability,
        )

    assert source.tapped is False


def test_tap_cost_taps_source_when_executed() -> None:
    ability = ActivatedAbility(
        ability_type="untap_self",
        mana_cost="",
        requires_tap=True,
        parameters={},
    )
    source = create_permanent(
        tapped=False,
        ability=ability,
    )

    with pytest.raises(
        ValueError,
        match="Permanent is already untapped",
    ):
        AbilityExecutor().validate(
            source=source,
            ability=ability,
        )

    assert source.tapped is False


def test_rejects_tap_cost_for_tapped_permanent() -> None:
    ability = ActivatedAbility(
        ability_type="unsupported_effect",
        mana_cost="",
        requires_tap=True,
        parameters={},
    )
    source = create_permanent(
        tapped=True,
        ability=ability,
    )

    with pytest.raises(
        ValueError,
        match="Tapped permanent cannot pay a tap activation cost",
    ):
        AbilityExecutor().validate(
            source=source,
            ability=ability,
        )

    assert source.tapped is True


def test_rejects_tap_cost_for_summoning_sick_creature() -> None:
    ability = ActivatedAbility(
        ability_type="unsupported_effect",
        mana_cost="",
        requires_tap=True,
        parameters={},
    )
    source = create_permanent(
        tapped=False,
        ability=ability,
        type_line="Creature — Elf Druid",
        summoning_sick=True,
    )

    with pytest.raises(
        ValueError,
        match="Summoning-sick creature cannot activate",
    ):
        AbilityExecutor().validate(
            source=source,
            ability=ability,
        )

    assert source.tapped is False