from __future__ import annotations

from types import MappingProxyType

from krs.abilities.mana_ability import ManaAbility
from krs.abilities.static import StaticAbility
from krs.actions.tap_permanent import TapPermanentAction
from krs.cards.card import Card
from krs.engine.action_executor import ActionExecutor
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
    static_abilities: tuple[StaticAbility, ...] = (),
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line=type_line,
        mana_abilities=mana_abilities,
        static_abilities=static_abilities,
    )


def create_permanent(
    *,
    permanent_id: int,
    card: Card,
) -> Permanent:
    return Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=0,
        controller_id=0,
        summoning_sick=False,
    )


def create_state(
    *,
    permanents: tuple[Permanent, ...],
) -> GameState:
    player = Player(
        player_id=0,
    )

    for permanent in permanents:
        player.battlefield.add(permanent)

    return GameState(
        players=[player],
        started=True,
        phase=Phase.MAIN,
        turn_number=2,
    )


def create_nyxbloom(
    permanent_id: int,
) -> Permanent:
    return create_permanent(
        permanent_id=permanent_id,
        card=create_card(
            card_id="nyxbloom-id",
            name="Nyxbloom Ancient",
            type_line=(
                "Enchantment Creature — Elemental"
            ),
            static_abilities=(
                StaticAbility(
                    ability_type=(
                        "mana_production_multiplier"
                    ),
                    parameters=MappingProxyType(
                        {
                            "multiplier": 3,
                            "source_filter": {},
                        }
                    ),
                ),
            ),
        ),
    )


def test_nyxbloom_triples_sol_ring_mana() -> None:
    sol_ring = create_permanent(
        permanent_id=1,
        card=create_card(
            card_id="sol-ring-id",
            name="Sol Ring",
            type_line="Artifact",
            mana_abilities=(
                ManaAbility(
                    produced_mana=MappingProxyType(
                        {
                            Mana.COLORLESS: 2,
                        }
                    ),
                    requires_tap=True,
                ),
            ),
        ),
    )
    state = create_state(
        permanents=(
            sol_ring,
            create_nyxbloom(2),
        ),
    )

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=2,
            permanent=sol_ring,
            mana=Mana.COLORLESS,
        ),
    )

    player = state.players[0]

    assert player.mana_pool.count(
        Mana.COLORLESS
    ) == 6
    assert state.mana_generated == 6


def test_nyxbloom_triples_basic_land_mana() -> None:
    forest = create_permanent(
        permanent_id=1,
        card=create_card(
            card_id="forest-id",
            name="Forest",
            type_line="Basic Land — Forest",
        ),
    )
    state = create_state(
        permanents=(
            forest,
            create_nyxbloom(2),
        ),
    )

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=2,
            permanent=forest,
            mana=Mana.GREEN,
        ),
    )

    player = state.players[0]

    assert player.mana_pool.count(
        Mana.GREEN
    ) == 3
    assert state.mana_generated == 3