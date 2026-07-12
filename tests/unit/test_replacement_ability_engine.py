from __future__ import annotations

import pytest

from krs.abilities.replacement import ReplacementAbility
from krs.cards.card import Card
from krs.engine.replacement_ability_engine import (
    ReplacementAbilityEngine,
)
from krs.game.permanent import Permanent


def create_roaming_throne() -> Permanent:
    card = Card(
        id="roaming-throne-id",
        name="Roaming Throne",
        mana_cost="{4}",
        mana_value=4,
        oracle_text=(
            "As Roaming Throne enters, choose a creature type."
        ),
        type_line="Artifact Creature — Golem",
        power="4",
        toughness="4",
        replacement_abilities=(
            ReplacementAbility(
                ability_type="choose_creature_type",
                event="enters_battlefield",
                parameters={
                    "choice_type": "creature_type",
                },
            ),
        ),
    )

    return Permanent(
        permanent_id=1,
        card=card,
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
        entered_turn=1,
    )


def test_applies_chosen_creature_type() -> None:
    permanent = create_roaming_throne()

    ReplacementAbilityEngine().apply_enters_battlefield_replacements(
        permanent=permanent,
        chosen_values={
            "creature_type": "Druid",
        },
    )

    assert permanent.chosen_values == {
        "creature_type": "Druid",
    }


def test_strips_chosen_creature_type() -> None:
    permanent = create_roaming_throne()

    ReplacementAbilityEngine().apply_enters_battlefield_replacements(
        permanent=permanent,
        chosen_values={
            "creature_type": "  Druid  ",
        },
    )

    assert permanent.chosen_values["creature_type"] == "Druid"


def test_requires_chosen_creature_type() -> None:
    permanent = create_roaming_throne()

    with pytest.raises(
        ValueError,
        match="Required chosen value was not provided",
    ):
        ReplacementAbilityEngine().apply_enters_battlefield_replacements(
            permanent=permanent,
            chosen_values={},
        )

    assert permanent.chosen_values == {}


def test_ignores_replacement_for_other_event() -> None:
    card = Card(
        id="other-event-id",
        name="Other Event Permanent",
        mana_cost="{1}",
        mana_value=1,
        oracle_text="",
        type_line="Artifact",
        replacement_abilities=(
            ReplacementAbility(
                ability_type="choose_creature_type",
                event="leaves_battlefield",
                parameters={
                    "choice_type": "creature_type",
                },
            ),
        ),
    )
    permanent = Permanent(
        permanent_id=1,
        card=card,
        owner_id=0,
        controller_id=0,
    )

    ReplacementAbilityEngine().apply_enters_battlefield_replacements(
        permanent=permanent,
        chosen_values={},
    )

    assert permanent.chosen_values == {}


def test_rejects_unsupported_enters_battlefield_replacement() -> None:
    card = Card(
        id="unsupported-id",
        name="Unsupported Permanent",
        mana_cost="{1}",
        mana_value=1,
        oracle_text="",
        type_line="Artifact",
        replacement_abilities=(
            ReplacementAbility(
                ability_type="unsupported_replacement",
                event="enters_battlefield",
                parameters={},
            ),
        ),
    )
    permanent = Permanent(
        permanent_id=1,
        card=card,
        owner_id=0,
        controller_id=0,
    )

    with pytest.raises(
        NotImplementedError,
        match="Unsupported replacement ability type",
    ):
        ReplacementAbilityEngine().apply_enters_battlefield_replacements(
            permanent=permanent,
            chosen_values={},
        )