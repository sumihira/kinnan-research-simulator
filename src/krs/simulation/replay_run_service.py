from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar

from krs.game.game_state import GameState
from krs.replay.replay_bundle import (
    ReplayBundlePaths,
    ReplayBundleWriter,
)
from krs.simulation.replay_simulation_factory import (
    ReplaySimulationComponents,
)


RunResultT = TypeVar("RunResultT")


@dataclass(frozen=True, slots=True)
class ReplayRunResult:
    """
    Stores the result of one Replay-enabled simulation run.

    run_result is the value returned by the existing Goldfish execution
    function. replay_paths contains every generated Replay report path.
    """

    run_result: object
    replay_paths: ReplayBundlePaths


@dataclass(frozen=True, slots=True)
class ReplayRunService:
    """
    Executes an existing Goldfish run and saves its Replay bundle.

    The service does not depend on the concrete GoldfishRunner signature.
    Instead, callers supply a zero-argument callable containing the existing
    run invocation. This prevents Replay integration from changing Runner
    responsibilities or public APIs.
    """

    bundle_writer: ReplayBundleWriter = field(
        default_factory=ReplayBundleWriter,
    )

    def run(
        self,
        *,
        components: ReplaySimulationComponents,
        state: GameState,
        run_game: Callable[[], RunResultT],
        output_directory: str | Path,
    ) -> ReplayRunResult:
        """
        Execute one game and save its Replay reports.

        The game result is returned unchanged. A game_end lifecycle event is
        recorded only when GameState indicates that the game has finished.

        If the execution callable raises an exception, no Replay bundle is
        written and the exception is propagated unchanged.
        """
        if not callable(run_game):
            raise TypeError(
                "run_game must be callable."
            )

        self._validate_state(
            components=components,
            state=state,
        )

        run_result = run_game()

        if state.game_over:
            self._record_game_end_if_missing(
                components=components,
                state=state,
            )

        replay_paths = self.bundle_writer.write(
            components.replay,
            output_directory,
        )

        return ReplayRunResult(
            run_result=run_result,
            replay_paths=replay_paths,
        )

    @staticmethod
    def _validate_state(
        *,
        components: ReplaySimulationComponents,
        state: GameState,
    ) -> None:
        """
        Validate Replay execution inputs before starting the run.
        """
        if not components.config.save_replays:
            raise ValueError(
                "Replay run requires save_replays=True."
            )

        if state.game_over:
            raise ValueError(
                "Cannot start a Replay run for a finished game."
            )

    @staticmethod
    def _record_game_end_if_missing(
        *,
        components: ReplaySimulationComponents,
        state: GameState,
    ) -> None:
        """
        Record game_end exactly once.

        A custom runner may already record the lifecycle event. The service
        checks the final Replay event to avoid adding a duplicate.
        """
        events = components.replay.events

        if (
            events
            and events[-1].action == "game_end"
        ):
            return

        components.recorded_game_engine.record_game_end(
            state
        )