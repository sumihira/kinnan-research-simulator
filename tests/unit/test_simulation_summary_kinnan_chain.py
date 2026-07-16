from __future__ import annotations

import pytest

from krs.simulation.experiment import SimulationSummary
from krs.simulation.runner import GoldfishRunResult
from krs.statistics.kinnan_chain import (
    KinnanChainSnapshot,
    KinnanChainStatistics,
    KinnanChainSummary,
)


def create_result(
    *,
    turns_started: int = 3,
    kinnan_activations: int = 0,
    reached_turn_limit: bool = False,
    game_over: bool = False,
    winner: str | None = None,
    kinnan_chain: KinnanChainSnapshot | None = None,
) -> GoldfishRunResult:
    return GoldfishRunResult(
        turns_started=turns_started,
        kinnan_activations=kinnan_activations,
        reached_turn_limit=reached_turn_limit,
        game_over=game_over,
        winner=winner,
        kinnan_chain=(
            kinnan_chain
            if kinnan_chain is not None
            else KinnanChainSnapshot.empty()
        ),
    )


def create_chain_snapshot(
    *,
    card_ids: tuple[str, ...],
    turn: int,
) -> KinnanChainSnapshot:
    statistics = KinnanChainStatistics()

    for card_id in card_ids:
        statistics.record_hit(
            card_id,
            turn=turn,
        )

    return statistics.snapshot()


def test_summary_aggregates_kinnan_chain_snapshots() -> None:
    no_activation = create_result()

    one_hit_statistics = KinnanChainStatistics()
    one_hit_statistics.record_hit(
        "card-1",
        turn=2,
    )

    two_hit_chain = create_chain_snapshot(
        card_ids=(
            "card-2",
            "card-3",
        ),
        turn=3,
    )

    three_hit_chain = create_chain_snapshot(
        card_ids=(
            "card-4",
            "card-5",
            "card-6",
        ),
        turn=4,
    )

    results = (
        no_activation,
        create_result(
            kinnan_activations=1,
            kinnan_chain=one_hit_statistics.snapshot(),
        ),
        create_result(
            kinnan_activations=2,
            kinnan_chain=two_hit_chain,
        ),
        create_result(
            kinnan_activations=3,
            kinnan_chain=three_hit_chain,
        ),
    )

    summary = SimulationSummary.from_results(
        games_requested=4,
        results=results,
    )

    assert summary.kinnan_chain.games == 4
    assert (
        summary.kinnan_chain.games_with_activation
        == 3
    )
    assert summary.kinnan_chain.games_with_chain == 2
    assert summary.kinnan_chain.total_activations == 6
    assert summary.kinnan_chain.chain_activations == 5
    assert (
        summary.kinnan_chain.average_longest_chain
        == pytest.approx(1.5)
    )
    assert summary.kinnan_chain.max_chain == 3
    assert (
        summary.kinnan_chain.max_chain_distribution
        == (
            (0, 1),
            (1, 1),
            (2, 1),
            (3, 1),
        )
    )
    assert summary.kinnan_chain.first_chain_turns == (
        3,
        4,
    )
    assert summary.kinnan_chain.turn_chain_counts == (
        (3, 1),
        (4, 1),
    )


def test_summary_calculates_kinnan_chain_rates() -> None:
    chain = create_chain_snapshot(
        card_ids=(
            "card-1",
            "card-2",
        ),
        turn=2,
    )

    miss_statistics = KinnanChainStatistics()
    miss_statistics.record_miss()

    results = (
        create_result(
            kinnan_activations=2,
            kinnan_chain=chain,
        ),
        create_result(
            kinnan_activations=1,
            kinnan_chain=miss_statistics.snapshot(),
        ),
        create_result(),
    )

    summary = SimulationSummary.from_results(
        games_requested=3,
        results=results,
    )

    assert (
        summary.kinnan_chain.overall_chain_rate
        == pytest.approx(1 / 3)
    )
    assert (
        summary.kinnan_chain.activation_game_chain_rate
        == pytest.approx(1 / 2)
    )
    assert (
        summary.kinnan_chain.activation_chain_rate
        == pytest.approx(2 / 3)
    )


def test_summary_calculates_turn_chain_rates() -> None:
    turn_two = create_chain_snapshot(
        card_ids=(
            "card-1",
            "card-2",
        ),
        turn=2,
    )
    turn_four = create_chain_snapshot(
        card_ids=(
            "card-3",
            "card-4",
        ),
        turn=4,
    )

    summary = SimulationSummary.from_results(
        games_requested=3,
        results=(
            create_result(
                kinnan_activations=2,
                kinnan_chain=turn_two,
            ),
            create_result(
                kinnan_activations=2,
                kinnan_chain=turn_four,
            ),
            create_result(),
        ),
    )

    assert (
        summary.kinnan_chain.chain_count_through_turn(1)
        == 0
    )
    assert (
        summary.kinnan_chain.chain_count_through_turn(2)
        == 1
    )
    assert (
        summary.kinnan_chain.chain_count_through_turn(3)
        == 1
    )
    assert (
        summary.kinnan_chain.chain_count_through_turn(4)
        == 2
    )
    assert (
        summary.kinnan_chain.chain_rate_through_turn(2)
        == pytest.approx(1 / 3)
    )
    assert (
        summary.kinnan_chain.chain_rate_through_turn(4)
        == pytest.approx(2 / 3)
    )


def test_empty_results_create_empty_chain_summary() -> None:
    summary = SimulationSummary.from_results(
        games_requested=5,
        results=(),
    )

    assert summary.games_completed == 0
    assert summary.kinnan_chain == KinnanChainSummary.empty()


def test_direct_summary_construction_defaults_to_empty_chain() -> None:
    summary = SimulationSummary(
        games_requested=1,
        games_completed=1,
        wins=0,
        non_wins=1,
        turn_limit_games=1,
        total_turns_started=5,
        total_kinnan_activations=0,
        fastest_win_turn=None,
    )

    assert summary.kinnan_chain == KinnanChainSummary.empty()


def test_summary_accepts_matching_chain_game_count() -> None:
    chain_summary = KinnanChainSummary.from_games(
        (
            KinnanChainSnapshot.empty(),
            KinnanChainSnapshot.empty(),
        )
    )

    summary = SimulationSummary(
        games_requested=2,
        games_completed=2,
        wins=0,
        non_wins=2,
        turn_limit_games=2,
        total_turns_started=10,
        total_kinnan_activations=0,
        fastest_win_turn=None,
        kinnan_chain=chain_summary,
    )

    assert summary.kinnan_chain.games == 2


def test_summary_rejects_mismatched_chain_game_count() -> None:
    chain_summary = KinnanChainSummary.from_games(
        (
            KinnanChainSnapshot.empty(),
        )
    )

    with pytest.raises(
        ValueError,
        match=(
            "kinnan_chain.games must be zero or equal "
            "games_completed"
        ),
    ):
        SimulationSummary(
            games_requested=2,
            games_completed=2,
            wins=0,
            non_wins=2,
            turn_limit_games=2,
            total_turns_started=10,
            total_kinnan_activations=0,
            fastest_win_turn=None,
            kinnan_chain=chain_summary,
        )


def test_chain_summary_is_immutable_through_simulation_summary() -> None:
    summary = SimulationSummary.from_results(
        games_requested=1,
        results=(
            create_result(),
        ),
    )

    with pytest.raises(AttributeError):
        summary.kinnan_chain.games = 2  # type: ignore[misc]