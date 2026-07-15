from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from krs.ai.strategy_factory import StrategyFactory
from krs.engine.action_executor import ActionExecutor
from krs.engine.game_engine import GameEngine
from krs.replay.game_engine_recorder import (
    ReplayGameEngineRecorder,
)
from krs.replay.replay import Replay
from krs.simulation.simulation_config import SimulationConfig
from krs.simulation.simulation_config_loader import (
    SimulationConfigLoader,
)


@dataclass(frozen=True, slots=True)
class ReplaySimulationComponents:
    """
    Stores components for one Replay-enabled simulation.

    replay is shared by ActionExecutor and ReplayGameEngineRecorder.
    game_engine retains the original concrete GameEngine for APIs that
    explicitly require it. recorded_game_engine is the lifecycle-recording
    adapter that should be passed to Goldfish execution code.
    """

    config: SimulationConfig
    replay: Replay
    action_executor: ActionExecutor
    game_engine: GameEngine
    recorded_game_engine: ReplayGameEngineRecorder

    def __post_init__(self) -> None:
        if not self.config.save_replays:
            raise ValueError(
                "Replay simulation components require "
                "save_replays=True."
            )

        if self.action_executor.replay is not self.replay:
            raise ValueError(
                "ActionExecutor must use the shared Replay."
            )

        if self.recorded_game_engine.replay is not self.replay:
            raise ValueError(
                "ReplayGameEngineRecorder must use "
                "the shared Replay."
            )

        if self.recorded_game_engine.engine is not self.game_engine:
            raise ValueError(
                "ReplayGameEngineRecorder must wrap "
                "the configured GameEngine."
            )


class ReplaySimulationFactory:
    """
    Builds Replay-enabled simulation components.

    The existing SimulationFactory remains responsible for normal
    simulations. This factory is used only when SimulationConfig has
    save_replays enabled.
    """

    def __init__(
        self,
        *,
        config_loader: SimulationConfigLoader | None = None,
        strategy_factory: StrategyFactory | None = None,
    ) -> None:
        self._config_loader = (
            config_loader
            if config_loader is not None
            else SimulationConfigLoader()
        )
        self._strategy_factory = (
            strategy_factory
            if strategy_factory is not None
            else StrategyFactory()
        )

    def load_config(
        self,
        path: str | Path,
    ) -> SimulationConfig:
        """
        Load one SimulationConfig from YAML.
        """
        return self._config_loader.load(path)

    def create(
        self,
        config: SimulationConfig,
    ) -> ReplaySimulationComponents:
        """
        Create components that share one Replay instance.

        save_replays must be enabled explicitly. This prevents callers from
        accidentally using the more expensive Replay path for ordinary
        simulations.
        """
        if not config.save_replays:
            raise ValueError(
                "Replay simulation requires "
                "save_replays=True."
            )

        replay = Replay()
        action_executor = ActionExecutor(
            replay=replay,
        )

        game_engine = GameEngine.from_strategy(
            config.strategy_name,
            action_executor=action_executor,
            strategy_factory=self._strategy_factory,
        )

        recorded_game_engine = ReplayGameEngineRecorder(
            engine=game_engine,
            replay=replay,
        )

        return ReplaySimulationComponents(
            config=config,
            replay=replay,
            action_executor=action_executor,
            game_engine=game_engine,
            recorded_game_engine=recorded_game_engine,
        )

    def create_from_file(
        self,
        path: str | Path,
    ) -> ReplaySimulationComponents:
        """
        Load configuration and create Replay-enabled components.
        """
        config = self.load_config(path)

        return self.create(config)