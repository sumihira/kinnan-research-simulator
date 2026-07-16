from __future__ import annotations

from unittest.mock import Mock

from krs.engine.game_engine import GameEngine
from krs.game.game_state import GameState
from krs.game.phase import Phase
from krs.game.player import Player
from krs.simulation.runner import GoldfishRunner


def create_running_state() -> GameState:
    return GameState(
        players=[
            Player(player_id=0),
        ],
        started=True,
        phase=Phase.MAIN,
        turn_number=2,
    )


def configure_end_phase(
    engine: Mock,
) -> None:
    def advance_phase(
        state: GameState,
    ) -> None:
        state.phase = Phase.END

    engine.advance_phase.side_effect = advance_phase


def test_runner_prioritizes_immediate_kinnan_cast() -> None:
    state = create_running_state()
    engine = Mock(
        spec=GameEngine,
    )
    execution_order: list[str] = []

    def execute_land(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert current_state is state
        assert player_id == 0
        execution_order.append("land")
        return True

    def execute_kinnan_cast(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert current_state is state
        assert player_id == 0
        execution_order.append("kinnan_cast")
        return True

    def execute_activation(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert current_state is state
        assert player_id == 0
        execution_order.append("activation")
        return False

    engine.execute_land_play_if_available.side_effect = (
        execute_land
    )
    engine.execute_kinnan_cast_if_available.side_effect = (
        execute_kinnan_cast
    )
    engine.execute_kinnan_activation_if_available.side_effect = (
        execute_activation
    )

    configure_end_phase(engine)

    result = GoldfishRunner(
        game_engine=engine,
        max_turns=2,
    ).run(state)

    assert execution_order == [
        "land",
        "kinnan_cast",
        "activation",
    ]
    assert result.kinnan_activations == 0

    (
        engine
        .execute_mana_permanent_cast_if_available
        .assert_not_called()
    )


def test_runner_casts_mana_permanent_when_kinnan_unavailable() -> None:
    state = create_running_state()
    engine = Mock(
        spec=GameEngine,
    )
    execution_order: list[str] = []

    kinnan_cast_results = iter(
        (
            False,
            True,
        )
    )

    def execute_land(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert current_state is state
        assert player_id == 0
        execution_order.append("land")
        return True

    def execute_kinnan_cast(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert current_state is state
        assert player_id == 0
        execution_order.append("kinnan_cast")
        return next(kinnan_cast_results)

    def execute_mana_permanent(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert current_state is state
        assert player_id == 0
        execution_order.append("mana_permanent")
        return True

    def execute_activation(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert current_state is state
        assert player_id == 0
        execution_order.append("activation")
        return False

    engine.execute_land_play_if_available.side_effect = (
        execute_land
    )
    engine.execute_kinnan_cast_if_available.side_effect = (
        execute_kinnan_cast
    )
    (
        engine
        .execute_mana_permanent_cast_if_available
        .side_effect
    ) = execute_mana_permanent
    engine.execute_kinnan_activation_if_available.side_effect = (
        execute_activation
    )

    configure_end_phase(engine)

    GoldfishRunner(
        game_engine=engine,
        max_turns=2,
    ).run(state)

    assert execution_order == [
        "land",
        "kinnan_cast",
        "mana_permanent",
        "kinnan_cast",
        "activation",
    ]


def test_runner_stops_mana_development_after_kinnan_cast() -> None:
    state = create_running_state()
    engine = Mock(
        spec=GameEngine,
    )

    engine.execute_land_play_if_available.return_value = True

    engine.execute_kinnan_cast_if_available.side_effect = (
        False,
        True,
    )

    (
        engine
        .execute_mana_permanent_cast_if_available
        .return_value
    ) = True

    (
        engine
        .execute_kinnan_activation_if_available
        .return_value
    ) = False

    configure_end_phase(engine)

    GoldfishRunner(
        game_engine=engine,
        max_turns=2,
    ).run(state)

    assert (
        engine
        .execute_mana_permanent_cast_if_available
        .call_count
        == 1
    )
    assert (
        engine
        .execute_kinnan_cast_if_available
        .call_count
        == 2
    )


def test_runner_continues_mana_development_until_kinnan_castable() -> None:
    state = create_running_state()
    engine = Mock(
        spec=GameEngine,
    )

    engine.execute_land_play_if_available.return_value = True

    engine.execute_kinnan_cast_if_available.side_effect = (
        False,
        False,
        True,
    )

    (
        engine
        .execute_mana_permanent_cast_if_available
        .side_effect
    ) = (
        True,
        True,
    )

    (
        engine
        .execute_kinnan_activation_if_available
        .return_value
    ) = False

    configure_end_phase(engine)

    GoldfishRunner(
        game_engine=engine,
        max_turns=2,
    ).run(state)

    assert (
        engine
        .execute_mana_permanent_cast_if_available
        .call_count
        == 2
    )
    assert (
        engine
        .execute_kinnan_cast_if_available
        .call_count
        == 3
    )


def test_runner_stops_when_no_mana_permanent_is_available() -> None:
    state = create_running_state()
    engine = Mock(
        spec=GameEngine,
    )

    engine.execute_land_play_if_available.return_value = False
    engine.execute_kinnan_cast_if_available.return_value = False

    (
        engine
        .execute_mana_permanent_cast_if_available
        .return_value
    ) = False

    (
        engine
        .execute_kinnan_activation_if_available
        .return_value
    ) = False

    configure_end_phase(engine)

    GoldfishRunner(
        game_engine=engine,
        max_turns=2,
    ).run(state)

    assert (
        engine
        .execute_kinnan_cast_if_available
        .call_count
        == 1
    )
    assert (
        engine
        .execute_mana_permanent_cast_if_available
        .call_count
        == 1
    )


def test_runner_respects_mana_permanent_cast_limit() -> None:
    state = create_running_state()
    engine = Mock(
        spec=GameEngine,
    )

    engine.execute_land_play_if_available.return_value = False
    engine.execute_kinnan_cast_if_available.return_value = False

    (
        engine
        .execute_mana_permanent_cast_if_available
        .return_value
    ) = True

    (
        engine
        .execute_kinnan_activation_if_available
        .return_value
    ) = False

    configure_end_phase(engine)

    GoldfishRunner(
        game_engine=engine,
        max_turns=2,
        max_mana_permanent_casts_per_turn=3,
    ).run(state)

    assert (
        engine
        .execute_mana_permanent_cast_if_available
        .call_count
        == 3
    )

    assert (
        engine
        .execute_kinnan_cast_if_available
        .call_count
        == 4
    )


def test_runner_skips_development_after_game_over() -> None:
    state = create_running_state()
    engine = Mock(
        spec=GameEngine,
    )

    def execute_land(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert player_id == 0
        current_state.game_over = True
        current_state.winner = "Player"
        return True

    engine.execute_land_play_if_available.side_effect = (
        execute_land
    )

    result = GoldfishRunner(
        game_engine=engine,
        max_turns=2,
    ).run(state)

    assert result.game_over is True
    assert result.winner == "Player"

    engine.execute_kinnan_cast_if_available.assert_not_called()
    (
        engine
        .execute_mana_permanent_cast_if_available
        .assert_not_called()
    )
    (
        engine
        .execute_kinnan_activation_if_available
        .assert_not_called()
    )