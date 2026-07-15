from __future__ import annotations

import json
from pathlib import Path

from krs.cards.card import Card
from krs.engine.action_executor import ActionExecutor
from krs.engine.game_engine import GameEngine
from krs.game.game_state import GameState
from krs.game.library import Library
from krs.game.phase import Phase
from krs.game.player import Player
from krs.replay.game_engine_recorder import (
    ReplayGameEngineRecorder,
)
from krs.replay.replay import Replay
from krs.simulation.replay_run_service import (
    ReplayRunService,
)
from krs.simulation.replay_simulation_factory import (
    ReplaySimulationComponents,
)
from krs.simulation.simulation_config import SimulationConfig


def create_card(
    card_id: str,
) -> Card:
    return Card(
        id=card_id,
        name=f"Card {card_id}",
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line="Creature",
        power="1",
        toughness="1",
    )


def create_library(
    card_count: int = 10,
) -> Library:
    return Library(
        cards=[
            create_card(
                f"card_{index:02d}"
            )
            for index in range(card_count)
        ]
    )


def create_state() -> GameState:
    player = Player(
        player_id=0,
        library=create_library(),
    )

    return GameState(
        game_id=1,
        players=[player],
        seed=12345,
        started=False,
        game_over=False,
        winner=None,
        turn_number=1,
        phase=Phase.UNTAP,
        active_player_index=0,
    )


def create_config() -> SimulationConfig:
    return SimulationConfig(
        strategy_name="balanced",
        games=1,
        max_turns=6,
        seed=12345,
        mulligan_enabled=False,
        save_replays=True,
    )


def create_components() -> ReplaySimulationComponents:
    replay = Replay()

    action_executor = ActionExecutor(
        replay=replay,
    )
    game_engine = GameEngine(
        action_executor=action_executor,
    )
    recorded_game_engine = ReplayGameEngineRecorder(
        engine=game_engine,
        replay=replay,
    )

    return ReplaySimulationComponents(
        config=create_config(),
        replay=replay,
        action_executor=action_executor,
        game_engine=game_engine,
        recorded_game_engine=recorded_game_engine,
    )


def execute_finished_game(
    *,
    components: ReplaySimulationComponents,
    state: GameState,
) -> str:
    """
    Execute a minimal real game flow using the configured engines.

    The opening hand and draw step are executed through ActionExecutor,
    producing real Replay Action events.
    """
    engine = components.recorded_game_engine

    engine.start_game(state)
    engine.start_turn(state)

    engine.advance_phase(state)

    assert state.phase is Phase.UPKEEP

    engine.advance_phase(state)

    assert state.phase is Phase.DRAW

    state.game_over = True
    state.winner = "Player"

    return "completed"


