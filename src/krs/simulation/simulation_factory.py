from __future__ import annotations

from pathlib import Path

from krs.ai.strategy_factory import StrategyFactory
from krs.engine.game_engine import GameEngine
from krs.simulation.experiment_manager import ExperimentManager
from krs.simulation.monte_carlo import MonteCarloSimulator
from krs.simulation.simulation_config import SimulationConfig
from krs.simulation.simulation_config_loader import (
    SimulationConfigLoader,
)
from krs.simulation.simulator import GoldfishSimulator
from krs.simulation.simulator_factory import (
    GoldfishSimulatorFactory,
)


class SimulationFactory:
    """
    Builds simulation components from configuration.

    The factory acts as the simulation composition root. It creates
    configuration, engines, simulators, experiment management, and the
    public Monte Carlo entry point.
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
        """Load one SimulationConfig from YAML."""
        return self._config_loader.load(path)

    def create_game_engine(
        self,
        config: SimulationConfig,
    ) -> GameEngine:
        """Create a strategy-configured GameEngine."""
        return GameEngine.from_strategy(
            config.strategy_name,
            strategy_factory=self._strategy_factory,
        )

    def create_simulator_factory(
        self,
        config: SimulationConfig,
    ) -> GoldfishSimulatorFactory:
        """
        Create a factory that builds isolated Goldfish simulators.

        Every generated simulator receives a fresh GameEngine configured
        through this SimulationFactory's StrategyFactory.
        """
        return GoldfishSimulatorFactory(
            config=config,
            game_engine_factory=(
                lambda: self.create_game_engine(config)
            ),
        )

    def create_goldfish_simulator(
        self,
        config: SimulationConfig,
    ) -> GoldfishSimulator:
        """Create one GoldfishSimulator."""
        simulator_factory = self.create_simulator_factory(
            config,
        )

        return simulator_factory.create()

    def create_experiment_manager(
        self,
        config: SimulationConfig,
    ) -> ExperimentManager:
        """
        Create an ExperimentManager for sequential or parallel execution.
        """
        simulator_factory = self.create_simulator_factory(
            config,
        )
        simulator = simulator_factory.create()

        return ExperimentManager(
            simulator=simulator,
            simulator_factory=simulator_factory,
        )

    def create_monte_carlo_simulator(
        self,
        config: SimulationConfig,
    ) -> MonteCarloSimulator:
        """Create the public Monte Carlo simulation entry point."""
        experiment_manager = self.create_experiment_manager(
            config,
        )

        return MonteCarloSimulator(
            experiment_manager=experiment_manager,
        )

    def create_from_file(
        self,
        path: str | Path,
    ) -> tuple[SimulationConfig, GameEngine]:
        """
        Load configuration and create a GameEngine.

        This method is retained for compatibility with existing callers.
        """
        config = self.load_config(path)
        engine = self.create_game_engine(config)

        return config, engine

    def create_monte_carlo_from_file(
        self,
        path: str | Path,
    ) -> tuple[SimulationConfig, MonteCarloSimulator]:
        """
        Load configuration and create a complete Monte Carlo simulator.
        """
        config = self.load_config(path)
        simulator = self.create_monte_carlo_simulator(
            config,
        )

        return config, simulator