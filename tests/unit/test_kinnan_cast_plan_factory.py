from __future__ import annotations

from types import MappingProxyType

import pytest

from krs.abilities.mana_ability import ManaAbility
from krs.ai.kinnan_cast_plan_factory import (
    KinnanCastPlanFactory,
)
from krs.cards.card import Card
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player
from krs.mana.mana import Mana


def create_kinnan() -> Card:
    return Card(
        id="kinnan-id",
        name="Kinnan, Bonder Prodigy",
        mana_cost="{G}{U}",
        mana_value=2,
        oracle_text="",
        type_line="Legendary Creature — Human Druid",
        power="2",
        toughness="2",
    )


def create_card(
    *,
    card_id: str,
    name: str,
    type_line: str,
    mana_abilities: tuple[ManaAbility, ...] = (),
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line=type_line,
        mana_abilities=mana_abilities,
    )


def create_permanent(
    *,
    permanent_id: int,
    card: Card,
    tapped: bool = False,
    summoning_sick: bool = False,
) -> Permanent:
    return Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=0,
        controller_id=0,
        tapped=tapped,
        summoning_sick=summoning_sick,
        entered_turn=1,
    )


def create_state(
    *,
    battlefield: tuple[Permanent, ...] = (),
    include_kinnan: bool = True,
    commander_cast_count: int = 0,
) -> GameState:
    player = Player(
        player_id=0,
    )

    if include_kinnan:
        player.command.add(
            create_kinnan()
        )

    player.commander_cast_count = commander_cast_count

    for permanent in battlefield:
        player.battlefield.add(
            permanent
        )

    return GameState(
        players=[player],
        started=True,
        phase=Phase.MAIN,
        turn_number=2,
    )


def mana_ability(
    produced_mana: dict[Mana, int],
) -> ManaAbility:
    return ManaAbility(
        produced_mana=MappingProxyType(
            produced_mana
        ),
        requires_tap=True,
    )


def forest(
    permanent_id: int,
) -> Permanent:
    return create_permanent(
        permanent_id=permanent_id,
        card=create_card(
            card_id=f"forest-{permanent_id}",
            name="Forest",
            type_line="Basic Land — Forest",
        ),
    )


def island(
    permanent_id: int,
) -> Permanent:
    return create_permanent(
        permanent_id=permanent_id,
        card=create_card(
            card_id=f"island-{permanent_id}",
            name="Island",
            type_line="Basic Land — Island",
        ),
    )


def test_factory_creates_green_blue_cast_plan() -> None:
    state = create_state(
        battlefield=(
            forest(1),
            island(2),
        )
    )

    plan = KinnanCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert len(plan.mana_actions) == 2

    assert plan.mana_actions[0].permanent.permanent_id == 1
    assert plan.mana_actions[0].mana is Mana.GREEN

    assert plan.mana_actions[1].permanent.permanent_id == 2
    assert plan.mana_actions[1].mana is Mana.BLUE

    assert plan.cast_action.card.name == (
        "Kinnan, Bonder Prodigy"
    )
    assert plan.cast_action.base_cost.green == 1
    assert plan.cast_action.base_cost.blue == 1


def test_factory_uses_existing_floating_mana() -> None:
    state = create_state(
        battlefield=(
            island(1),
        )
    )
    state.players[0].mana_pool.add(
        Mana.GREEN
    )

    plan = KinnanCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert len(plan.mana_actions) == 1
    assert plan.mana_actions[0].mana is Mana.BLUE


def test_factory_requires_no_taps_when_pool_can_pay() -> None:
    state = create_state()

    player = state.players[0]
    player.mana_pool.add(Mana.GREEN)
    player.mana_pool.add(Mana.BLUE)

    plan = KinnanCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert plan.mana_actions == ()


def test_factory_selects_colors_from_configured_land() -> None:
    command_tower = create_permanent(
        permanent_id=1,
        card=create_card(
            card_id="command-tower",
            name="Command Tower",
            type_line="Land",
            mana_abilities=(
                mana_ability(
                    {
                        Mana.BLUE: 1,
                        Mana.GREEN: 1,
                    }
                ),
            ),
        ),
    )

    state = create_state(
        battlefield=(
            command_tower,
            island(2),
        )
    )

    plan = KinnanCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert len(plan.mana_actions) == 2

    selected = {
        (
            action.permanent.permanent_id,
            action.mana,
        )
        for action in plan.mana_actions
    }

    assert selected == {
        (1, Mana.GREEN),
        (2, Mana.BLUE),
    }


