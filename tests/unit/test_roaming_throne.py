from __future__ import annotations

import pytest

from krs.abilities.static import StaticAbility
from krs.abilities.triggered import TriggeredAbility
from krs.cards.card import Card
from krs.engine.trigger_engine import TriggerEngine
from krs.game.permanent import Permanent
from krs.game.zone import Zone


def create_triggered_creature(
    *,
    permanent_id: int = 1,
    controller_id: int = 0,
    creature_types: str = "Druid",
) -> Permanent:
    card = Card(
        id=f"source-{permanent_id}-id",
        name="Triggered Creature",
        mana_cost="{1}{G}",
        mana_value=2,
        oracle_text=(
            "Whenever another creature enters, draw a card."
        ),
        type_line=f"Creature — {creature_types}",
        triggered_abilities=(
            TriggeredAbility(
                ability_type="draw_card",
                event="creature_enters_battlefield",
                parameters={
                    "amount": 1,
                },
            ),
        ),
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


def create_roaming_throne(
    *,
    permanent_id: int = 10,
    controller_id: int = 0,
    chosen_creature_type: str | None = "Druid",
    additional_trigger_count: int = 1,
) -> Permanent:
    card = Card(
        id=f"roaming-throne-{permanent_id}-id",
        name="Roaming Throne",
        mana_cost="{4}",
        mana_value=4,
        oracle_text=(
            "As Roaming Throne enters, choose a creature type."
        ),
        type_line="Artifact Creature — Golem",
        static_abilities=(
            StaticAbility(
                ability_type="additional_trigger",
                parameters={
                    "additional_trigger_count": (
                        additional_trigger_count
                    ),
                    "source_filter": {
                        "other_creature": True,
                        "chosen_creature_type": True,
                    },
                    "controller_only": True,
                },
            ),
        ),
    )

    permanent = Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=controller_id,
        controller_id=controller_id,
        tapped=False,
        summoning_sick=False,
        entered_turn=1,
    )

    if chosen_creature_type is not None:
        permanent.chosen_values["creature_type"] = (
            chosen_creature_type
        )

    return permanent


def get_triggered_ability(
    source: Permanent,
) -> TriggeredAbility:
    return source.effective_card.triggered_abilities[0]


def test_triggered_ability_triggers_once_without_roaming_throne() -> None:
    source = create_triggered_creature()
    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)

    trigger_count = TriggerEngine().count_triggers(
        source=source,
        ability=get_triggered_ability(source),
        battlefield=battlefield,
    )

    assert trigger_count == 1


def test_roaming_throne_adds_one_trigger() -> None:
    source = create_triggered_creature()
    roaming_throne = create_roaming_throne()

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(roaming_throne)

    trigger_count = TriggerEngine().count_triggers(
        source=source,
        ability=get_triggered_ability(source),
        battlefield=battlefield,
    )

    assert trigger_count == 2


def test_multiple_roaming_thrones_stack() -> None:
    source = create_triggered_creature()
    first_throne = create_roaming_throne(
        permanent_id=10,
    )
    second_throne = create_roaming_throne(
        permanent_id=11,
    )

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(first_throne)
    battlefield.add(second_throne)

    trigger_count = TriggerEngine().count_triggers(
        source=source,
        ability=get_triggered_ability(source),
        battlefield=battlefield,
    )

    assert trigger_count == 3


def test_roaming_throne_does_not_modify_its_own_trigger() -> None:
    roaming_throne = create_roaming_throne()

    source_card = Card(
        id="roaming-throne-trigger-source-id",
        name="Roaming Throne",
        mana_cost="{4}",
        mana_value=4,
        oracle_text="Test triggered ability.",
        type_line="Artifact Creature — Golem",
        static_abilities=(
            *roaming_throne.effective_card.static_abilities,
        ),
        triggered_abilities=(
            TriggeredAbility(
                ability_type="test_trigger",
                event="test_event",
                parameters={},
            ),
        ),
    )
    source = Permanent(
        permanent_id=roaming_throne.permanent_id,
        card=source_card,
        owner_id=0,
        controller_id=0,
        tapped=False,
        summoning_sick=False,
        entered_turn=1,
        chosen_values={
            "creature_type": "Golem",
        },
    )

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)

    trigger_count = TriggerEngine().count_triggers(
        source=source,
        ability=get_triggered_ability(source),
        battlefield=battlefield,
    )

    assert trigger_count == 1


