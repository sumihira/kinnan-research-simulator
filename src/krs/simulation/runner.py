from __future__ import annotations

from dataclasses import dataclass, field

from krs.engine.game_engine import GameEngine
from krs.game.game_state import GameState
from krs.game.phase import Phase
from krs.statistics.kinnan_chain import (
    KinnanChainSnapshot,
)


@dataclass(frozen=True, slots=True)
class GoldfishRunResult:
    """
    Stores the result of one Goldfish execution.

    The result is immutable so simulation callers can safely retain it
    without depending on later GameState mutations.
    """

    turns_started: int
    kinnan_activations: int
    reached_turn_limit: bool
    game_over: bool
    winner: str | None
    kinnan_chain: KinnanChainSnapshot = field(
        default_factory=KinnanChainSnapshot.empty,
    )


@dataclass(slots=True)
class GoldfishRunner:
    """
    Runs the minimum Goldfish turn loop.

    The runner coordinates GameEngine operations. It does not directly
    execute Actions or modify player zones.

    Kinnan activations are limited per turn so an incorrectly configured
    state or mocked engine cannot cause an infinite loop.
    """

    game_engine: GameEngine
    max_turns: int = 10
    max_kinnan_activations_per_turn: int = 100

    def __post_init__(self) -> None:
        if self.max_turns < 1:
            raise ValueError(
                "max_turns must be at least 1."
            )

        if self.max_kinnan_activations_per_turn < 1:
            raise ValueError(
                "max_kinnan_activations_per_turn "
                "must be at least 1."
            )

    def run(
        self,
        state: GameState,
    ) -> GoldfishRunResult:
        """
        Run one Goldfish game.

        An unstarted game is started through GameEngine. A started game may
        also be resumed, provided it has not already finished.

        The final allowed turn is played through its END phase. The runner
        does not call end_turn after that turn because doing so would advance
        GameState.turn_number beyond max_turns.
        """
        self._validate_state(state)

        if not state.started:
            self.game_engine.start_game(state)
            self.game_engine.start_turn(state)

        turns_started = 0
        kinnan_activations = 0

        while (
            not state.game_over
            and state.turn_number <= self.max_turns
        ):
            turns_started += 1

            self._advance_to_main_phase(state)

            if state.game_over:
                break

            kinnan_activations += (
                self._execute_main_phase(state)
            )

            if state.game_over:
                break

            self._advance_to_end_phase(state)

            if state.game_over:
                break

            if state.turn_number >= self.max_turns:
                break

            self.game_engine.end_turn(state)

        return GoldfishRunResult(
            turns_started=turns_started,
            kinnan_activations=kinnan_activations,
            reached_turn_limit=(
                not state.game_over
                and state.turn_number >= self.max_turns
            ),
            game_over=state.game_over,
            winner=state.winner,
            kinnan_chain=state.kinnan_chain.snapshot(),
        )

    @staticmethod
    def _validate_state(
        state: GameState,
    ) -> None:
        if not state.players:
            raise ValueError(
                "Cannot run a Goldfish game without players."
            )

        if state.game_over:
            raise ValueError(
                "Cannot run a Goldfish game that has "
                "already finished."
            )

    def _advance_to_main_phase(
        self,
        state: GameState,
    ) -> None:
        """
        Advance the current turn to MAIN.

        A resumed game may already be in MAIN. Resuming from END is rejected
        because that turn has already completed.
        """
        if state.phase is Phase.END:
            raise ValueError(
                "Cannot resume a Goldfish turn from END phase."
            )

        while (
            not state.game_over
            and state.phase is not Phase.MAIN
        ):
            self.game_engine.advance_phase(state)

    def _execute_main_phase(
        self,
        state: GameState,
    ) -> int:
        """
        Execute automatic actions during the main phase.

        The active player first attempts to play one land. Kinnan
        activations are then executed while they remain available.

        Returns the number of Kinnan activations executed during this
        main phase.
        """
        player = state.active_player

        if player is None:
            raise ValueError(
                "Active player could not be resolved."
            )

        self.game_engine.execute_land_play_if_available(
            state,
            player_id=player.player_id,
        )

        activation_count = 0

        while (
            not state.game_over
            and activation_count
            < self.max_kinnan_activations_per_turn
        ):
            executed = (
                self.game_engine
                .execute_kinnan_activation_if_available(
                    state,
                    player_id=player.player_id,
                )
            )

            if not executed:
                break

            activation_count += 1

        return activation_count

    def _advance_to_end_phase(
        self,
        state: GameState,
    ) -> None:
        """Advance the current turn from MAIN to END."""
        while (
            not state.game_over
            and state.phase is not Phase.END
        ):
            self.game_engine.advance_phase(state)