def test_factory_uses_single_multi_mana_source_when_possible() -> None:
    source = create_permanent(
        permanent_id=1,
        card=create_card(
            card_id="special-source",
            name="Special Source",
            type_line="Artifact",
            mana_abilities=(
                mana_ability(
                    {
                        Mana.GREEN: 2,
                    }
                ),
            ),
        ),
    )

    state = create_state(
        battlefield=(
            source,
        )
    )
    state.players[0].mana_pool.add(
        Mana.BLUE
    )

    plan = KinnanCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert len(plan.mana_actions) == 1
    assert plan.mana_actions[0].permanent is source
    assert plan.mana_actions[0].mana is Mana.GREEN


def test_factory_ignores_tapped_sources() -> None:
    tapped_forest = forest(1)
    tapped_forest.tapped = True

    state = create_state(
        battlefield=(
            tapped_forest,
            island(2),
        )
    )

    plan = KinnanCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is None


def test_factory_ignores_summoning_sick_mana_creature() -> None:
    birds = create_permanent(
        permanent_id=1,
        card=create_card(
            card_id="birds",
            name="Birds of Paradise",
            type_line="Creature — Bird",
            mana_abilities=(
                mana_ability(
                    {
                        Mana.BLUE: 1,
                        Mana.GREEN: 1,
                    }
                ),
            ),
        ),
        summoning_sick=True,
    )

    state = create_state(
        battlefield=(
            birds,
            island(2),
        )
    )

    plan = KinnanCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is None


def test_factory_uses_non_summoning_sick_mana_creature() -> None:
    birds = create_permanent(
        permanent_id=1,
        card=create_card(
            card_id="birds",
            name="Birds of Paradise",
            type_line="Creature — Bird",
            mana_abilities=(
                mana_ability(
                    {
                        Mana.BLUE: 1,
                        Mana.GREEN: 1,
                    }
                ),
            ),
        ),
        summoning_sick=False,
    )

    state = create_state(
        battlefield=(
            birds,
            island(2),
        )
    )

    plan = KinnanCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert len(plan.mana_actions) == 2


def test_factory_returns_none_without_kinnan_in_command_zone() -> None:
    state = create_state(
        battlefield=(
            forest(1),
            island(2),
        ),
        include_kinnan=False,
    )

    plan = KinnanCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is None


def test_factory_returns_none_when_colors_are_insufficient() -> None:
    state = create_state(
        battlefield=(
            forest(1),
            forest(2),
        )
    )

    plan = KinnanCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is None


def test_factory_accounts_for_commander_tax() -> None:
    colorless_source = create_permanent(
        permanent_id=3,
        card=create_card(
            card_id="sol-ring",
            name="Sol Ring",
            type_line="Artifact",
            mana_abilities=(
                mana_ability(
                    {
                        Mana.COLORLESS: 2,
                    }
                ),
            ),
        ),
    )

    state = create_state(
        battlefield=(
            forest(1),
            island(2),
            colorless_source,
        ),
        commander_cast_count=1,
    )

    plan = KinnanCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert len(plan.mana_actions) == 3


def test_factory_rejects_unpayable_commander_tax() -> None:
    state = create_state(
        battlefield=(
            forest(1),
            island(2),
        ),
        commander_cast_count=1,
    )

    plan = KinnanCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is None


def test_factory_prefers_minimum_number_of_taps() -> None:
    sol_ring = create_permanent(
        permanent_id=3,
        card=create_card(
            card_id="sol-ring",
            name="Sol Ring",
            type_line="Artifact",
            mana_abilities=(
                mana_ability(
                    {
                        Mana.COLORLESS: 2,
                    }
                ),
            ),
        ),
    )

    state = create_state(
        battlefield=(
            forest(1),
            island(2),
            sol_ring,
        )
    )

    plan = KinnanCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert len(plan.mana_actions) == 2

    selected_ids = {
        action.permanent.permanent_id
        for action in plan.mana_actions
    }

    assert selected_ids == {
        1,
        2,
    }


def test_factory_does_not_modify_state() -> None:
    state = create_state(
        battlefield=(
            forest(1),
            island(2),
        )
    )
    player = state.players[0]

    original_pool_total = player.mana_pool.total()
    original_action_count = state.action_count

    plan = KinnanCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert all(
        not permanent.tapped
        for permanent in player.battlefield
    )
    assert player.mana_pool.total() == original_pool_total
    assert state.action_count == original_action_count
    assert len(player.command) == 1
    assert len(player.battlefield) == 2


def test_factory_rejects_unknown_player() -> None:
    state = create_state()

    with pytest.raises(
        ValueError,
        match="Player not found: 99",
    ):
        KinnanCastPlanFactory().create(
            state=state,
            player_id=99,
        )