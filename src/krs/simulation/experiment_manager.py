from __future__ import annotations

from dataclasses import dataclass

from krs.decks.deck import Deck
from krs.simulation.experiment import (
    ExperimentResult,
    SimulationSummary,
)
from krs.simulation.runner import GoldfishRunResult
from krs.simulation.simulator import GoldfishSimulator
from krs.simulation.worker import (
    SimulationGameResult,
    SimulationWorker,
)


@dataclass(slots=True)
class ExperimentManager:
    """
    Runs every game configured for one simulation experiment.

    Version 1 executes games sequentially through SimulationWorker.
    Worker results retain game IDs so future parallel execution can restore
    deterministic result ordering before aggregation.
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

        Worker completion order does not affect ExperimentResult ordering.
        Results are always returned in ascending game_id order.
        """
        worker_results = tuple(
            self._run_game(
                deck,
                game_id=game_id,
                player_id=player_id,
                player_name=player_name,
            )
            for game_id in range(self.simulator.config.games)
        )

        results = self._order_game_results(
            worker_results,
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
    ) -> SimulationGameResult:
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

    @staticmethod
    def _order_game_results(
        worker_results: tuple[SimulationGameResult, ...],
    ) -> tuple[GoldfishRunResult, ...]:
        """
        Return Goldfish results ordered by ascending game_id.

        Duplicate game IDs indicate an invalid experiment result set and are
        rejected before statistics are generated.
        """
        ordered_results = sorted(
            worker_results,
            key=lambda worker_result: worker_result.game_id,
        )

        game_ids = tuple(
            worker_result.game_id
            for worker_result in ordered_results
        )

        if len(set(game_ids)) != len(game_ids):
            raise ValueError(
                "Worker results contain duplicate game_id values."
            )

        return tuple(
            worker_result.result
            for worker_result in ordered_results
        )