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
from krs.simulation.simulator_factory import (
    GoldfishSimulatorFactory,
)
from krs.simulation.worker import (
    SimulationGameResult,
    SimulationWorker,
)


@dataclass(slots=True)
class ExperimentManager:
    """
    Runs every game configured for one simulation experiment.

    Sequential execution may use an injected shared worker.

    Concurrent execution creates an independent simulator and worker for
    every game through GoldfishSimulatorFactory. This prevents GameEngine
    and other mutable runtime components from being shared across threads.
    """

    simulator: GoldfishSimulator
    worker: SimulationWorker | None = None
    simulator_factory: GoldfishSimulatorFactory | None = None

    def __post_init__(self) -> None:
        if self.worker is None:
            self.worker = SimulationWorker(
                simulator=self.simulator,
            )

        if self.simulator_factory is None:
            self.simulator_factory = GoldfishSimulatorFactory(
                config=self.simulator.config,
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
            self._run_game_with_shared_worker(
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
        Execute games through independent per-game workers.

        Every submitted task creates its own GoldfishSimulator, GameEngine,
        GameStateFactory, and SimulationWorker.
        """
        with ThreadPoolExecutor(
            max_workers=self.simulator.config.workers,
        ) as executor:
            futures = tuple(
                self._submit_isolated_game(
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

    def _submit_isolated_game(
        self,
        executor: ThreadPoolExecutor,
        deck: Deck,
        *,
        game_id: int,
        player_id: int,
        player_name: str,
    ) -> Future[SimulationGameResult]:
        """Submit one isolated game execution to the executor."""
        return executor.submit(
            self._run_game_with_isolated_worker,
            deck,
            game_id=game_id,
            player_id=player_id,
            player_name=player_name,
        )

    def _run_game_with_shared_worker(
        self,
        deck: Deck,
        *,
        game_id: int,
        player_id: int,
        player_name: str,
    ) -> SimulationGameResult:
        """
        Execute one sequential game with the configured shared worker.
        """
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

    def _run_game_with_isolated_worker(
        self,
        deck: Deck,
        *,
        game_id: int,
        player_id: int,
        player_name: str,
    ) -> SimulationGameResult:
        """
        Create an isolated simulator and worker, then execute one game.
        """
        simulator_factory = self.simulator_factory

        if simulator_factory is None:
            raise RuntimeError(
                "GoldfishSimulatorFactory has not been initialized."
            )

        simulator = simulator_factory.create()
        worker = SimulationWorker(
            simulator=simulator,
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