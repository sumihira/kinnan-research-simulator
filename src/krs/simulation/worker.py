from __future__ import annotations

from dataclasses import dataclass

from krs.decks.deck import Deck
from krs.simulation.runner import GoldfishRunResult
from krs.simulation.simulator import GoldfishSimulator


@dataclass(slots=True)
class SimulationWorker:
    """
    Executes one independent Goldfish simulation game.

    The worker provides a stable single-game execution boundary for both
    sequential and future parallel experiment execution.
    """

    simulator: GoldfishSimulator

    def run_game(
        self,
        deck: Deck,
        *,
        game_id: int,
        player_id: int = 0,
        player_name: str = "Player",
    ) -> GoldfishRunResult:
        """
        Execute one Goldfish game through GoldfishSimulator.

        Each game ID is passed unchanged to the simulator so deterministic
        per-game seed derivation remains stable.
        """
        if game_id < 0:
            raise ValueError("game_id must not be negative.")

        return self.simulator.simulate_game(
            deck,
            game_id=game_id,
            player_id=player_id,
            player_name=player_name,
        )