from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from krs.simulation.runner import GoldfishRunResult
from krs.simulation.simulation_config import SimulationConfig


@dataclass(frozen=True, slots=True)
class SimulationSummary:
    """
    Aggregated statistics for one simulation experiment.

    A game is counted as a win when it finished and has a winner.
    Games without a winner are counted as non-winning games.
    """

    games_requested: int
    games_completed: int
    wins: int
    non_wins: int
    turn_limit_games: int
    total_turns_started: int
    total_kinnan_activations: int
    fastest_win_turn: int | None

    def __post_init__(self) -> None:
        if self.games_requested < 1:
            raise ValueError(
                "games_requested must be at least 1."
            )

        if self.games_completed < 0:
            raise ValueError(
                "games_completed must not be negative."
            )

        if self.games_completed > self.games_requested:
            raise ValueError(
                "games_completed must not exceed games_requested."
            )

        if self.wins < 0:
            raise ValueError("wins must not be negative.")

        if self.non_wins < 0:
            raise ValueError("non_wins must not be negative.")

        if self.wins + self.non_wins != self.games_completed:
            raise ValueError(
                "wins and non_wins must equal games_completed."
            )

        if self.turn_limit_games < 0:
            raise ValueError(
                "turn_limit_games must not be negative."
            )

        if self.turn_limit_games > self.games_completed:
            raise ValueError(
                "turn_limit_games must not exceed games_completed."
            )

        if self.total_turns_started < 0:
            raise ValueError(
                "total_turns_started must not be negative."
            )

        if self.total_kinnan_activations < 0:
            raise ValueError(
                "total_kinnan_activations must not be negative."
            )

        if (
            self.fastest_win_turn is not None
            and self.fastest_win_turn < 1
        ):
            raise ValueError(
                "fastest_win_turn must be at least 1."
            )

    @property
    def win_rate(self) -> float:
        """Return the win rate from 0.0 through 1.0."""
        if self.games_completed == 0:
            return 0.0

        return self.wins / self.games_completed

    @property
    def average_turns_started(self) -> float:
        """Return average turns started per completed game."""
        if self.games_completed == 0:
            return 0.0

        return self.total_turns_started / self.games_completed

    @property
    def average_kinnan_activations(self) -> float:
        """Return average Kinnan activations per completed game."""
        if self.games_completed == 0:
            return 0.0

        return (
            self.total_kinnan_activations
            / self.games_completed
        )

    @classmethod
    def from_results(
        cls,
        *,
        games_requested: int,
        results: tuple[GoldfishRunResult, ...],
    ) -> Self:
        """Create aggregate statistics from Goldfish results."""
        wins = sum(
            1
            for result in results
            if result.game_over and result.winner is not None
        )

        winning_turns = [
            result.turns_started
            for result in results
            if result.game_over and result.winner is not None
        ]

        games_completed = len(results)

        return cls(
            games_requested=games_requested,
            games_completed=games_completed,
            wins=wins,
            non_wins=games_completed - wins,
            turn_limit_games=sum(
                1
                for result in results
                if result.reached_turn_limit
            ),
            total_turns_started=sum(
                result.turns_started
                for result in results
            ),
            total_kinnan_activations=sum(
                result.kinnan_activations
                for result in results
            ),
            fastest_win_turn=(
                min(winning_turns)
                if winning_turns
                else None
            ),
        )


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    """
    Complete output of one simulation experiment.

    Individual game results are retained so later statistics and replay
    features can inspect each game without rerunning the experiment.
    """

    config: SimulationConfig
    game_results: tuple[GoldfishRunResult, ...]
    summary: SimulationSummary

    def __post_init__(self) -> None:
        if len(self.game_results) != self.summary.games_completed:
            raise ValueError(
                "game_results count must equal games_completed."
            )

        if self.config.games != self.summary.games_requested:
            raise ValueError(
                "config.games must equal games_requested."
            )