from __future__ import annotations

from pathlib import Path

from krs.ai.strategy_factory import StrategyFactory
from krs.engine.game_engine import GameEngine
from krs.simulation.simulation_config import SimulationConfig
from krs.simulation.simulation_config_loader import (
    SimulationConfigLoader,
)


class SimulationFactory:
    """
    Builds simulation components from configuration files.
    """

    def __init__(
        self,
        *,
        config_loader: SimulationConfigLoader | None = None,
        strategy_factory: StrategyFactory | None = None,
    ) -> None:
        self._config_loader = (
            config_loader or SimulationConfigLoader()
        )
        self._strategy_factory = (
            strategy_factory or StrategyFactory()
        )

    def load_config(
        self,
        path: str | Path,
    ) -> SimulationConfig:
        return self._config_loader.load(path)

    def create_game_engine(
        self,
        config: SimulationConfig,
    ) -> GameEngine:
        return GameEngine.from_strategy(
            config.strategy_name,
            strategy_factory=self._strategy_factory,
        )

    def create_from_file(
        self,
        path: str | Path,
    ) -> tuple[SimulationConfig, GameEngine]:
        config = self.load_config(path)
        engine = self.create_game_engine(config)

        return config, engine