def test_replay_run_writes_complete_bundle(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()
    output_directory = (
        tmp_path
        / "replays"
        / "game-0001"
    )

    result = ReplayRunService().run(
        components=components,
        state=state,
        run_game=lambda: execute_finished_game(
            components=components,
            state=state,
        ),
        output_directory=output_directory,
    )

    assert result.run_result == "completed"

    assert result.replay_paths.output_directory == (
        output_directory
    )
    assert (
        result.replay_paths.replay_json_path
        == output_directory / "replay.json"
    )
    assert (
        result.replay_paths.statistics_json_path
        == output_directory / "statistics.json"
    )
    assert (
        result.replay_paths.replay_html_path
        == output_directory / "replay.html"
    )

    assert all(
        path.is_file()
        for path in result.replay_paths.all_paths
    )


def test_replay_run_records_complete_event_flow(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()

    ReplayRunService().run(
        components=components,
        state=state,
        run_game=lambda: execute_finished_game(
            components=components,
            state=state,
        ),
        output_directory=tmp_path,
    )

    actions = tuple(
        event.action
        for event in components.replay.events
    )

    assert actions == (
        "draw",
        "game_start",
        "turn_start",
        "draw",
        "game_end",
    )

    assert components.replay.event_count == 5

    assert (
        components.replay.events[-1].description
        == "Game ended. Winner: Player."
    )


def test_replay_json_matches_recorded_events(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()

    result = ReplayRunService().run(
        components=components,
        state=state,
        run_game=lambda: execute_finished_game(
            components=components,
            state=state,
        ),
        output_directory=tmp_path,
    )

    replay_data = json.loads(
        result.replay_paths.replay_json_path.read_text(
            encoding="utf-8",
        )
    )

    assert replay_data["event_count"] == 5

    assert [
        event["action"]
        for event in replay_data["events"]
    ] == [
        "draw",
        "game_start",
        "turn_start",
        "draw",
        "game_end",
    ]

    assert replay_data["events"][0] == {
        "turn": 1,
        "phase": "untap",
        "action": "draw",
        "description": (
            "Player 0 executed draw."
        ),
    }

    assert replay_data["events"][-1] == {
        "turn": 1,
        "phase": "draw",
        "action": "game_end",
        "description": (
            "Game ended. Winner: Player."
        ),
    }


def test_statistics_json_matches_replay(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()

    result = ReplayRunService().run(
        components=components,
        state=state,
        run_game=lambda: execute_finished_game(
            components=components,
            state=state,
        ),
        output_directory=tmp_path,
    )

    statistics = json.loads(
        result.replay_paths.statistics_json_path.read_text(
            encoding="utf-8",
        )
    )

    assert statistics["event_count"] == 5
    assert statistics["turn_count"] == 1
    assert statistics["max_turn"] == 1
    assert statistics["game_start_count"] == 1
    assert statistics["game_end_count"] == 1

    assert statistics["action_counts"] == {
        "draw": 2,
        "game_end": 1,
        "game_start": 1,
        "turn_start": 1,
    }

    assert statistics["phase_counts"] == {
        "draw": 2,
        "untap": 3,
    }


def test_replay_html_matches_replay(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()

    result = ReplayRunService().run(
        components=components,
        state=state,
        run_game=lambda: execute_finished_game(
            components=components,
            state=state,
        ),
        output_directory=tmp_path,
    )

    html = (
        result.replay_paths.replay_html_path
        .read_text(
            encoding="utf-8",
        )
    )

    assert html.startswith("<!DOCTYPE html>")
    assert "Kinnan Research Simulator Replay" in html
    assert "5 events across 1 turn" in html
    assert "Event Timeline" in html

    assert html.count(
        "<code>draw</code>"
    ) == 2
    assert "<code>game_start</code>" in html
    assert "<code>turn_start</code>" in html
    assert "<code>game_end</code>" in html

    draw_position = html.index(
        "<code>draw</code>"
    )
    game_start_position = html.index(
        "<code>game_start</code>"
    )
    turn_start_position = html.index(
        "<code>turn_start</code>"
    )
    final_draw_position = html.index(
        "<code>draw</code>",
        draw_position + 1,
    )
    game_end_position = html.index(
        "<code>game_end</code>"
    )

    assert draw_position < game_start_position
    assert game_start_position < turn_start_position
    assert turn_start_position < final_draw_position
    assert final_draw_position < game_end_position


def test_replay_run_preserves_game_state_result(
    tmp_path: Path,
) -> None:
    components = create_components()
    state = create_state()

    ReplayRunService().run(
        components=components,
        state=state,
        run_game=lambda: execute_finished_game(
            components=components,
            state=state,
        ),
        output_directory=tmp_path,
    )

    player = state.players[0]

    assert state.started is True
    assert state.game_over is True
    assert state.winner == "Player"
    assert state.turn_number == 1
    assert state.phase is Phase.DRAW

    assert len(player.hand) == 8
    assert len(player.library) == 2


def test_replay_run_is_reproducible_with_fixed_seed(
    tmp_path: Path,
) -> None:
    first_components = create_components()
    first_state = create_state()

    first_result = ReplayRunService().run(
        components=first_components,
        state=first_state,
        run_game=lambda: execute_finished_game(
            components=first_components,
            state=first_state,
        ),
        output_directory=(
            tmp_path
            / "first"
        ),
    )

    second_components = create_components()
    second_state = create_state()

    second_result = ReplayRunService().run(
        components=second_components,
        state=second_state,
        run_game=lambda: execute_finished_game(
            components=second_components,
            state=second_state,
        ),
        output_directory=(
            tmp_path
            / "second"
        ),
    )

    first_replay_data = json.loads(
        first_result.replay_paths.replay_json_path.read_text(
            encoding="utf-8",
        )
    )
    second_replay_data = json.loads(
        second_result.replay_paths.replay_json_path.read_text(
            encoding="utf-8",
        )
    )

    first_statistics = json.loads(
        first_result.replay_paths.statistics_json_path.read_text(
            encoding="utf-8",
        )
    )
    second_statistics = json.loads(
        second_result.replay_paths.statistics_json_path.read_text(
            encoding="utf-8",
        )
    )

    assert first_replay_data == second_replay_data
    assert first_statistics == second_statistics