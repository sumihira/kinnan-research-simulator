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


def create_running_state() -> GameState:
    return GameState(
        players=[Player(player_id=0)],
        started=True,
        phase=Phase.MAIN,
        turn_number=1,
    )


def create_mana_permanent(
    *,
    permanent_id: int = 1,
    name: str = "Sol Ring",
    produced_mana: dict[Mana, int] | None = None,
    tapped: bool = False,
) -> Permanent:
    ability = ManaAbility(
        produced_mana=produced_mana
        or {
            Mana.COLORLESS: 2,
        }
    )

    card = Card(
        id=f"{name.lower().replace(' ', '-')}-id",
        name=name,
        mana_cost="{1}",
        mana_value=1,
        oracle_text="{T}: Add {C}{C}.",
        type_line="Artifact",
        mana_abilities=(ability,),
    )

    return Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=0,
        controller_id=0,
        tapped=tapped,
        summoning_sick=False,
        entered_turn=1,
    )


def test_sol_ring_produces_two_colorless_mana() -> None:
    state = create_running_state()
    player = state.players[0]

    sol_ring = create_mana_permanent()
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
    assert player.mana_pool.total() == 2
    assert state.mana_generated == 2
    assert state.action_count == 1


def test_basalt_monolith_produces_three_colorless_mana() -> None:
    state = create_running_state()
    player = state.players[0]

    basalt = create_mana_permanent(
        name="Basalt Monolith",
        produced_mana={
            Mana.COLORLESS: 3,
        },
    )
    player.battlefield.add(basalt)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=basalt,
            mana=Mana.COLORLESS,
        ),
    )

    assert player.mana_pool.count(Mana.COLORLESS) == 3
    assert state.mana_generated == 3


def test_nonland_mana_source_cannot_be_tapped_twice() -> None:
    state = create_running_state()
    player = state.players[0]

    sol_ring = create_mana_permanent()
    player.battlefield.add(sol_ring)

    executor = ActionExecutor()

    action = TapPermanentAction(
        player_id=0,
        turn_number=1,
        permanent=sol_ring,
        mana=Mana.COLORLESS,
    )

    executor.execute(state, action)

    with pytest.raises(
        ValueError,
        match="Permanent is already tapped: Sol Ring",
    ):
        executor.execute(state, action)

    assert player.mana_pool.total() == 2
    assert state.mana_generated == 2
    assert state.action_count == 1


def test_nonland_without_mana_ability_cannot_be_tapped_for_mana() -> None:
    state = create_running_state()
    player = state.players[0]

    card = Card(
        id="ornithopter-id",
        name="Ornithopter",
        mana_cost="{0}",
        mana_value=0,
        oracle_text="Flying",
        type_line="Artifact Creature — Thopter",
        power="0",
        toughness="2",
    )

    permanent = Permanent(
        permanent_id=1,
        card=card,
        owner_id=0,
        controller_id=0,
        summoning_sick=False,
    )
    player.battlefield.add(permanent)

    with pytest.raises(
        ValueError,
        match="Mana ability not found at index 0",
    ):
        ActionExecutor().execute(
            state,
            TapPermanentAction(
                player_id=0,
                turn_number=1,
                permanent=permanent,
                mana=Mana.COLORLESS,
            ),
        )

    assert permanent.tapped is False
    assert player.mana_pool.total() == 0
    assert state.mana_generated == 0
    assert state.action_count == 0


def test_invalid_mana_ability_index_is_rejected() -> None:
    state = create_running_state()
    player = state.players[0]

    sol_ring = create_mana_permanent()
    player.battlefield.add(sol_ring)

    with pytest.raises(
        ValueError,
        match="Mana ability not found at index 2",
    ):
        ActionExecutor().execute(
            state,
            TapPermanentAction(
                player_id=0,
                turn_number=1,
                permanent=sol_ring,
                mana=Mana.COLORLESS,
                ability_index=2,
            ),
        )

    assert sol_ring.tapped is False
    assert player.mana_pool.total() == 0


def test_wrong_mana_type_is_rejected() -> None:
    state = create_running_state()
    player = state.players[0]

    sol_ring = create_mana_permanent()
    player.battlefield.add(sol_ring)

    with pytest.raises(
        ValueError,
        match="cannot produce selected mana",
    ):
        ActionExecutor().execute(
            state,
            TapPermanentAction(
                player_id=0,
                turn_number=1,
                permanent=sol_ring,
                mana=Mana.BLUE,
            ),
        )

    assert sol_ring.tapped is False
    assert player.mana_pool.total() == 0


def test_multiple_output_types_can_be_selected() -> None:
    state = create_running_state()
    player = state.players[0]

    mana_source = create_mana_permanent(
        name="Test Mana Source",
        produced_mana={
            Mana.BLUE: 1,
            Mana.GREEN: 1,
        },
    )
    player.battlefield.add(mana_source)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=mana_source,
            mana=Mana.GREEN,
        ),
    )

    assert player.mana_pool.count(Mana.GREEN) == 1
    assert player.mana_pool.count(Mana.BLUE) == 0