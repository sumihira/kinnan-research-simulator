from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from krs.game.game_state import GameState
from krs.game.phase import Phase
from krs.game.player import Player
from krs.replay.replay_bundle import (
    ReplayBundlePaths,
    ReplayBundleWriter,
)
from krs.replay.replay_event import ReplayEvent
from krs.simulation.replay_run_service import (
    ReplayRunResult,
    ReplayRunService,
)
from krs.simulation.replay_simulation_factory import (
    ReplaySimulationComponents,
    ReplaySimulationFactory,
)
from krs.simulation.simulation_config import SimulationConfig


def create_config(
    *,
    save_replays: bool = True,
) -> SimulationConfig:
    return SimulationConfig(
        strategy_name="balanced",
        games=1,
        max_turns=6,
        seed=12345,
        mulligan_enabled=True,
        save_replays=save_replays,
    )


def create_components() -> ReplaySimulationComponents:
    return ReplaySimulationFactory().create(
        create_config()
    )


def create_state(
    *,
    game_over: bool = False,
    winner: str | None = None,
) -> GameState:
    return GameState(
        game_id=1,
        players=[
            Player(
                player_id=0,
            ),
        ],
        started=True,
        game_over=game_over,
        winner=winner,
        turn_number=3,
        phase=Phase.MAIN,
        active_player_index=0,
    )


def create_bundle_paths(
    output_directory: Path,
) -> ReplayBundlePaths:
    return ReplayBundlePaths(
        output_directory=output_directory,
        replay_json_path=(
            output_directory
            / "replay.json"
        ),
        statistics_json_path=(
            output_directory
            / "statistics.json"
        ),
        replay_html_path=(
            output_directory
            / "replay.html"
        ),
    )


def test_run_returns_game_result_and_bundle_paths(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()
    expected_result = object()

    def run_game() -> object:
        state.game_over = True
        state.winner = "Player"
        return expected_result

    result = ReplayRunService().run(
        components=components,
        state=state,
        run_game=run_game,
        output_directory=tmp_path,
    )

    assert isinstance(
        result,
        ReplayRunResult,
    )
    assert result.run_result is expected_result
    assert result.replay_paths == (
        create_bundle_paths(tmp_path)
    )


def test_run_writes_every_replay_file(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()

    def run_game() -> str:
        state.game_over = True
        return "completed"

    result = ReplayRunService().run(
        components=components,
        state=state,
        run_game=run_game,
        output_directory=tmp_path,
    )

    assert all(
        path.is_file()
        for path in result.replay_paths.all_paths
    )


def test_run_records_game_end_for_finished_game(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()

    def run_game() -> None:
        state.game_over = True
        state.winner = "Player"

    ReplayRunService().run(
        components=components,
        state=state,
        run_game=run_game,
        output_directory=tmp_path,
    )

    assert components.replay.events[-1].action == (
        "game_end"
    )
    assert (
        components.replay.events[-1].description
        == "Game ended. Winner: Player."
    )


def test_run_records_game_end_without_winner(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()

    def run_game() -> None:
        state.game_over = True
        state.winner = None

    ReplayRunService().run(
        components=components,
        state=state,
        run_game=run_game,
        output_directory=tmp_path,
    )

    assert (
        components.replay.events[-1].description
        == "Game ended without a winner."
    )


def test_run_does_not_duplicate_game_end(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()

    def run_game() -> None:
        state.game_over = True
        state.winner = "Player"

        components.replay.add(
            ReplayEvent(
                turn=state.turn_number,
                phase="main",
                action="game_end",
                description=(
                    "Game ended. Winner: Player."
                ),
            )
        )

    ReplayRunService().run(
        components=components,
        state=state,
        run_game=run_game,
        output_directory=tmp_path,
    )

    assert tuple(
        event.action
        for event in components.replay.events
    ).count("game_end") == 1


def test_run_saves_running_replay_without_game_end(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()

    result = ReplayRunService().run(
        components=components,
        state=state,
        run_game=lambda: "turn-limit",
        output_directory=tmp_path,
    )

    assert result.run_result == "turn-limit"
    assert all(
        event.action != "game_end"
        for event in components.replay.events
    )
    assert all(
        path.is_file()
        for path in result.replay_paths.all_paths
    )


def test_run_preserves_existing_events(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()

    existing_event = ReplayEvent(
        turn=1,
        phase="draw",
        action="draw",
        description="Player 0 executed draw.",
    )
    components.replay.add(
        existing_event
    )

    def run_game() -> None:
        state.game_over = True

    ReplayRunService().run(
        components=components,
        state=state,
        run_game=run_game,
        output_directory=tmp_path,
    )

    assert components.replay.events[0] is (
        existing_event
    )
    assert components.replay.events[-1].action == (
        "game_end"
    )


def test_run_delegates_bundle_writing(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()
    bundle_writer = Mock(
        spec=ReplayBundleWriter,
    )
    expected_paths = create_bundle_paths(
        tmp_path
    )
    bundle_writer.write.return_value = (
        expected_paths
    )

    def run_game() -> str:
        state.game_over = True
        return "result"

    service = ReplayRunService(
        bundle_writer=bundle_writer,
    )

    result = service.run(
        components=components,
        state=state,
        run_game=run_game,
        output_directory=tmp_path,
    )

    bundle_writer.write.assert_called_once_with(
        components.replay,
        tmp_path,
    )
    assert result.replay_paths is expected_paths


def test_run_propagates_game_exception(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()
    bundle_writer = Mock(
        spec=ReplayBundleWriter,
    )

    def run_game() -> None:
        raise RuntimeError(
            "Simulation failed."
        )

    with pytest.raises(
        RuntimeError,
        match="Simulation failed.",
    ):
        ReplayRunService(
            bundle_writer=bundle_writer,
        ).run(
            components=components,
            state=state,
            run_game=run_game,
            output_directory=tmp_path,
        )

    bundle_writer.write.assert_not_called()


def test_run_propagates_bundle_exception(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()
    bundle_writer = Mock(
        spec=ReplayBundleWriter,
    )
    bundle_writer.write.side_effect = RuntimeError(
        "Bundle failed."
    )

    with pytest.raises(
        RuntimeError,
        match="Bundle failed.",
    ):
        ReplayRunService(
            bundle_writer=bundle_writer,
        ).run(
            components=components,
            state=state,
            run_game=lambda: "result",
            output_directory=tmp_path,
        )


def test_run_rejects_finished_initial_state(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state(
        game_over=True,
    )
    run_game = Mock()

    with pytest.raises(
        ValueError,
        match=(
            "Cannot start a Replay run "
            "for a finished game."
        ),
    ):
        ReplayRunService().run(
            components=components,
            state=state,
            run_game=run_game,
            output_directory=tmp_path,
        )

    run_game.assert_not_called()


def test_run_rejects_non_callable(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()

    with pytest.raises(
        TypeError,
        match="run_game must be callable.",
    ):
        ReplayRunService().run(
            components=components,
            state=state,
            run_game="invalid",  # type: ignore[arg-type]
            output_directory=tmp_path,
        )


def test_run_callable_is_called_once(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()
    run_game = Mock(
        return_value="result",
    )

    ReplayRunService().run(
        components=components,
        state=state,
        run_game=run_game,
        output_directory=tmp_path,
    )

    run_game.assert_called_once_with()


def test_service_is_immutable() -> None:
    service = ReplayRunService()

    with pytest.raises(AttributeError):
        service.bundle_writer = (  # type: ignore[misc]
            ReplayBundleWriter()
        )