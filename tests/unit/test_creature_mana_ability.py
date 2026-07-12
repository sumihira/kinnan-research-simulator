import pytest

from krs.abilities.mana_ability import ManaAbility
from krs.actions.tap_permanent import TapPermanentAction
from krs.cards.card import Card
from krs.engine.action_executor import ActionExecutor
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player
from krs.mana.mana import Mana
from krs.abilities.static import StaticAbility

def create_running_state() -> GameState:
    return GameState(
        players=[Player(player_id=0)],
        started=True,
        phase=Phase.MAIN,
        turn_number=1,
    )


def create_mana_creature(
    *,
    permanent_id: int = 1,
    name: str = "Llanowar Elves",
    summoning_sick: bool = True,
    keywords: tuple[str, ...] = (),
    can_activate_as_though_haste: bool = False,
) -> Permanent:
    card = Card(
        id=f"{name.lower().replace(' ', '-')}-id",
        name=name,
        mana_cost="{G}",
        mana_value=1,
        oracle_text="{T}: Add {G}.",
        type_line="Creature — Elf Druid",
        power="1",
        toughness="1",
        mana_abilities=(
            ManaAbility(
                produced_mana={
                    Mana.GREEN: 1,
                }
            ),
        ),
        keywords=keywords,
    )

    return Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=0,
        controller_id=0,
        summoning_sick=summoning_sick,
        entered_turn=1,
        can_activate_tap_abilities_as_though_haste=(
            can_activate_as_though_haste
        ),
    )
def create_kinnan() -> Permanent:
    card = Card(
        id="kinnan-id",
        name="Kinnan, Bonder Prodigy",
        mana_cost="{G}{U}",
        mana_value=2,
        oracle_text="",
        type_line="Legendary Creature — Human Druid",
        power="2",
        toughness="2",
        static_abilities=(
            StaticAbility(
                ability_type="additional_nonland_mana",
                parameters={
                    "source_filter": {
                        "permanent_type": "nonland",
                    },
                    "additional_amount": 1,
                    "mana_selection": "produced_type",
                },
            ),
        ),
    )

    return Permanent(
        permanent_id=10,
        card=card,
        owner_id=0,
        controller_id=0,
        entered_turn=1,
    )


def test_mana_creature_gets_kinnan_bonus_after_sickness_ends() -> None:
    state = create_running_state()
    player = state.players[0]

    player.battlefield.add(create_kinnan())

    llanowar_elves = create_mana_creature(
        summoning_sick=False,
    )
    player.battlefield.add(llanowar_elves)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=llanowar_elves,
            mana=Mana.GREEN,
        ),
    )

    assert player.mana_pool.count(Mana.GREEN) == 2
    assert state.mana_generated == 2


def test_summoning_sickness_prevents_mana_and_kinnan_bonus() -> None:
    state = create_running_state()
    player = state.players[0]

    player.battlefield.add(create_kinnan())

    llanowar_elves = create_mana_creature(
        summoning_sick=True,
    )
    player.battlefield.add(llanowar_elves)

    with pytest.raises(
        ValueError,
        match="Summoning-sick creature",
    ):
        ActionExecutor().execute(
            state,
            TapPermanentAction(
                player_id=0,
                turn_number=1,
                permanent=llanowar_elves,
                mana=Mana.GREEN,
            ),
        )

    assert player.mana_pool.total() == 0
    assert state.mana_generated == 0

def test_summoning_sick_mana_creature_cannot_be_tapped() -> None:
    state = create_running_state()
    player = state.players[0]

    llanowar_elves = create_mana_creature(
        summoning_sick=True,
    )
    player.battlefield.add(llanowar_elves)

    with pytest.raises(
        ValueError,
        match=(
            "Summoning-sick creature cannot activate "
            "a tap ability: Llanowar Elves"
        ),
    ):
        ActionExecutor().execute(
            state,
            TapPermanentAction(
                player_id=0,
                turn_number=1,
                permanent=llanowar_elves,
                mana=Mana.GREEN,
            ),
        )

    assert llanowar_elves.tapped is False
    assert player.mana_pool.total() == 0
    assert state.mana_generated == 0
    assert state.action_count == 0


def test_mana_creature_can_be_tapped_after_summoning_sickness_ends() -> None:
    state = create_running_state()
    player = state.players[0]

    llanowar_elves = create_mana_creature(
        summoning_sick=False,
    )
    player.battlefield.add(llanowar_elves)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=llanowar_elves,
            mana=Mana.GREEN,
        ),
    )

    assert llanowar_elves.tapped is True
    assert player.mana_pool.count(Mana.GREEN) == 1
    assert state.mana_generated == 1
    assert state.action_count == 1


def test_haste_allows_new_mana_creature_to_be_tapped() -> None:
    state = create_running_state()
    player = state.players[0]

    hasty_creature = create_mana_creature(
        name="Hasty Mana Dork",
        summoning_sick=True,
        keywords=("Haste",),
    )
    player.battlefield.add(hasty_creature)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=hasty_creature,
            mana=Mana.GREEN,
        ),
    )

    assert hasty_creature.tapped is True
    assert player.mana_pool.count(Mana.GREEN) == 1


def test_as_though_haste_allows_new_mana_creature_to_be_tapped() -> None:
    state = create_running_state()
    player = state.players[0]

    mana_creature = create_mana_creature(
        summoning_sick=True,
        can_activate_as_though_haste=True,
    )
    player.battlefield.add(mana_creature)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=mana_creature,
            mana=Mana.GREEN,
        ),
    )

    assert mana_creature.tapped is True
    assert player.mana_pool.count(Mana.GREEN) == 1


def test_noncreature_mana_source_ignores_summoning_sickness() -> None:
    state = create_running_state()
    player = state.players[0]

    card = Card(
        id="sol-ring-id",
        name="Sol Ring",
        mana_cost="{1}",
        mana_value=1,
        oracle_text="{T}: Add {C}{C}.",
        type_line="Artifact",
        mana_abilities=(
            ManaAbility(
                produced_mana={
                    Mana.COLORLESS: 2,
                }
            ),
        ),
    )

    sol_ring = Permanent(
        permanent_id=1,
        card=card,
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
        entered_turn=1,
    )
    player.battlefield.add(sol_ring)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=sol_ring,
            mana=Mana.COLORLESS,
        ),
    )

    assert sol_ring.tapped is True
    assert player.mana_pool.count(Mana.COLORLESS) == 2