import pytest

from krs.cards.card import Card
from krs.engine.game_engine import GameEngine
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player
from krs.mana.mana import Mana


def create_card(
    card_id: str = "card-id",
    name: str = "Test Permanent",
    type_line: str = "Artifact",
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line=type_line,
    )


def create_running_state(
    *,
    turn_number: int = 1,
    phase: Phase = Phase.UNTAP,
) -> GameState:
    player = Player(player_id=0)

    return GameState(
        players=[player],
        started=True,
        turn_number=turn_number,
        phase=phase,
    )


def test_start_turn_sets_phase_to_untap() -> None:
    state = create_running_state(
        phase=Phase.END,
    )

    GameEngine().start_turn(state)

    assert state.phase is Phase.UNTAP


def test_start_turn_resets_land_play_count() -> None:
    state = create_running_state()
    player = state.players[0]
    player.land_played_this_turn = 1

    GameEngine().start_turn(state)

    assert player.land_played_this_turn == 0


def test_start_turn_untaps_active_player_permanents() -> None:
    state = create_running_state()
    player = state.players[0]

    permanent = Permanent(
        permanent_id=1,
        card=create_card(),
        owner_id=0,
        controller_id=0,
        tapped=True,
        entered_turn=0,
    )
    player.battlefield.add(permanent)

    GameEngine().start_turn(state)

    assert permanent.tapped is False


def test_start_turn_removes_old_summoning_sickness() -> None:
    state = create_running_state(
        turn_number=2,
    )
    player = state.players[0]

    permanent = Permanent(
        permanent_id=1,
        card=create_card(
            type_line="Creature — Elf Druid",
        ),
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
        entered_turn=1,
    )
    player.battlefield.add(permanent)

    GameEngine().start_turn(state)

    assert permanent.summoning_sick is False


def test_start_turn_keeps_current_turn_summoning_sickness() -> None:
    state = create_running_state(
        turn_number=2,
    )
    player = state.players[0]

    permanent = Permanent(
        permanent_id=1,
        card=create_card(
            type_line="Creature — Elf Druid",
        ),
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
        entered_turn=2,
    )
    player.battlefield.add(permanent)

    GameEngine().start_turn(state)

    assert permanent.summoning_sick is True


def test_start_turn_clears_active_player_mana_pool() -> None:
    state = create_running_state()
    player = state.players[0]

    player.mana_pool.add(Mana.GREEN, 2)

    GameEngine().start_turn(state)

    assert player.mana_pool.total() == 0


@pytest.mark.parametrize(
    ("start_phase", "expected_phase"),
    [
        (Phase.UNTAP, Phase.UPKEEP),
        (Phase.UPKEEP, Phase.DRAW),
        (Phase.DRAW, Phase.MAIN),
        (Phase.MAIN, Phase.END),
    ],
)
def test_advance_phase(
    start_phase: Phase,
    expected_phase: Phase,
) -> None:
    state = create_running_state(
        phase=start_phase,
    )

    GameEngine().advance_phase(state)

    assert state.phase is expected_phase


def test_advance_phase_rejects_end_phase() -> None:
    state = create_running_state(
        phase=Phase.END,
    )

    with pytest.raises(
        ValueError,
        match="Cannot advance beyond END phase",
    ):
        GameEngine().advance_phase(state)


def test_end_turn_increments_turn_number() -> None:
    state = create_running_state(
        turn_number=1,
        phase=Phase.END,
    )

    GameEngine().end_turn(state)

    assert state.turn_number == 2
    assert state.phase is Phase.UNTAP


def test_end_turn_resets_land_play_count() -> None:
    state = create_running_state(
        phase=Phase.END,
    )
    player = state.players[0]
    player.land_played_this_turn = 1

    GameEngine().end_turn(state)

    assert player.land_played_this_turn == 0


def test_end_turn_clears_all_mana_pools() -> None:
    first = Player(player_id=0)
    second = Player(player_id=1)

    first.mana_pool.add(Mana.GREEN)
    second.mana_pool.add(Mana.BLUE)

    state = GameState(
        players=[first, second],
        started=True,
        phase=Phase.END,
    )

    GameEngine().end_turn(state)

    assert first.mana_pool.total() == 0
    assert second.mana_pool.total() == 0


def test_end_turn_advances_active_player() -> None:
    first = Player(player_id=0)
    second = Player(player_id=1)

    state = GameState(
        players=[first, second],
        started=True,
        phase=Phase.END,
        active_player_index=0,
    )

    GameEngine().end_turn(state)

    assert state.active_player_index == 1
    assert state.active_player is second


def test_end_turn_wraps_active_player_index() -> None:
    first = Player(player_id=0)
    second = Player(player_id=1)

    state = GameState(
        players=[first, second],
        started=True,
        phase=Phase.END,
        active_player_index=1,
    )

    GameEngine().end_turn(state)

    assert state.active_player_index == 0
    assert state.active_player is first


def test_end_turn_requires_end_phase() -> None:
    state = create_running_state(
        phase=Phase.MAIN,
    )

    with pytest.raises(
        ValueError,
        match="only end during the END phase",
    ):
        GameEngine().end_turn(state)


def test_turn_operations_reject_unstarted_game() -> None:
    state = GameState(
        players=[Player(player_id=0)],
        started=False,
    )

    with pytest.raises(
        ValueError,
        match="Game has not started",
    ):
        GameEngine().start_turn(state)


def test_turn_operations_reject_finished_game() -> None:
    state = GameState(
        players=[Player(player_id=0)],
        started=True,
        game_over=True,
    )

    with pytest.raises(
        ValueError,
        match="Game has already finished",
    ):
        GameEngine().start_turn(state)