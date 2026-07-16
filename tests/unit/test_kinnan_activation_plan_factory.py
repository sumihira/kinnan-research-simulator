from __future__ import annotations

from types import MappingProxyType

import pytest

from krs.abilities.mana_ability import ManaAbility
from krs.ai.kinnan_activation_plan_factory import (
    KinnanActivationPlanFactory,
)
from krs.cards.card import Card
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player
from krs.mana.mana import Mana


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


def create_kinnan_permanent() -> Permanent:
    return Permanent(
        permanent_id=1,
        card=Card(
            id="kinnan-id",
            name="Kinnan, Bonder Prodigy",
            mana_cost="{G}{U}",
            mana_value=2,
            oracle_text="",
            type_line=(
                "Legendary Creature — Human Druid"
            ),
            power="2",
            toughness="2",
        ),
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
        entered_turn=2,
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


def mana_ability(
    produced_mana: dict[Mana, int],
) -> ManaAbility:
    return ManaAbility(
        produced_mana=MappingProxyType(
            produced_mana
        ),
        requires_tap=True,
    )


def create_state(
    *,
    sources: tuple[Permanent, ...] = (),
    include_kinnan: bool = True,
) -> GameState:
    player = Player(
        player_id=0,
    )

    if include_kinnan:
        player.battlefield.add(
            create_kinnan_permanent()
        )

    for source in sources:
        player.battlefield.add(source)

    return GameState(
        players=[player],
        started=True,
        phase=Phase.MAIN,
        turn_number=2,
    )


def basic_land(
    permanent_id: int,
    *,
    name: str,
    subtype: str,
) -> Permanent:
    return create_permanent(
        permanent_id=permanent_id,
        card=create_card(
            card_id=f"{name}-{permanent_id}",
            name=name,
            type_line=f"Basic Land — {subtype}",
        ),
    )


def mana_rock(
    permanent_id: int,
    *,
    name: str,
    mana: Mana,
    amount: int,
) -> Permanent:
    return create_permanent(
        permanent_id=permanent_id,
        card=create_card(
            card_id=f"{name}-{permanent_id}",
            name=name,
            type_line="Artifact",
            mana_abilities=(
                mana_ability(
                    {
                        mana: amount,
                    }
                ),
            ),
        ),
    )


def test_factory_creates_activation_payment_plan() -> None:
    state = create_state(
        sources=(
            basic_land(
                2,
                name="Forest",
                subtype="Forest",
            ),
            basic_land(
                3,
                name="Island",
                subtype="Island",
            ),
            mana_rock(
                4,
                name="Sol Ring",
                mana=Mana.COLORLESS,
                amount=2,
            ),
            mana_rock(
                5,
                name="Thran Dynamo",
                mana=Mana.COLORLESS,
                amount=3,
            ),
        )
    )

    plan = KinnanActivationPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert plan.source_permanent_id == 1

    selected_ids = {
        action.permanent.permanent_id
        for action in plan.mana_actions
    }

    assert selected_ids == {
        2,
        3,
        4,
        5,
    }

    selected_mana = {
        action.permanent.permanent_id: action.mana
        for action in plan.mana_actions
    }

    assert selected_mana[2] is Mana.GREEN
    assert selected_mana[3] is Mana.BLUE
    assert selected_mana[4] is Mana.COLORLESS
    assert selected_mana[5] is Mana.COLORLESS


def test_factory_counts_kinnan_nonland_bonus() -> None:
    state = create_state(
        sources=(
            basic_land(
                2,
                name="Forest",
                subtype="Forest",
            ),
            basic_land(
                3,
                name="Island",
                subtype="Island",
            ),
            mana_rock(
                4,
                name="Sol Ring",
                mana=Mana.COLORLESS,
                amount=2,
            ),
        )
    )

    state.players[0].mana_pool.add(
        Mana.COLORLESS,
        2,
    )

    plan = KinnanActivationPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None

    selected_ids = {
        action.permanent.permanent_id
        for action in plan.mana_actions
    }

    assert selected_ids == {
        2,
        3,
        4,
    }


def test_factory_does_not_apply_bonus_to_land() -> None:
    state = create_state(
        sources=(
            basic_land(
                2,
                name="Forest",
                subtype="Forest",
            ),
            basic_land(
                3,
                name="Island",
                subtype="Island",
            ),
            basic_land(
                4,
                name="Wastes",
                subtype="Wastes",
            ),
            basic_land(
                5,
                name="Wastes",
                subtype="Wastes",
            ),
            basic_land(
                6,
                name="Wastes",
                subtype="Wastes",
            ),
            basic_land(
                7,
                name="Wastes",
                subtype="Wastes",
            ),
        )
    )

    plan = KinnanActivationPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is None


def test_factory_uses_floating_mana() -> None:
    state = create_state(
        sources=(
            basic_land(
                2,
                name="Forest",
                subtype="Forest",
            ),
            basic_land(
                3,
                name="Island",
                subtype="Island",
            ),
        )
    )

    state.players[0].mana_pool.add(
        Mana.COLORLESS,
        5,
    )

    plan = KinnanActivationPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert len(plan.mana_actions) == 2


def test_factory_requires_no_taps_when_pool_can_pay() -> None:
    state = create_state()
    player = state.players[0]

    player.mana_pool.add(
        Mana.GREEN
    )
    player.mana_pool.add(
        Mana.BLUE
    )
    player.mana_pool.add(
        Mana.COLORLESS,
        5,
    )

    plan = KinnanActivationPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert plan.mana_actions == ()


def test_factory_ignores_tapped_source() -> None:
    sol_ring = mana_rock(
        4,
        name="Sol Ring",
        mana=Mana.COLORLESS,
        amount=2,
    )
    sol_ring.tapped = True

    state = create_state(
        sources=(
            basic_land(
                2,
                name="Forest",
                subtype="Forest",
            ),
            basic_land(
                3,
                name="Island",
                subtype="Island",
            ),
            sol_ring,
        )
    )

    state.players[0].mana_pool.add(
        Mana.COLORLESS,
        2,
    )

    plan = KinnanActivationPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is None


def test_factory_ignores_summoning_sick_mana_creature() -> None:
    mana_creature = create_permanent(
        permanent_id=4,
        card=create_card(
            card_id="birds-id",
            name="Birds of Paradise",
            type_line="Creature — Bird",
            mana_abilities=(
                mana_ability(
                    {
                        Mana.GREEN: 1,
                        Mana.BLUE: 1,
                    }
                ),
            ),
        ),
        summoning_sick=True,
    )

    state = create_state(
        sources=(
            mana_creature,
        )
    )

    state.players[0].mana_pool.add(
        Mana.COLORLESS,
        5,
    )
    state.players[0].mana_pool.add(
        Mana.BLUE,
    )

    plan = KinnanActivationPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is None


def test_factory_returns_none_without_kinnan() -> None:
    state = create_state(
        include_kinnan=False,
    )

    plan = KinnanActivationPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is None


def test_factory_does_not_modify_state() -> None:
    forest = basic_land(
        2,
        name="Forest",
        subtype="Forest",
    )
    island = basic_land(
        3,
        name="Island",
        subtype="Island",
    )

    state = create_state(
        sources=(
            forest,
            island,
        )
    )

    state.players[0].mana_pool.add(
        Mana.COLORLESS,
        5,
    )

    original_action_count = state.action_count
    original_pool_total = (
        state.players[0].mana_pool.total()
    )

    plan = KinnanActivationPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert forest.tapped is False
    assert island.tapped is False
    assert (
        state.players[0].mana_pool.total()
        == original_pool_total
    )
    assert state.action_count == original_action_count


def test_factory_rejects_unknown_player() -> None:
    state = create_state()

    with pytest.raises(
        ValueError,
        match="Player not found: 99",
    ):
        KinnanActivationPlanFactory().create(
            state=state,
            player_id=99,
        )