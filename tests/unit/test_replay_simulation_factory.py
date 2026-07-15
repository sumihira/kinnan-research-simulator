from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import Mock

import pytest

from krs.ai.strategy_factory import StrategyFactory
from krs.engine.action_executor import ActionExecutor
from krs.engine.game_engine import GameEngine
from krs.replay.game_engine_recorder import (
    ReplayGameEngineRecorder,
)
from krs.replay.replay import Replay
from krs.simulation.replay_simulation_factory import (
    ReplaySimulationComponents,
    ReplaySimulationFactory,
)
from krs.simulation.simulation_config import SimulationConfig
from krs.simulation.simulation_config_loader import (
    SimulationConfigLoader,
)


def create_config(
    *,
    save_replays: bool = True,
    strategy_name: str = "balanced",
) -> SimulationConfig:
    return SimulationConfig(
        strategy_name=strategy_name,
        games=10,
        max_turns=6,
        seed=12345,
        mulligan_enabled=True,
        save_replays=save_replays,
    )


def test_create_returns_replay_simulation_components() -> None:
    components = ReplaySimulationFactory().create(
        create_config()
    )

    assert isinstance(
        components,
        ReplaySimulationComponents,
    )
    assert isinstance(
        components.replay,
        Replay,
    )
    assert isinstance(
        components.action_executor,
        ActionExecutor,
    )
    assert isinstance(
        components.game_engine,
        GameEngine,
    )
    assert isinstance(
        components.recorded_game_engine,
        ReplayGameEngineRecorder,
    )


def test_create_preserves_config() -> None:
    config = create_config()

    components = ReplaySimulationFactory().create(
        config
    )

    assert components.config is config


def test_action_executor_uses_shared_replay() -> None:
    components = ReplaySimulationFactory().create(
        create_config()
    )

    assert (
        components.action_executor.replay
        is components.replay
    )


def test_game_engine_recorder_uses_shared_replay() -> None:
    components = ReplaySimulationFactory().create(
        create_config()
    )

    assert (
        components.recorded_game_engine.replay
        is components.replay
    )


def test_game_engine_recorder_wraps_created_engine() -> None:
    components = ReplaySimulationFactory().create(
        create_config()
    )

    assert (
        components.recorded_game_engine.engine
        is components.game_engine
    )


def test_created_replay_is_initially_empty() -> None:
    components = ReplaySimulationFactory().create(
        create_config()
    )

    assert components.replay.is_empty is True
    assert components.replay.event_count == 0


def test_create_does_not_reuse_replay_between_calls() -> None:
    factory = ReplaySimulationFactory()
    config = create_config()

    first = factory.create(config)
    second = factory.create(config)

    assert first.replay is not second.replay
    assert (
        first.action_executor
        is not second.action_executor
    )
    assert first.game_engine is not second.game_engine
    assert (
        first.recorded_game_engine
        is not second.recorded_game_engine
    )


def test_create_uses_configured_strategy() -> None:
    strategy_factory = Mock(
        spec=StrategyFactory,
    )

    factory = ReplaySimulationFactory(
        strategy_factory=strategy_factory,
    )

    factory.create(
        create_config(
            strategy_name="combo",
        )
    )

    strategy_factory.create_kinnan_hit_selector.assert_called_once_with(
        "combo"
    )


def test_create_rejects_disabled_save_replays() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Replay simulation requires "
            "save_replays=True."
        ),
    ):
        ReplaySimulationFactory().create(
            create_config(
                save_replays=False,
            )
        )


def test_load_config_delegates_to_loader(
    tmp_path: Path,
) -> None:
    config = create_config()
    config_path = tmp_path / "simulation.yaml"

    config_loader = Mock(
        spec=SimulationConfigLoader,
    )
    config_loader.load.return_value = config

    factory = ReplaySimulationFactory(
        config_loader=config_loader,
    )

    result = factory.load_config(
        config_path
    )

    assert result is config

    config_loader.load.assert_called_once_with(
        config_path
    )


