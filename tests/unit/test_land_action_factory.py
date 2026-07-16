from __future__ import annotations

from pathlib import Path

import pytest

from krs.ai.land_action_factory import LandActionFactory
from krs.cards.card import Card
from krs.cards.card_config_loader import CardConfigLoader
from krs.cards.card_enricher import CardEnricher
from krs.game.game_state import GameState
from krs.game.player import Player


CARD_CONFIG_DIRECTORY = Path("config/cards")


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


def create_enriched_land(
    *,
    card_id: str,
    name: str,
    type_line: str = "Land",
) -> Card:
    return CardEnricher(
        CardConfigLoader(
            CARD_CONFIG_DIRECTORY
        )
    ).enrich(
        create_card(
            card_id=card_id,
            name=name,
            type_line=type_line,
        )
    )


def create_state(
    *,
    cards: tuple[Card, ...] = (),
    land_played_this_turn: int = 0,
) -> GameState:
    player = Player(
        player_id=0,
    )

    for card in cards:
        player.hand.add(card)

    player.land_played_this_turn = (
        land_played_this_turn
    )

    return GameState(
        players=[player],
        started=True,
        turn_number=3,
    )


def test_factory_returns_none_without_land() -> None:
    state = create_state(
        cards=(
            create_card(
                card_id="sol-ring",
                name="Sol Ring",
                type_line="Artifact",
            ),
        )
    )

    action = LandActionFactory().create(
        state=state,
        player_id=0,
    )

    assert action is None


def test_factory_returns_none_after_land_played() -> None:
    state = create_state(
        cards=(
            create_card(
                card_id="forest",
                name="Forest",
                type_line="Basic Land — Forest",
            ),
        ),
        land_played_this_turn=1,
    )

    action = LandActionFactory().create(
        state=state,
        player_id=0,
    )

    assert action is None


def test_factory_creates_land_action() -> None:
    forest = create_card(
        card_id="forest",
        name="Forest",
        type_line="Basic Land — Forest",
    )
    state = create_state(
        cards=(forest,),
    )

    action = LandActionFactory().create(
        state=state,
        player_id=0,
    )

    assert action is not None
    assert action.player_id == 0
    assert action.turn_number == 3
    assert action.card is forest


def test_factory_prioritizes_blue_green_land() -> None:
    forest = create_card(
        card_id="forest",
        name="Forest",
        type_line="Basic Land — Forest",
    )
    island = create_card(
        card_id="island",
        name="Island",
        type_line="Basic Land — Island",
    )
    tropical_island = create_card(
        card_id="tropical-island",
        name="Tropical Island",
        type_line="Land — Forest Island",
    )

    state = create_state(
        cards=(
            forest,
            island,
            tropical_island,
        )
    )

    action = LandActionFactory().create(
        state=state,
        player_id=0,
    )

    assert action is not None
    assert action.card is tropical_island


def test_factory_prioritizes_green_over_blue() -> None:
    island = create_card(
        card_id="island",
        name="Island",
        type_line="Basic Land — Island",
    )
    forest = create_card(
        card_id="forest",
        name="Forest",
        type_line="Basic Land — Forest",
    )

    state = create_state(
        cards=(
            island,
            forest,
        )
    )

    action = LandActionFactory().create(
        state=state,
        player_id=0,
    )

    assert action is not None
    assert action.card is forest


def test_factory_uses_configured_land_mana() -> None:
    ancient_tomb = create_enriched_land(
        card_id="ancient-tomb",
        name="Ancient Tomb",
    )
    command_tower = create_enriched_land(
        card_id="command-tower",
        name="Command Tower",
    )

    state = create_state(
        cards=(
            ancient_tomb,
            command_tower,
        )
    )

    action = LandActionFactory().create(
        state=state,
        player_id=0,
    )

    assert action is not None
    assert action.card is command_tower


def test_factory_prefers_command_tower_over_forest() -> None:
    forest = create_card(
        card_id="forest",
        name="Forest",
        type_line="Basic Land — Forest",
    )
    command_tower = create_enriched_land(
        card_id="command-tower",
        name="Command Tower",
    )

    state = create_state(
        cards=(
            forest,
            command_tower,
        )
    )

    action = LandActionFactory().create(
        state=state,
        player_id=0,
    )

    assert action is not None
    assert action.card is command_tower


def test_factory_uses_name_as_deterministic_tiebreaker() -> None:
    boseiju = create_enriched_land(
        card_id="boseiju",
        name="Boseiju, Who Endures",
    )
    forest = create_card(
        card_id="forest",
        name="Forest",
        type_line="Basic Land — Forest",
    )

    state = create_state(
        cards=(
            forest,
            boseiju,
        )
    )

    action = LandActionFactory().create(
        state=state,
        player_id=0,
    )

    assert action is not None
    assert action.card is boseiju


def test_factory_ignores_nonland_with_mana_ability() -> None:
    birds = CardEnricher(
        CardConfigLoader(
            CARD_CONFIG_DIRECTORY
        )
    ).enrich(
        create_card(
            card_id="birds",
            name="Birds of Paradise",
            type_line="Creature — Bird",
        )
    )
    forest = create_card(
        card_id="forest",
        name="Forest",
        type_line="Basic Land — Forest",
    )

    state = create_state(
        cards=(
            birds,
            forest,
        )
    )

    action = LandActionFactory().create(
        state=state,
        player_id=0,
    )

    assert action is not None
    assert action.card is forest


def test_factory_rejects_unknown_player() -> None:
    state = create_state()

    with pytest.raises(
        ValueError,
        match="Player not found: 99",
    ):
        LandActionFactory().create(
            state=state,
            player_id=99,
        )


def test_factory_does_not_modify_hand() -> None:
    forest = create_card(
        card_id="forest",
        name="Forest",
        type_line="Basic Land — Forest",
    )
    state = create_state(
        cards=(forest,),
    )
    player = state.players[0]

    action = LandActionFactory().create(
        state=state,
        player_id=0,
    )

    assert action is not None
    assert tuple(player.hand) == (forest,)
    assert player.land_played_this_turn == 0