from __future__ import annotations

import pytest

from krs.actions.activate_kinnan import ActivateKinnanAction
from krs.cards.card import Card
from krs.engine.kinnan_resolution_engine import (
    KinnanResolutionEngine,
)
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player
from krs.mana.mana import Mana
from unittest.mock import Mock

from krs.engine.battlefield_entry_engine import (
    BattlefieldEntryEngine,
)


def create_card(
    *,
    card_id: str,
    name: str,
    type_line: str,
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line=type_line,
    )


def create_running_state() -> GameState:
    player = Player(player_id=0)

    kinnan = Permanent(
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
        entered_turn=1,
    )
    player.battlefield.add(kinnan)

    player.mana_pool.add(
        Mana.COLORLESS,
        5,
    )
    player.mana_pool.add(
        Mana.GREEN,
    )
    player.mana_pool.add(
        Mana.BLUE,
    )

    return GameState(
        players=[player],
        started=True,
        phase=Phase.MAIN,
        turn_number=1,
        next_permanent_id=2,
    )


def test_kinnan_resolution_puts_selected_hit_onto_battlefield() -> None:
    state = create_running_state()
    player = state.players[0]

    hit = create_card(
        card_id="hit-id",
        name="Non-Human Creature",
        type_line="Creature — Beast",
    )
    miss = create_card(
        card_id="miss-id",
        name="Human Creature",
        type_line="Creature — Human",
    )

    player.library.cards.extend(
        [
            hit,
            miss,
        ]
    )

    KinnanResolutionEngine().execute(
        state=state,
        action=ActivateKinnanAction(
            player_id=0,
            turn_number=1,
            source_permanent_id=1,
            selected_card_id=hit.id,
        ),
    )

    battlefield_cards = [
        permanent.effective_card
        for permanent in player.battlefield
    ]

    assert hit in battlefield_cards
    assert miss in player.library
    assert player.mana_pool.total() == 0
    assert state.mana_spent == 7
    assert state.action_count == 1
    assert state.next_permanent_id == 3


def test_kinnan_resolution_rejects_insufficient_mana() -> None:
    state = create_running_state()
    player = state.players[0]
    player.mana_pool.clear()

    with pytest.raises(
        ValueError,
        match="Kinnan activation cost cannot be paid",
    ):
        KinnanResolutionEngine().execute(
            state=state,
            action=ActivateKinnanAction(
                player_id=0,
                turn_number=1,
                source_permanent_id=1,
                selected_card_id=None,
            ),
        )

    assert state.mana_spent == 0
    assert state.action_count == 0
    assert len(player.battlefield) == 1


def test_kinnan_resolution_rejects_non_kinnan_source() -> None:
    state = create_running_state()
    player = state.players[0]
    player.battlefield.clear()

    source = Permanent(
        permanent_id=1,
        card=create_card(
            card_id="other-id",
            name="Other Creature",
            type_line="Creature — Druid",
        ),
        owner_id=0,
        controller_id=0,
    )
    player.battlefield.add(source)

    with pytest.raises(
        ValueError,
        match="Source permanent is not Kinnan",
    ):
        KinnanResolutionEngine().execute(
            state=state,
            action=ActivateKinnanAction(
                player_id=0,
                turn_number=1,
                source_permanent_id=1,
                selected_card_id=None,
            ),
        )

    assert player.mana_pool.total() == 7
    assert state.action_count == 0

def test_kinnan_hit_uses_battlefield_entry_engine() -> None:
    state = create_running_state()
    player = state.players[0]

    selected_card = create_card(
        card_id="selected-id",
        name="Selected Creature",
        type_line="Creature — Beast",
    )
    player.library.cards.append(selected_card)

    battlefield_entry_engine = Mock(
        spec=BattlefieldEntryEngine,
    )
    engine = KinnanResolutionEngine(
        battlefield_entry_engine=battlefield_entry_engine,
    )

    engine.execute(
        state=state,
        action=ActivateKinnanAction(
            player_id=0,
            turn_number=1,
            source_permanent_id=1,
            selected_card_id=selected_card.id,
        ),
    )

    battlefield_entry_engine.validate.assert_called_once()

    validate_arguments = (
        battlefield_entry_engine
        .validate
        .call_args
        .kwargs
    )
    validated_permanent = validate_arguments["permanent"]

    assert validated_permanent.effective_card is selected_card
    assert validate_arguments["controller"] is player

    battlefield_entry_engine.enter.assert_called_once_with(
        state=state,
        controller=player,
        permanent=validated_permanent,
    )


def test_kinnan_miss_does_not_use_battlefield_entry_engine() -> None:
    state = create_running_state()

    battlefield_entry_engine = Mock(
        spec=BattlefieldEntryEngine,
    )
    engine = KinnanResolutionEngine(
        battlefield_entry_engine=battlefield_entry_engine,
    )

    engine.execute(
        state=state,
        action=ActivateKinnanAction(
            player_id=0,
            turn_number=1,
            source_permanent_id=1,
            selected_card_id=None,
        ),
    )

    battlefield_entry_engine.validate.assert_not_called()
    battlefield_entry_engine.enter.assert_not_called()


def test_kinnan_entry_validation_failure_preserves_state() -> None:
    state = create_running_state()
    player = state.players[0]

    selected_card = create_card(
        card_id="selected-id",
        name="Selected Creature",
        type_line="Creature — Beast",
    )
    player.library.cards.append(selected_card)

    battlefield_entry_engine = Mock(
        spec=BattlefieldEntryEngine,
    )
    battlefield_entry_engine.validate.side_effect = ValueError(
        "Entry validation failed."
    )

    engine = KinnanResolutionEngine(
        battlefield_entry_engine=battlefield_entry_engine,
    )

    original_mana = player.mana_pool.total()
    original_library = list(player.library)
    original_battlefield = list(player.battlefield)
    original_next_permanent_id = state.next_permanent_id

    with pytest.raises(
        ValueError,
        match="Entry validation failed",
    ):
        engine.execute(
            state=state,
            action=ActivateKinnanAction(
                player_id=0,
                turn_number=1,
                source_permanent_id=1,
                selected_card_id=selected_card.id,
            ),
        )

    assert player.mana_pool.total() == original_mana
    assert list(player.library) == original_library
    assert list(player.battlefield) == original_battlefield
    assert state.next_permanent_id == original_next_permanent_id
    assert state.mana_spent == 0
    assert state.action_count == 0