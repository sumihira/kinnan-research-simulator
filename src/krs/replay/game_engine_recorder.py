from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from krs.engine.game_engine import GameEngine
from krs.game.game_state import GameState
from krs.game.phase import Phase
from krs.replay.replay import Replay
from krs.replay.replay_event import ReplayEvent


@dataclass(slots=True)
class ReplayGameEngineRecorder:
    """
    Records GameEngine lifecycle events without modifying GameEngine.

    All methods and attributes not implemented by this adapter are delegated
    to the wrapped GameEngine. This preserves existing APIs such as Kinnan
    action creation and automatic Kinnan activation execution.
    """

    engine: GameEngine
    replay: Replay = field(
        default_factory=Replay,
    )

    def start_game(
        self,
        state: GameState,
    ) -> None:
        """
        Start a game through the wrapped engine and record success.

        Failed game starts are not recorded.
        """
        self.engine.start_game(state)

        self._record(
            state=state,
            action="game_start",
            description=(
                f"Started game {state.game_id} with "
                f"{len(state.players)} player(s)."
            ),
        )

    def start_turn(
        self,
        state: GameState,
    ) -> None:
        """
        Start a turn through the wrapped engine and record success.

        Failed turn starts are not recorded.
        """
        self.engine.start_turn(state)

        self._record_turn_start(state)

    def advance_phase(
        self,
        state: GameState,
    ) -> None:
        """
        Delegate phase advancement to the wrapped GameEngine.
        """
        self.engine.advance_phase(state)

    def end_turn(
        self,
        state: GameState,
    ) -> None:
        """
        End the current turn and record the newly started turn.

        GameEngine.end_turn() already calls its own start_turn(). The adapter
        therefore calls only end_turn() and records one turn_start event after
        successful completion, avoiding duplicate lifecycle events.
        """
        self.engine.end_turn(state)

        self._record_turn_start(state)

    def record_game_end(
        self,
        state: GameState,
    ) -> None:
        """
        Record the current finished game state.

        The method intentionally does not mutate GameState. The caller or
        simulation runner remains responsible for setting game_over and winner.
        """
        if not state.started:
            raise ValueError(
                "Cannot record the end of an unstarted game."
            )

        if not state.game_over:
            raise ValueError(
                "Cannot record game end before the game is finished."
            )

        description = (
            f"Game ended. Winner: {state.winner}."
            if state.winner is not None
            else "Game ended without a winner."
        )

        self._record(
            state=state,
            action="game_end",
            description=description,
        )

    def _record_turn_start(
        self,
        state: GameState,
    ) -> None:
        player = state.active_player

        if player is None:
            raise ValueError(
                "Active player could not be resolved."
            )

        self._record(
            state=state,
            action="turn_start",
            description=(
                f"Started turn {state.turn_number} "
                f"for player {player.player_id}."
            ),
        )

    def _record(
        self,
        *,
        state: GameState,
        action: str,
        description: str,
    ) -> None:
        self.replay.add(
            ReplayEvent(
                turn=state.turn_number,
                phase=self._phase_name(state.phase),
                action=action,
                description=description,
            )
        )

    @staticmethod
    def _phase_name(
        phase: Phase,
    ) -> str:
        """
        Return a stable lower-case Replay phase name.
        """
        return phase.name.casefold()

    def __getattr__(
        self,
        name: str,
    ) -> Any:
        """
        Delegate unknown public APIs to the wrapped GameEngine.

        This keeps existing GameEngine functionality available without
        duplicating or replacing its implementation.
        """
        return getattr(
            self.engine,
            name,
        )