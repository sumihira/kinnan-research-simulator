from __future__ import annotations

import pytest

from krs.simulation.experiment import (
    ExperimentResult,
    SimulationSummary,
)
from krs.simulation.runner import GoldfishRunResult
from krs.simulation.simulation_config import SimulationConfig


def create_result(
    *,
    turns_started: int = 3,
    kinnan_activations: int = 0,
    reached_turn_limit: bool = False,
    game_over: bool = False,
    winner: str | None = None,
) -> GoldfishRunResult:
    return GoldfishRunResult(
        turns_started=turns_started,
        kinnan_activations=kinnan_activations,
        reached_turn_limit=reached_turn_limit,
        game_over=game_over,
        winner=winner,
    )


def test_summary_aggregates_game_results() -> None:
    results = (
        create_result(
            turns_started=3,
            kinnan_activations=2,
            game_over=True,
            winner="Player",
        ),
        create_result(
            turns_started=5,
            kinnan_activations=1,
            game_over=True,
            winner="Player",
        ),
        create_result(
            turns_started=6,
            kinnan_activations=0,
            reached_turn_limit=True,
        ),
    )

    summary = SimulationSummary.from_results(
        games_requested=3,
        results=results,
    )

    assert summary.games_requested == 3
    assert summary.games_completed == 3
    assert summary.wins == 2
    assert summary.non_wins == 1
    assert summary.turn_limit_games == 1
    assert summary.total_turns_started == 14
    assert summary.total_kinnan_activations == 3
    assert summary.fastest_win_turn == 3


def test_summary_calculates_rates_and_averages() -> None:
    results = (
        create_result(
            turns_started=2,
            kinnan_activations=1,
            game_over=True,
            winner="Player",
        ),
        create_result(
            turns_started=4,
            kinnan_activations=3,
        ),
    )

    summary = SimulationSummary.from_results(
        games_requested=2,
        results=results,
    )

    assert summary.win_rate == pytest.approx(0.5)
    assert summary.average_turns_started == pytest.approx(3.0)
    assert summary.average_kinnan_activations == pytest.approx(
        2.0
    )


def test_summary_treats_game_over_without_winner_as_non_win() -> None:
    results = (
        create_result(
            game_over=True,
            winner=None,
        ),
    )

    summary = SimulationSummary.from_results(
        games_requested=1,
        results=results,
    )

    assert summary.wins == 0
    assert summary.non_wins == 1
    assert summary.fastest_win_turn is None


def test_summary_returns_zero_for_empty_completed_results() -> None:
    summary = SimulationSummary.from_results(
        games_requested=3,
        results=(),
    )

    assert summary.games_completed == 0
    assert summary.win_rate == 0.0
    assert summary.average_turns_started == 0.0
    assert summary.average_kinnan_activations == 0.0
    assert summary.fastest_win_turn is None


def test_summary_is_immutable() -> None:
    summary = SimulationSummary.from_results(
        games_requested=1,
        results=(
            create_result(),
        ),
    )

    with pytest.raises(AttributeError):
        summary.wins = 1  # type: ignore[misc]


def test_summary_rejects_completed_count_above_requested() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "games_completed must not exceed "
            "games_requested."
        ),
    ):
        SimulationSummary(
            games_requested=1,
            games_completed=2,
            wins=0,
            non_wins=2,
            turn_limit_games=0,
            total_turns_started=0,
            total_kinnan_activations=0,
            fastest_win_turn=None,
        )


def test_summary_rejects_inconsistent_win_counts() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "wins and non_wins must equal "
            "games_completed."
        ),
    ):
        SimulationSummary(
            games_requested=3,
            games_completed=3,
            wins=2,
            non_wins=0,
            turn_limit_games=0,
            total_turns_started=0,
            total_kinnan_activations=0,
            fastest_win_turn=None,
        )


def test_experiment_result_accepts_matching_data() -> None:
    config = SimulationConfig(
        games=2,
    )
    game_results = (
        create_result(),
        create_result(),
    )
    summary = SimulationSummary.from_results(
        games_requested=2,
        results=game_results,
    )

    result = ExperimentResult(
        config=config,
        game_results=game_results,
        summary=summary,
    )

    assert result.config is config
    assert result.game_results is game_results
    assert result.summary is summary


def test_experiment_result_rejects_result_count_mismatch() -> None:
    config = SimulationConfig(
        games=2,
    )
    game_results = (
        create_result(),
    )
    summary = SimulationSummary.from_results(
        games_requested=2,
        results=(
            create_result(),
            create_result(),
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "game_results count must equal "
            "games_completed."
        ),
    ):
        ExperimentResult(
            config=config,
            game_results=game_results,
            summary=summary,
        )


def test_experiment_result_rejects_config_games_mismatch() -> None:
    config = SimulationConfig(
        games=3,
    )
    game_results = (
        create_result(),
        create_result(),
    )
    summary = SimulationSummary.from_results(
        games_requested=2,
        results=game_results,
    )

    with pytest.raises(
        ValueError,
        match=(
            "config.games must equal "
            "games_requested."
        ),
    ):
        ExperimentResult(
            config=config,
            game_results=game_results,
            summary=summary,
        )