from __future__ import annotations

from pathlib import Path

import pytest

from krs.actions.tap_permanent import TapPermanentAction
from krs.cards.card import Card
from krs.cards.card_config_loader import CardConfigLoader
from krs.cards.card_enricher import CardEnricher
from krs.engine.action_executor import ActionExecutor
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player
from krs.mana.mana import Mana


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
    permanent_id: int,
    name: str,
    type_line: str = "Land",
) -> Permanent:
    card = CardEnricher(
        CardConfigLoader(
            CARD_CONFIG_DIRECTORY
        )
    ).enrich(
        create_card(
            card_id=name.casefold().replace(
                " ",
                "-",
            ),
            name=name,
            type_line=type_line,
        )
    )

    return Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=0,
        controller_id=0,
        summoning_sick=False,
        entered_turn=1,
    )


def create_basic_land(
    *,
    permanent_id: int,
    name: str,
    type_line: str,
) -> Permanent:
    return Permanent(
        permanent_id=permanent_id,
        card=create_card(
            card_id=name.casefold(),
            name=name,
            type_line=type_line,
        ),
        owner_id=0,
        controller_id=0,
        summoning_sick=False,
        entered_turn=1,
    )


def create_running_state() -> GameState:
    return GameState(
        players=[
            Player(player_id=0),
        ],
        started=True,
        phase=Phase.MAIN,
        turn_number=1,
    )


def tap_for_mana(
    *,
    state: GameState,
    permanent: Permanent,
    mana: Mana,
) -> None:
    state.players[0].battlefield.add(
        permanent
    )

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=state.turn_number,
            permanent=permanent,
            mana=mana,
        ),
    )


@pytest.mark.parametrize(
    (
        "card_name",
        "mana",
        "expected_amount",
    ),
    (
        (
            "Ancient Tomb",
            Mana.COLORLESS,
            2,
        ),
        (
            "Boseiju, Who Endures",
            Mana.GREEN,
            1,
        ),
        (
            "Command Tower",
            Mana.BLUE,
            1,
        ),
        (
            "Command Tower",
            Mana.GREEN,
            1,
        ),
        (
            "Otawara, Soaring City",
            Mana.BLUE,
            1,
        ),
        (
            "Treasure Vault",
            Mana.COLORLESS,
            1,
        ),
        (
            "Waterlogged Grove",
            Mana.BLUE,
            1,
        ),
        (
            "Waterlogged Grove",
            Mana.GREEN,
            1,
        ),
        (
            "Yavimaya Coast",
            Mana.COLORLESS,
            1,
        ),
        (
            "Yavimaya Coast",
            Mana.BLUE,
            1,
        ),
        (
            "Yavimaya Coast",
            Mana.GREEN,
            1,
        ),
    ),
)
def test_configured_land_produces_expected_mana(
    card_name: str,
    mana: Mana,
    expected_amount: int,
) -> None:
    state = create_running_state()

    land = create_enriched_land(
        permanent_id=1,
        name=card_name,
    )

    tap_for_mana(
        state=state,
        permanent=land,
        mana=mana,
    )

    assert land.tapped is True
    assert (
        state.players[0].mana_pool.count(mana)
        == expected_amount
    )
    assert (
        state.players[0].mana_pool.total()
        == expected_amount
    )
    assert (
        state.mana_generated
        == expected_amount
    )
    assert state.action_count == 1


@pytest.mark.parametrize(
    "card_name",
    (
        "City of Brass",
        "Forbidden Orchard",
        "Mana Confluence",
    ),
)
@pytest.mark.parametrize(
    "mana",
    (
        Mana.WHITE,
        Mana.BLUE,
        Mana.BLACK,
        Mana.RED,
        Mana.GREEN,
    ),
)
def test_five_color_land_can_produce_selected_color(
    card_name: str,
    mana: Mana,
) -> None:
    state = create_running_state()

    land = create_enriched_land(
        permanent_id=1,
        name=card_name,
    )

    tap_for_mana(
        state=state,
        permanent=land,
        mana=mana,
    )

    assert state.players[0].mana_pool.count(mana) == 1
    assert state.players[0].mana_pool.total() == 1


def test_configured_land_rejects_unsupported_color() -> None:
    state = create_running_state()
    land = create_enriched_land(
        permanent_id=1,
        name="Command Tower",
    )
    state.players[0].battlefield.add(
        land
    )

    with pytest.raises(
        ValueError,
        match=(
            "Mana ability cannot produce selected mana"
        ),
    ):
        ActionExecutor().execute(
            state,
            TapPermanentAction(
                player_id=0,
                turn_number=1,
                permanent=land,
                mana=Mana.RED,
            ),
        )

    assert land.tapped is False
    assert state.players[0].mana_pool.total() == 0
    assert state.mana_generated == 0
    assert state.action_count == 0


def test_basic_land_without_config_uses_basic_land_type() -> None:
    state = create_running_state()

    forest = create_basic_land(
        permanent_id=1,
        name="Forest",
        type_line="Basic Land — Forest",
    )

    tap_for_mana(
        state=state,
        permanent=forest,
        mana=Mana.GREEN,
    )

    assert state.players[0].mana_pool.count(
        Mana.GREEN
    ) == 1


def test_typed_dual_land_without_config_uses_land_types() -> None:
    state = create_running_state()

    breeding_pool = create_basic_land(
        permanent_id=1,
        name="Breeding Pool",
        type_line="Land — Forest Island",
    )

    tap_for_mana(
        state=state,
        permanent=breeding_pool,
        mana=Mana.BLUE,
    )

    assert state.players[0].mana_pool.count(
        Mana.BLUE
    ) == 1


def test_configured_land_does_not_receive_kinnan_bonus() -> None:
    state = create_running_state()

    command_tower = create_enriched_land(
        permanent_id=1,
        name="Command Tower",
    )

    kinnan = Permanent(
        permanent_id=2,
        card=create_card(
            card_id="kinnan",
            name="Kinnan, Bonder Prodigy",
            type_line=(
                "Legendary Creature — Human Druid"
            ),
        ),
        owner_id=0,
        controller_id=0,
        summoning_sick=False,
        entered_turn=1,
    )

    state.players[0].battlefield.add(
        kinnan
    )

    tap_for_mana(
        state=state,
        permanent=command_tower,
        mana=Mana.GREEN,
    )

    assert state.players[0].mana_pool.count(
        Mana.GREEN
    ) == 1
    assert state.mana_generated == 1


@pytest.mark.parametrize(
    "filename",
    (
        "ancient_tomb.yaml",
        "boseiju_who_endures.yaml",
        "city_of_brass.yaml",
        "command_tower.yaml",
        "forbidden_orchard.yaml",
        "mana_confluence.yaml",
        "otawara_soaring_city.yaml",
        "treasure_vault.yaml",
        "waterlogged_grove.yaml",
        "yavimaya_coast.yaml",
    ),
)
def test_land_config_filename_is_snake_case(
    filename: str,
) -> None:
    path = CARD_CONFIG_DIRECTORY / filename

    assert path.exists()
    assert path.name == path.name.casefold()
    assert " " not in path.name
    assert "," not in path.name