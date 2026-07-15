from __future__ import annotations

from dataclasses import dataclass

from krs.decks.deck import Deck
from krs.simulation.experiment import (
    ExperimentResult,
    SimulationSummary,
)
from krs.simulation.runner import GoldfishRunResult
from krs.simulation.simulator import GoldfishSimulator
from krs.simulation.worker import SimulationWorker


@dataclass(slots=True)
class ExperimentManager:
    """
    Runs every game configured for one simulation experiment.

    Version 1 executes games sequentially through SimulationWorker.
    The worker boundary allows parallel execution to be added later without
    changing ExperimentResult or SimulationSummary.
    """

    simulator: GoldfishSimulator
    worker: SimulationWorker | None = None

    def __post_init__(self) -> None:
        if self.worker is None:
            self.worker = SimulationWorker(
                simulator=self.simulator,
            )

    def run(
        self,
        deck: Deck,
        *,
        player_id: int = 0,
        player_name: str = "Player",
    ) -> ExperimentResult:
        """
        Execute config.games Goldfish games and aggregate the results.
        """
        results = tuple(
            self._run_game(
                deck,
                game_id=game_id,
                player_id=player_id,
                player_name=player_name,
            )
            for game_id in range(self.simulator.config.games)
        )

        summary = SimulationSummary.from_results(
            games_requested=self.simulator.config.games,
            results=results,
        )

        return ExperimentResult(
            config=self.simulator.config,
            game_results=results,
            summary=summary,
        )

    def _run_game(
        self,
        deck: Deck,
        *,
        game_id: int,
        player_id: int,
        player_name: str,
    ) -> GoldfishRunResult:
        """Execute one game through the configured SimulationWorker."""
        worker = self.worker

        if worker is None:
            raise RuntimeError(
                "SimulationWorker has not been initialized."
            )

        return worker.run_game(
            deck,
            game_id=game_id,
            player_id=player_id,
            player_name=player_name,
        )