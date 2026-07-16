from __future__ import annotations

from types import MappingProxyType

import pytest

from krs.abilities.mana_ability import ManaAbility
from krs.ai.mana_permanent_cast_plan_factory import (
    ManaPermanentCastPlanFactory,
)
from krs.cards.card import Card
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player
from krs.mana.mana import Mana


def mana_ability(
    produced_mana: dict[Mana, int],
) -> ManaAbility:
    return ManaAbility(
        produced_mana=MappingProxyType(
            produced_mana
        ),
        requires_tap=True,
    )


def create_card(
    *,
    card_id: str,
    name: str,
    mana_cost: str,
    type_line: str,
    mana_abilities: tuple[ManaAbility, ...] = (),
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost=mana_cost,
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
    hand: tuple[Card, ...] = (),
    battlefield: tuple[Permanent, ...] = (),
) -> GameState:
    player = Player(
        player_id=0,
    )

    for card in hand:
        player.hand.add(card)

    for permanent in battlefield:
        player.battlefield.add(permanent)

    return GameState(
        players=[player],
        started=True,
        phase=Phase.MAIN,
        turn_number=2,
    )


def forest(
    permanent_id: int,
) -> Permanent:
    return create_permanent(
        permanent_id=permanent_id,
        card=create_card(
            card_id=f"forest-{permanent_id}",
            name="Forest",
            mana_cost="",
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
            mana_cost="",
            type_line="Basic Land — Island",
        ),
    )


def sol_ring() -> Card:
    return create_card(
        card_id="sol-ring-id",
        name="Sol Ring",
        mana_cost="{1}",
        type_line="Artifact",
        mana_abilities=(
            mana_ability(
                {
                    Mana.COLORLESS: 2,
                }
            ),
        ),
    )


def birds_of_paradise() -> Card:
    return create_card(
        card_id="birds-id",
        name="Birds of Paradise",
        mana_cost="{G}",
        type_line="Creature — Bird",
        mana_abilities=(
            mana_ability(
                {
                    Mana.WHITE: 1,
                    Mana.BLUE: 1,
                    Mana.BLACK: 1,
                    Mana.RED: 1,
                    Mana.GREEN: 1,
                }
            ),
        ),
    )


def arcane_signet() -> Card:
    return create_card(
        card_id="arcane-signet-id",
        name="Arcane Signet",
        mana_cost="{2}",
        type_line="Artifact",
        mana_abilities=(
            mana_ability(
                {
                    Mana.BLUE: 1,
                    Mana.GREEN: 1,
                }
            ),
        ),
    )


def test_factory_creates_sol_ring_cast_plan() -> None:
    card = sol_ring()
    state = create_state(
        hand=(card,),
        battlefield=(
            forest(1),
        ),
    )

    plan = ManaPermanentCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert len(plan.mana_actions) == 1
    assert plan.mana_actions[0].permanent.permanent_id == 1
    assert plan.mana_actions[0].mana is Mana.GREEN
    assert plan.cast_action.card is card
    assert plan.cast_action.cost.generic == 1


def test_factory_uses_floating_mana() -> None:
    card = sol_ring()
    state = create_state(
        hand=(card,),
    )
    state.players[0].mana_pool.add(
        Mana.COLORLESS,
    )

    plan = ManaPermanentCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert plan.mana_actions == ()
    assert plan.cast_action.card is card


def test_factory_prioritizes_higher_mana_output() -> None:
    ring = sol_ring()
    birds = birds_of_paradise()

    state = create_state(
        hand=(
            birds,
            ring,
        ),
        battlefield=(
            forest(1),
        ),
    )

    plan = ManaPermanentCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert plan.cast_action.card is ring


def test_factory_casts_birds_when_only_birds_is_payable() -> None:
    birds = birds_of_paradise()
    signet = arcane_signet()

    state = create_state(
        hand=(
            signet,
            birds,
        ),
        battlefield=(
            forest(1),
        ),
    )

    plan = ManaPermanentCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert plan.cast_action.card is birds
    assert plan.cast_action.cost.green == 1


def test_factory_uses_two_lands_for_arcane_signet() -> None:
    signet = arcane_signet()

    state = create_state(
        hand=(signet,),
        battlefield=(
            forest(1),
            island(2),
        ),
    )

    plan = ManaPermanentCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert len(plan.mana_actions) == 2
    assert plan.cast_action.card is signet
    assert plan.cast_action.cost.generic == 2


def test_factory_returns_none_without_mana_permanent() -> None:
    card = create_card(
        card_id="ornithopter-id",
        name="Ornithopter",
        mana_cost="{0}",
        type_line="Artifact Creature — Thopter",
    )

    state = create_state(
        hand=(card,),
    )

    plan = ManaPermanentCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is None


def test_factory_ignores_land_in_hand() -> None:
    configured_land = create_card(
        card_id="command-tower-id",
        name="Command Tower",
        mana_cost="",
        type_line="Land",
        mana_abilities=(
            mana_ability(
                {
                    Mana.BLUE: 1,
                    Mana.GREEN: 1,
                }
            ),
        ),
    )

    state = create_state(
        hand=(configured_land,),
    )

    plan = ManaPermanentCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is None


