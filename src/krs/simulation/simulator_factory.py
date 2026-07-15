from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from krs.engine.game_engine import GameEngine
from krs.simulation.game_state_factory import GameStateFactory
from krs.simulation.simulation_config import SimulationConfig
from krs.simulation.simulator import GoldfishSimulator


GameEngineFactory = Callable[[], GameEngine]
GameStateFactoryFactory = Callable[[], GameStateFactory]


@dataclass(frozen=True, slots=True)
class GoldfishSimulatorFactory:
    """
    Creates independent GoldfishSimulator instances.

    Every call to create() builds a new GameEngine and GameStateFactory.
    This prevents mutable simulation components from being shared across
    concurrent games.
    """

    config: SimulationConfig
    game_engine_factory: GameEngineFactory | None = None
    state_factory_factory: GameStateFactoryFactory = field(
        default=GameStateFactory,
    )

    def create(self) -> GoldfishSimulator:
        """Create a fully independent GoldfishSimulator."""
        game_engine = self._create_game_engine()
        state_factory = self.state_factory_factory()

        return GoldfishSimulator(
            config=self.config,
            game_engine=game_engine,
            state_factory=state_factory,
        )

    def _create_game_engine(self) -> GameEngine:
        """Create a new GameEngine for one simulator."""
        if self.game_engine_factory is not None:
            return self.game_engine_factory()

        return GameEngine.from_strategy(
            self.config.strategy_name,
        )