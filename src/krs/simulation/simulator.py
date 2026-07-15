from __future__ import annotations

from dataclasses import dataclass, field

from krs.decks.deck import Deck
from krs.engine.game_engine import GameEngine
from krs.simulation.game_state_factory import GameStateFactory
from krs.simulation.runner import (
    GoldfishRunner,
    GoldfishRunResult,
)
from krs.simulation.seed import derive_game_seed
from krs.simulation.simulation_config import SimulationConfig


@dataclass(slots=True)
class GoldfishSimulator:
    """
    Coordinates the components required to execute one Goldfish game.

    GoldfishSimulator creates a fresh GameState for each game and delegates
    the actual turn loop to GoldfishRunner.
    """

    config: SimulationConfig
    game_engine: GameEngine
    state_factory: GameStateFactory = field(
        default_factory=GameStateFactory,
    )

    def simulate_game(
        self,
        deck: Deck,
        *,
        game_id: int = 0,
        player_id: int = 0,
        player_name: str = "Player",
    ) -> GoldfishRunResult:
        """
        Create and execute one Goldfish game.

        The per-game seed is derived from SimulationConfig.seed and game_id.
        A new GameState and GoldfishRunner are created for every call.
        """
        game_seed = derive_game_seed(
            self.config.seed,
            game_id,
        )

        state = self.state_factory.create_goldfish_state(
            deck,
            game_id=game_id,
            seed=game_seed,
            player_id=player_id,
            player_name=player_name,
        )

        runner = GoldfishRunner(
            game_engine=self.game_engine,
            max_turns=self.config.max_turns,
        )

        return runner.run(state)