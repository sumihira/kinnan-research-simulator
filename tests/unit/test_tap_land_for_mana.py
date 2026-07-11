import pytest

from krs.actions.tap_permanent import TapPermanentAction
from krs.cards.card import Card
from krs.engine.action_executor import ActionExecutor
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player
from krs.mana.mana import Mana


def create_card(
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


def create_land_permanent(
    *,
    permanent_id: int = 1,
    name: str = "Forest",
    type_line: str = "Basic Land — Forest",
    controller_id: int = 0,
    tapped: bool = False,
) -> Permanent:
    return Permanent(
        permanent_id=permanent_id,
        card=create_card(
            card_id=f"{name.lower()}-id",
            name=name,
            type_line=type_line,
        ),
        owner_id=controller_id,
        controller_id=controller_id,
        tapped=tapped,
        summoning_sick=False,
        entered_turn=1,
    )


def create_running_state() -> GameState:
    return GameState(
        players=[Player(player_id=0)],
        started=True,
        phase=Phase.MAIN,
        turn_number=1,
    )


@pytest.mark.parametrize(
    ("name", "type_line", "mana"),
    [
        ("Plains", "Basic Land — Plains", Mana.WHITE),
        ("Island", "Basic Land — Island", Mana.BLUE),
        ("Swamp", "Basic Land — Swamp", Mana.BLACK),
        ("Mountain", "Basic Land — Mountain", Mana.RED),
        ("Forest", "Basic Land — Forest", Mana.GREEN),
    ],
)
def test_basic_land_produces_expected_mana(
    name: str,
    type_line: str,
    mana: Mana,
) -> None:
    state = create_running_state()
    player = state.players[0]

    land = create_land_permanent(
        name=name,
        type_line=type_line,
    )
    player.battlefield.add(land)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=land,
            mana=mana,
        ),
    )

    assert land.tapped is True
    assert player.mana_pool.count(mana) == 1
    assert player.mana_pool.total() == 1
    assert state.mana_generated == 1
    assert state.action_count == 1


def test_tapped_land_cannot_be_tapped_again() -> None:
    state = create_running_state()
    player = state.players[0]

    forest = create_land_permanent(tapped=True)
    player.battlefield.add(forest)

    with pytest.raises(
        ValueError,
        match="Permanent is already tapped: Forest",
    ):
        ActionExecutor().execute(
            state,
            TapPermanentAction(
                player_id=0,
                turn_number=1,
                permanent=forest,
                mana=Mana.GREEN,
            ),
        )

    assert player.mana_pool.total() == 0
    assert state.mana_generated == 0
    assert state.action_count == 0


def test_land_cannot_produce_wrong_color() -> None:
    state = create_running_state()
    player = state.players[0]

    forest = create_land_permanent()
    player.battlefield.add(forest)

    with pytest.raises(
        ValueError,
        match="Land cannot produce selected mana",
    ):
        ActionExecutor().execute(
            state,
            TapPermanentAction(
                player_id=0,
                turn_number=1,
                permanent=forest,
                mana=Mana.BLUE,
            ),
        )

    assert forest.tapped is False
    assert player.mana_pool.total() == 0
    assert state.mana_generated == 0
    assert state.action_count == 0


def test_nonland_without_mana_ability_is_rejected() -> None:
    state = create_running_state()
    player = state.players[0]

    sol_ring = Permanent(
        permanent_id=1,
        card=create_card(
            "sol-ring-id",
            "Sol Ring",
            "Artifact",
        ),
        owner_id=0,
        controller_id=0,
        summoning_sick=False,
    )
    player.battlefield.add(sol_ring)

    with pytest.raises(
        ValueError,
        match="Mana ability not found at index 0: Sol Ring",
    ):
        ActionExecutor().execute(
            state,
            TapPermanentAction(
                player_id=0,
                turn_number=1,
                permanent=sol_ring,
                mana=Mana.COLORLESS,
            ),
        )

    assert sol_ring.tapped is False
    assert player.mana_pool.total() == 0
    assert state.mana_generated == 0
    assert state.action_count == 0


def test_land_not_on_battlefield_cannot_be_tapped() -> None:
    state = create_running_state()

    forest = create_land_permanent()

    with pytest.raises(
        ValueError,
        match="Permanent not found on battlefield: 1",
    ):
        ActionExecutor().execute(
            state,
            TapPermanentAction(
                player_id=0,
                turn_number=1,
                permanent=forest,
                mana=Mana.GREEN,
            ),
        )


def test_player_cannot_tap_land_they_do_not_control() -> None:
    state = create_running_state()
    player = state.players[0]

    forest = create_land_permanent(
        controller_id=1,
    )
    player.battlefield.add(forest)

    with pytest.raises(
        ValueError,
        match="Player does not control this permanent",
    ):
        ActionExecutor().execute(
            state,
            TapPermanentAction(
                player_id=0,
                turn_number=1,
                permanent=forest,
                mana=Mana.GREEN,
            ),
        )

    assert forest.tapped is False
    assert player.mana_pool.total() == 0


def test_mana_ability_cannot_be_used_before_game_start() -> None:
    player = Player(player_id=0)
    forest = create_land_permanent()
    player.battlefield.add(forest)

    state = GameState(
        players=[player],
        started=False,
    )

    with pytest.raises(
        ValueError,
        match="before the game starts",
    ):
        ActionExecutor().execute(
            state,
            TapPermanentAction(
                player_id=0,
                turn_number=1,
                permanent=forest,
                mana=Mana.GREEN,
            ),
        )


def test_mana_ability_cannot_be_used_after_game_end() -> None:
    state = create_running_state()
    state.game_over = True

    player = state.players[0]
    forest = create_land_permanent()
    player.battlefield.add(forest)

    with pytest.raises(
        ValueError,
        match="in a finished game",
    ):
        ActionExecutor().execute(
            state,
            TapPermanentAction(
                player_id=0,
                turn_number=1,
                permanent=forest,
                mana=Mana.GREEN,
            ),
        )


def test_dual_basic_land_types_can_produce_either_color() -> None:
    state = create_running_state()
    player = state.players[0]

    tropical_land = create_land_permanent(
        name="Test Tropical Land",
        type_line="Land — Forest Island",
    )
    player.battlefield.add(tropical_land)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=tropical_land,
            mana=Mana.BLUE,
        ),
    )

    assert player.mana_pool.count(Mana.BLUE) == 1
    assert tropical_land.tapped is True