def test_create_from_file_loads_and_creates(
    tmp_path: Path,
) -> None:
    config = create_config()
    config_path = tmp_path / "simulation.yaml"

    config_loader = Mock(
        spec=SimulationConfigLoader,
    )
    config_loader.load.return_value = config

    factory = ReplaySimulationFactory(
        config_loader=config_loader,
    )

    components = factory.create_from_file(
        config_path
    )

    config_loader.load.assert_called_once_with(
        config_path
    )
    assert components.config is config
    assert (
        components.action_executor.replay
        is components.replay
    )
    assert (
        components.recorded_game_engine.replay
        is components.replay
    )


def test_create_from_file_rejects_disabled_replay_config(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "simulation.yaml"

    config_loader = Mock(
        spec=SimulationConfigLoader,
    )
    config_loader.load.return_value = create_config(
        save_replays=False,
    )

    factory = ReplaySimulationFactory(
        config_loader=config_loader,
    )

    with pytest.raises(
        ValueError,
        match=(
            "Replay simulation requires "
            "save_replays=True."
        ),
    ):
        factory.create_from_file(
            config_path
        )


def test_recorded_engine_delegates_game_engine_api() -> None:
    components = ReplaySimulationFactory().create(
        create_config()
    )

    assert (
        components.recorded_game_engine
        .create_kinnan_activation_action
        is not None
    )
    assert (
        components.recorded_game_engine
        .find_activatable_kinnan
        is not None
    )
    assert (
        components.recorded_game_engine
        .execute_kinnan_activation_if_available
        is not None
    )


def test_components_are_immutable() -> None:
    components = ReplaySimulationFactory().create(
        create_config()
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        components.replay = Replay()  # type: ignore[misc]


def test_components_reject_disabled_config() -> None:
    replay = Replay()
    action_executor = ActionExecutor(
        replay=replay,
    )
    game_engine = GameEngine(
        action_executor=action_executor,
    )
    recorder = ReplayGameEngineRecorder(
        engine=game_engine,
        replay=replay,
    )

    with pytest.raises(
        ValueError,
        match=(
            "Replay simulation components require "
            "save_replays=True."
        ),
    ):
        ReplaySimulationComponents(
            config=create_config(
                save_replays=False,
            ),
            replay=replay,
            action_executor=action_executor,
            game_engine=game_engine,
            recorded_game_engine=recorder,
        )


def test_components_reject_executor_with_different_replay() -> None:
    shared_replay = Replay()
    other_replay = Replay()

    action_executor = ActionExecutor(
        replay=other_replay,
    )
    game_engine = GameEngine(
        action_executor=action_executor,
    )
    recorder = ReplayGameEngineRecorder(
        engine=game_engine,
        replay=shared_replay,
    )

    with pytest.raises(
        ValueError,
        match=(
            "ActionExecutor must use "
            "the shared Replay."
        ),
    ):
        ReplaySimulationComponents(
            config=create_config(),
            replay=shared_replay,
            action_executor=action_executor,
            game_engine=game_engine,
            recorded_game_engine=recorder,
        )


def test_components_reject_recorder_with_different_replay() -> None:
    shared_replay = Replay()
    other_replay = Replay()

    action_executor = ActionExecutor(
        replay=shared_replay,
    )
    game_engine = GameEngine(
        action_executor=action_executor,
    )
    recorder = ReplayGameEngineRecorder(
        engine=game_engine,
        replay=other_replay,
    )

    with pytest.raises(
        ValueError,
        match=(
            "ReplayGameEngineRecorder must use "
            "the shared Replay."
        ),
    ):
        ReplaySimulationComponents(
            config=create_config(),
            replay=shared_replay,
            action_executor=action_executor,
            game_engine=game_engine,
            recorded_game_engine=recorder,
        )


def test_components_reject_recorder_wrapping_other_engine() -> None:
    replay = Replay()

    action_executor = ActionExecutor(
        replay=replay,
    )
    game_engine = GameEngine(
        action_executor=action_executor,
    )
    other_engine = GameEngine()
    recorder = ReplayGameEngineRecorder(
        engine=other_engine,
        replay=replay,
    )

    with pytest.raises(
        ValueError,
        match=(
            "ReplayGameEngineRecorder must wrap "
            "the configured GameEngine."
        ),
    ):
        ReplaySimulationComponents(
            config=create_config(),
            replay=replay,
            action_executor=action_executor,
            game_engine=game_engine,
            recorded_game_engine=recorder,
        )