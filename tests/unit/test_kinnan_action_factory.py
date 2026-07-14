from __future__ import annotations

from unittest.mock import Mock

import pytest

from krs.ai.kinnan_action_factory import KinnanActionFactory
from krs.ai.kinnan_hit_selector import KinnanHitSelector
from krs.cards.card import Card
from krs.game.game_state import GameState
from krs.game.phase import Phase
from krs.game.player import Player


def create_card(
    *,
    card_id: str,
    name: str,
    mana_value: int,
    type_line: str,
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=mana_value,
        oracle_text="",
        type_line=type_line,
    )


def create_running_state(
    *,
    turn_number: int = 3,
) -> GameState:
    return GameState(
        players=[
            Player(player_id=0),
        ],
        started=True,
        phase=Phase.MAIN,
        turn_number=turn_number,
    )


def test_creates_action_with_ai_selected_card() -> None:
    state = create_running_state()
    player = state.players[0]

    small_creature = create_card(
        card_id="small-id",
        name="Small Creature",
        mana_value=2,
        type_line="Creature — Beast",
    )
    large_creature = create_card(
        card_id="large-id",
        name="Large Creature",
        mana_value=7,
        type_line="Creature — Whale",
    )
    artifact = create_card(
        card_id="artifact-id",
        name="Artifact",
        mana_value=10,
        type_line="Artifact",
    )

    player.library.cards.extend(
        [
            small_creature,
            large_creature,
            artifact,
        ]
    )

    action = KinnanActionFactory().create(
        state=state,
        player_id=0,
        source_permanent_id=15,
    )

    assert action.player_id == 0
    assert action.turn_number == 3
    assert action.source_permanent_id == 15
    assert action.selected_card_id == large_creature.id


def test_creates_action_without_selection_when_no_hit_exists() -> None:
    state = create_running_state()
    player = state.players[0]

    player.library.cards.extend(
        [
            create_card(
                card_id="artifact-id",
                name="Artifact",
                mana_value=4,
                type_line="Artifact",
            ),
            create_card(
                card_id="human-id",
                name="Human",
                mana_value=6,
                type_line="Creature — Human Wizard",
            ),
        ]
    )

    action = KinnanActionFactory().create(
        state=state,
        player_id=0,
        source_permanent_id=1,
    )

    assert action.selected_card_id is None


def test_only_passes_top_five_cards_to_selector() -> None:
    state = create_running_state()
    player = state.players[0]

    cards = [
        create_card(
            card_id=f"card-{index}",
            name=f"Card {index}",
            mana_value=index,
            type_line="Creature — Beast",
        )
        for index in range(6)
    ]
    player.library.cards.extend(cards)

    hit_selector = Mock(
        spec=KinnanHitSelector,
    )
    hit_selector.select.return_value = cards[1]

    factory = KinnanActionFactory(
        hit_selector=hit_selector,
    )

    action = factory.create(
        state=state,
        player_id=0,
        source_permanent_id=1,
    )

    hit_selector.select.assert_called_once()

    revealed_cards = (
        hit_selector.select.call_args.args[0]
    )

    assert list(revealed_cards) == cards[:5]
    assert cards[5] not in revealed_cards
    assert action.selected_card_id == cards[1].id


def test_uses_all_cards_when_library_has_fewer_than_five() -> None:
    state = create_running_state()
    player = state.players[0]

    cards = [
        create_card(
            card_id=f"card-{index}",
            name=f"Card {index}",
            mana_value=index,
            type_line="Creature — Beast",
        )
        for index in range(3)
    ]
    player.library.cards.extend(cards)

    hit_selector = Mock(
        spec=KinnanHitSelector,
    )
    hit_selector.select.return_value = cards[0]

    factory = KinnanActionFactory(
        hit_selector=hit_selector,
    )

    factory.create(
        state=state,
        player_id=0,
        source_permanent_id=1,
    )

    revealed_cards = (
        hit_selector.select.call_args.args[0]
    )

    assert list(revealed_cards) == cards


def test_empty_library_creates_action_without_selection() -> None:
    state = create_running_state()

    action = KinnanActionFactory().create(
        state=state,
        player_id=0,
        source_permanent_id=1,
    )

    assert action.selected_card_id is None


def test_factory_does_not_modify_library() -> None:
    state = create_running_state()
    player = state.players[0]

    cards = [
        create_card(
            card_id=f"card-{index}",
            name=f"Card {index}",
            mana_value=index,
            type_line="Creature — Beast",
        )
        for index in range(5)
    ]
    player.library.cards.extend(cards)

    original_library = list(player.library)

    KinnanActionFactory().create(
        state=state,
        player_id=0,
        source_permanent_id=1,
    )

    assert list(player.library) == original_library


def test_uses_current_turn_number() -> None:
    state = create_running_state(
        turn_number=8,
    )

    action = KinnanActionFactory().create(
        state=state,
        player_id=0,
        source_permanent_id=4,
    )

    assert action.turn_number == 8


def test_rejects_unknown_player() -> None:
    state = create_running_state()

    with pytest.raises(
        ValueError,
        match="Player not found: 99",
    ):
        KinnanActionFactory().create(
            state=state,
            player_id=99,
            source_permanent_id=1,
        )