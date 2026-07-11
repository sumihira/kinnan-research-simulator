from krs.game.game_state import GameState
from krs.game.phase import Phase
from krs.game.player import Player


def test_game_state_can_be_created() -> None:
    player = Player(player_id=0)

    state = GameState(
        players=[player],
        turn_number=1,
        phase=Phase.UNTAP,
        active_player_index=0,
        game_id=1,
        seed=12345,
    )

    assert state.players == [player]
    assert state.turn_number == 1
    assert state.phase is Phase.UNTAP
    assert state.active_player_index == 0
    assert state.game_id == 1
    assert state.seed == 12345


def test_game_state_has_expected_defaults() -> None:
    state = GameState()

    assert state.players == []
    assert state.turn_number == 1
    assert state.phase is Phase.UNTAP
    assert state.active_player_index == 0
    assert state.stack_size == 0
    assert state.game_over is False
    assert state.winner is None
    assert state.action_count == 0
    assert state.mana_spent == 0
    assert state.mana_generated == 0
    assert state.seed is None
    assert state.game_id == 0
    assert state.started is False


def test_game_states_do_not_share_player_lists() -> None:
    first = GameState()
    second = GameState()

    first.players.append(Player(player_id=0))

    assert len(first.players) == 1
    assert len(second.players) == 0


def test_active_player_can_be_resolved() -> None:
    first = Player(player_id=0, name="First")
    second = Player(player_id=1, name="Second")

    state = GameState(
        players=[first, second],
        active_player_index=1,
    )

    assert state.active_player is second


def test_active_player_returns_none_without_players() -> None:
    state = GameState()

    assert state.active_player is None


def test_active_player_returns_none_for_invalid_index() -> None:
    state = GameState(
        players=[Player(player_id=0)],
        active_player_index=5,
    )

    assert state.active_player is None


def test_game_state_can_track_statistics() -> None:
    state = GameState()

    state.action_count += 3
    state.mana_generated += 7
    state.mana_spent += 4

    assert state.action_count == 3
    assert state.mana_generated == 7
    assert state.mana_spent == 4


def test_game_state_can_be_marked_finished() -> None:
    state = GameState()

    state.game_over = True
    state.winner = "combo"

    assert state.game_over is True
    assert state.winner == "combo"