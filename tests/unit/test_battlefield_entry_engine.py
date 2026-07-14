from __future__ import annotations

from unittest.mock import Mock, call

from krs.cards.card import Card
from krs.engine.battlefield_entry_engine import (
    BattlefieldEntryEngine,
)
from krs.engine.etb_ability_engine import EtbAbilityEngine
from krs.engine.replacement_ability_engine import (
    ReplacementAbilityEngine,
)
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.player import Player


def create_fixture() -> tuple[
    GameState,
    Player,
    Permanent,
]:
    player = Player(player_id=0)
    state = GameState(
        players=[player],
        started=True,
        turn_number=1,
        next_permanent_id=2,
    )
    card = Card(
        id="entry-card-id",
        name="Entry Permanent",
        mana_cost="{2}",
        mana_value=2,
        oracle_text="",
        type_line="Creature — Beast",
        power="2",
        toughness="2",
    )
    permanent = Permanent(
        permanent_id=1,
        card=card,
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
        entered_turn=1,
    )

    return state, player, permanent


def test_validate_applies_replacement_and_validates_etb() -> None:
    replacement_engine = Mock(
        spec=ReplacementAbilityEngine,
    )
    etb_engine = Mock(
        spec=EtbAbilityEngine,
    )
    state, player, permanent = create_fixture()

    engine = BattlefieldEntryEngine(
        replacement_ability_engine=replacement_engine,
        etb_ability_engine=etb_engine,
    )

    engine.validate(
        permanent=permanent,
        controller=player,
        chosen_values={
            "creature_type": "Druid",
        },
    )

    replacement_engine.apply_enters_battlefield_replacements.assert_called_once_with(
        permanent=permanent,
        chosen_values={
            "creature_type": "Druid",
        },
    )
    etb_engine.validate.assert_called_once_with(
        permanent=permanent,
        controller=player,
    )

    assert permanent not in player.battlefield
    assert state.next_permanent_id == 2


def test_enter_adds_permanent_and_executes_etb() -> None:
    replacement_engine = Mock(
        spec=ReplacementAbilityEngine,
    )
    etb_engine = Mock(
        spec=EtbAbilityEngine,
    )
    state, player, permanent = create_fixture()

    engine = BattlefieldEntryEngine(
        replacement_ability_engine=replacement_engine,
        etb_ability_engine=etb_engine,
    )

    engine.enter(
        state=state,
        controller=player,
        permanent=permanent,
    )

    assert permanent in player.battlefield
    etb_engine.execute.assert_called_once_with(
        permanent=permanent,
        controller=player,
    )
    assert state.next_permanent_id == 3


def test_enter_does_not_repeat_replacement_validation() -> None:
    replacement_engine = Mock(
        spec=ReplacementAbilityEngine,
    )
    etb_engine = Mock(
        spec=EtbAbilityEngine,
    )
    state, player, permanent = create_fixture()

    engine = BattlefieldEntryEngine(
        replacement_ability_engine=replacement_engine,
        etb_ability_engine=etb_engine,
    )

    engine.validate(
        permanent=permanent,
        controller=player,
    )
    engine.enter(
        state=state,
        controller=player,
        permanent=permanent,
    )

    replacement_engine.apply_enters_battlefield_replacements.assert_called_once()
    etb_engine.validate.assert_called_once()
    etb_engine.execute.assert_called_once()