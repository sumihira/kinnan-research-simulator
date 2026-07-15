from __future__ import annotations

from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor
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

    A single configured worker executes games sequentially. Two or more
    configured workers execute games through ThreadPoolExecutor.

    Worker results retain game IDs, so completion order never changes the
    deterministic ordering stored in ExperimentResult.
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
        Execute the configured Goldfish games and aggregate their results.
        """
        worker_results = self._execute_games(
            deck,
            player_id=player_id,
            player_name=player_name,
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

    def _execute_games(
        self,
        deck: Deck,
        *,
        player_id: int,
        player_name: str,
    ) -> tuple[SimulationGameResult, ...]:
        """
        Execute games sequentially or concurrently from configuration.
        """
        if self.simulator.config.workers == 1:
            return self._execute_games_sequentially(
                deck,
                player_id=player_id,
                player_name=player_name,
            )

        return self._execute_games_concurrently(
            deck,
            player_id=player_id,
            player_name=player_name,
        )

    def _execute_games_sequentially(
        self,
        deck: Deck,
        *,
        player_id: int,
        player_name: str,
    ) -> tuple[SimulationGameResult, ...]:
        """Execute every configured game on the calling thread."""
        return tuple(
            self._run_game(
                deck,
                game_id=game_id,
                player_id=player_id,
                player_name=player_name,
            )
            for game_id in range(self.simulator.config.games)
        )

    def _execute_games_concurrently(
        self,
        deck: Deck,
        *,
        player_id: int,
        player_name: str,
    ) -> tuple[SimulationGameResult, ...]:
        """
        Execute configured games through ThreadPoolExecutor.

        Results are collected in submission order here, but final ordering
        is still normalized by game_id before aggregation.
        """
        with ThreadPoolExecutor(
            max_workers=self.simulator.config.workers,
        ) as executor:
            futures = tuple(
                self._submit_game(
                    executor,
                    deck,
                    game_id=game_id,
                    player_id=player_id,
                    player_name=player_name,
                )
                for game_id in range(
                    self.simulator.config.games
                )
            )

            return tuple(
                future.result()
                for future in futures
            )

    def _submit_game(
        self,
        executor: ThreadPoolExecutor,
        deck: Deck,
        *,
        game_id: int,
        player_id: int,
        player_name: str,
    ) -> Future[SimulationGameResult]:
        """Submit one SimulationWorker execution to the executor."""
        return executor.submit(
            self._run_game,
            deck,
            game_id=game_id,
            player_id=player_id,
            player_name=player_name,
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