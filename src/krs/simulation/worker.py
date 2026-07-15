from __future__ import annotations

from dataclasses import dataclass

from krs.decks.deck import Deck
from krs.simulation.runner import GoldfishRunResult
from krs.simulation.simulator import GoldfishSimulator


@dataclass(frozen=True, slots=True)
class SimulationGameResult:
    """
    Identifies the result produced by one simulation game.

    Keeping game_id with the result allows ExperimentManager to restore
    deterministic game order even when workers later finish out of order.
    """

    game_id: int
    result: GoldfishRunResult

    def __post_init__(self) -> None:
        if self.game_id < 0:
            raise ValueError("game_id must not be negative.")


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
    ) -> SimulationGameResult:
        """
        Execute one Goldfish game through GoldfishSimulator.

        The returned result retains game_id so experiment results can later
        be ordered independently of worker completion order.
        """
        if game_id < 0:
            raise ValueError("game_id must not be negative.")

        result = self.simulator.simulate_game(
            deck,
            game_id=game_id,
            player_id=player_id,
            player_name=player_name,
        )

        return SimulationGameResult(
            game_id=game_id,
            result=result,
        )