@pytest.mark.parametrize(
    "mana_cost",
    (
        "{X}",
        "{G/U}",
        "{G/P}",
    ),
)
def test_factory_ignores_unsupported_mana_cost(
    mana_cost: str,
) -> None:
    card = create_card(
        card_id="unsupported-id",
        name="Unsupported Mana Rock",
        mana_cost=mana_cost,
        type_line="Artifact",
        mana_abilities=(
            mana_ability(
                {
                    Mana.COLORLESS: 2,
                }
            ),
        ),
    )

    state = create_state(
        hand=(card,),
        battlefield=(
            forest(1),
            island(2),
        ),
    )

    plan = ManaPermanentCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is None


def test_factory_ignores_tapped_source() -> None:
    tapped_forest = forest(1)
    tapped_forest.tapped = True

    state = create_state(
        hand=(
            sol_ring(),
        ),
        battlefield=(
            tapped_forest,
        ),
    )

    plan = ManaPermanentCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is None


def test_factory_ignores_summoning_sick_mana_creature() -> None:
    source = create_permanent(
        permanent_id=1,
        card=birds_of_paradise(),
        summoning_sick=True,
    )

    state = create_state(
        hand=(
            sol_ring(),
        ),
        battlefield=(
            source,
        ),
    )

    plan = ManaPermanentCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is None


def test_factory_does_not_modify_state() -> None:
    card = sol_ring()
    source = forest(1)

    state = create_state(
        hand=(card,),
        battlefield=(source,),
    )

    player = state.players[0]
    original_action_count = state.action_count
    original_pool_total = player.mana_pool.total()

    plan = ManaPermanentCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert source.tapped is False
    assert tuple(player.hand) == (card,)
    assert player.mana_pool.total() == original_pool_total
    assert state.action_count == original_action_count


def test_factory_rejects_unknown_player() -> None:
    state = create_state()

    with pytest.raises(
        ValueError,
        match="Player not found: 99",
    ):
        ManaPermanentCastPlanFactory().create(
            state=state,
            player_id=99,
        )

def test_candidate_output_treats_colors_as_alternatives() -> None:
    ring = sol_ring()
    birds = birds_of_paradise()

    state = create_state(
        hand=(
            birds,
            ring,
        ),
        battlefield=(
            forest(1),
        ),
    )

    plan = ManaPermanentCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert plan.cast_action.card is ring

def gilded_lotus() -> Card:
    return create_card(
        card_id="gilded-lotus-id",
        name="Gilded Lotus",
        mana_cost="{5}",
        type_line="Artifact",
        mana_abilities=(
            mana_ability(
                {
                    Mana.WHITE: 3,
                    Mana.BLUE: 3,
                    Mana.BLACK: 3,
                    Mana.RED: 3,
                    Mana.GREEN: 3,
                }
            ),
        ),
    )

def test_color_selection_ability_uses_maximum_single_output() -> None:
    lotus = gilded_lotus()
    ring = sol_ring()

    state = create_state(
        hand=(
            ring,
            lotus,
        ),
    )

    player = state.players[0]
    player.mana_pool.add(
        Mana.COLORLESS,
        5,
    )

    plan = ManaPermanentCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert plan.cast_action.card is lotus

def roaming_throne() -> Card:
    return create_card(
        card_id="roaming-throne-id",
        name="Roaming Throne",
        mana_cost="{4}",
        type_line="Artifact Creature — Golem",
        mana_abilities=(
            mana_ability(
                {
                    Mana.COLORLESS: 1,
                }
            ),
        ),
    )

def test_roaming_throne_cast_plan_chooses_druid() -> None:
    card = roaming_throne()

    state = create_state(
        hand=(card,),
    )

    player = state.players[0]
    player.mana_pool.add(
        Mana.COLORLESS,
        4,
    )

    plan = ManaPermanentCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert plan.cast_action.card is card
    assert plan.cast_action.chosen_values == {
        "creature_type": "Druid",
    }

def test_regular_mana_permanent_has_no_chosen_values() -> None:
    card = sol_ring()

    state = create_state(
        hand=(card,),
    )

    state.players[0].mana_pool.add(
        Mana.COLORLESS,
    )

    plan = ManaPermanentCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None
    assert plan.cast_action.card is card
    assert plan.cast_action.chosen_values == {}

def test_cast_plan_chosen_values_are_immutable() -> None:
    card = roaming_throne()

    state = create_state(
        hand=(card,),
    )

    state.players[0].mana_pool.add(
        Mana.COLORLESS,
        4,
    )

    plan = ManaPermanentCastPlanFactory().create(
        state=state,
        player_id=0,
    )

    assert plan is not None

    with pytest.raises(
        TypeError,
    ):
        plan.cast_action.chosen_values[
            "creature_type"
        ] = "Wizard"  # type: ignore[index]