def test_roaming_throne_requires_same_controller() -> None:
    source = create_triggered_creature(
        controller_id=0,
    )
    roaming_throne = create_roaming_throne(
        controller_id=1,
    )

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(roaming_throne)

    trigger_count = TriggerEngine().count_triggers(
        source=source,
        ability=get_triggered_ability(source),
        battlefield=battlefield,
    )

    assert trigger_count == 1


def test_roaming_throne_requires_chosen_creature_type_match() -> None:
    source = create_triggered_creature(
        creature_types="Elf Druid",
    )
    roaming_throne = create_roaming_throne(
        chosen_creature_type="Wizard",
    )

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(roaming_throne)

    trigger_count = TriggerEngine().count_triggers(
        source=source,
        ability=get_triggered_ability(source),
        battlefield=battlefield,
    )

    assert trigger_count == 1


def test_roaming_throne_matches_creature_type_case_insensitively() -> None:
    source = create_triggered_creature(
        creature_types="Elf Druid",
    )
    roaming_throne = create_roaming_throne(
        chosen_creature_type="druid",
    )

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(roaming_throne)

    trigger_count = TriggerEngine().count_triggers(
        source=source,
        ability=get_triggered_ability(source),
        battlefield=battlefield,
    )

    assert trigger_count == 2


def test_roaming_throne_requires_chosen_value() -> None:
    source = create_triggered_creature()
    roaming_throne = create_roaming_throne(
        chosen_creature_type=None,
    )

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(roaming_throne)

    trigger_count = TriggerEngine().count_triggers(
        source=source,
        ability=get_triggered_ability(source),
        battlefield=battlefield,
    )

    assert trigger_count == 1


def test_roaming_throne_does_not_modify_noncreature_source() -> None:
    card = Card(
        id="artifact-id",
        name="Triggered Artifact",
        mana_cost="{2}",
        mana_value=2,
        oracle_text="Whenever an artifact enters, draw a card.",
        type_line="Artifact",
        triggered_abilities=(
            TriggeredAbility(
                ability_type="draw_card",
                event="artifact_enters_battlefield",
                parameters={},
            ),
        ),
    )
    source = Permanent(
        permanent_id=1,
        card=card,
        owner_id=0,
        controller_id=0,
        tapped=False,
        summoning_sick=False,
        entered_turn=1,
    )
    roaming_throne = create_roaming_throne()

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(roaming_throne)

    trigger_count = TriggerEngine().count_triggers(
        source=source,
        ability=get_triggered_ability(source),
        battlefield=battlefield,
    )

    assert trigger_count == 1


def test_configured_additional_trigger_count_is_applied() -> None:
    source = create_triggered_creature()
    roaming_throne = create_roaming_throne(
        additional_trigger_count=2,
    )

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(roaming_throne)

    trigger_count = TriggerEngine().count_triggers(
        source=source,
        ability=get_triggered_ability(source),
        battlefield=battlefield,
    )

    assert trigger_count == 3


@pytest.mark.parametrize(
    "additional_trigger_count",
    [
        True,
        1.5,
        "1",
        None,
    ],
)
def test_rejects_invalid_additional_trigger_count(
    additional_trigger_count: object,
) -> None:
    source = create_triggered_creature()

    card = Card(
        id="invalid-throne-id",
        name="Invalid Roaming Throne",
        mana_cost="{4}",
        mana_value=4,
        oracle_text="",
        type_line="Artifact Creature — Golem",
        static_abilities=(
            StaticAbility(
                ability_type="additional_trigger",
                parameters={
                    "additional_trigger_count": (
                        additional_trigger_count
                    ),
                    "source_filter": {
                        "other_creature": True,
                        "chosen_creature_type": True,
                    },
                    "controller_only": True,
                },
            ),
        ),
    )
    roaming_throne = Permanent(
        permanent_id=10,
        card=card,
        owner_id=0,
        controller_id=0,
        summoning_sick=False,
        chosen_values={
            "creature_type": "Druid",
        },
    )

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(roaming_throne)

    with pytest.raises(
        ValueError,
        match="additional_trigger_count must be an integer",
    ):
        TriggerEngine().count_triggers(
            source=source,
            ability=get_triggered_ability(source),
            battlefield=battlefield,
        )


def test_rejects_negative_additional_trigger_count() -> None:
    source = create_triggered_creature()
    roaming_throne = create_roaming_throne(
        additional_trigger_count=-1,
    )

    battlefield: Zone[Permanent] = Zone()
    battlefield.add(source)
    battlefield.add(roaming_throne)

    with pytest.raises(
        ValueError,
        match=(
            "additional_trigger_count must not be negative"
        ),
    ):
        TriggerEngine().count_triggers(
            source=source,
            ability=get_triggered_ability(source),
            battlefield=battlefield,
        )