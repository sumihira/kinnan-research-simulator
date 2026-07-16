from __future__ import annotations

import json
from pathlib import Path

import pytest

from krs.report.json import JsonExperimentReporter
from krs.simulation.experiment import (
    ExperimentResult,
    SimulationSummary,
)
from krs.simulation.runner import GoldfishRunResult
from krs.simulation.simulation_config import SimulationConfig
from krs.statistics.kinnan_chain import (
    KinnanChainSnapshot,
    KinnanChainStatistics,
)


def create_chain_snapshot(
    *,
    hit_card_ids: tuple[str, ...] = (),
    turn: int | None = None,
    misses: int = 0,
) -> KinnanChainSnapshot:
    statistics = KinnanChainStatistics()

    for card_id in hit_card_ids:
        statistics.record_hit(
            card_id,
            turn=turn,
        )

    for _ in range(misses):
        statistics.record_miss()

    return statistics.snapshot()


def create_game_result(
    *,
    chain: KinnanChainSnapshot,
    turns_started: int = 5,
) -> GoldfishRunResult:
    return GoldfishRunResult(
        turns_started=turns_started,
        kinnan_activations=chain.activation_count,
        reached_turn_limit=True,
        game_over=False,
        winner=None,
        kinnan_chain=chain,
    )


def create_experiment_result() -> ExperimentResult:
    config = SimulationConfig(
        strategy_name="combo",
        games=4,
        max_turns=6,
        seed=12345,
    )

    game_results = (
        create_game_result(
            chain=KinnanChainSnapshot.empty(),
        ),
        create_game_result(
            chain=create_chain_snapshot(
                hit_card_ids=("card-1",),
                turn=2,
            ),
        ),
        create_game_result(
            chain=create_chain_snapshot(
                hit_card_ids=(
                    "card-2",
                    "card-3",
                ),
                turn=3,
            ),
        ),
        create_game_result(
            chain=create_chain_snapshot(
                hit_card_ids=(
                    "card-4",
                    "card-5",
                    "card-6",
                ),
                turn=4,
                misses=1,
            ),
        ),
    )

    return ExperimentResult(
        config=config,
        game_results=game_results,
        summary=SimulationSummary.from_results(
            games_requested=config.games,
            results=game_results,
        ),
    )


def test_report_contains_kinnan_chain_summary() -> None:
    result = create_experiment_result()

    report = JsonExperimentReporter().to_dict(result)

    chain = report["kinnan_chain"]

    assert chain["games"] == 4
    assert chain["games_with_activation"] == 3
    assert chain["games_with_chain"] == 2
    assert chain["overall_chain_rate"] == pytest.approx(
        0.5
    )
    assert (
        chain["activation_game_chain_rate"]
        == pytest.approx(2 / 3)
    )
    assert chain["total_activations"] == 7
    assert chain["chain_activations"] == 5
    assert chain["activation_chain_rate"] == pytest.approx(
        5 / 7
    )
    assert chain["average_longest_chain"] == pytest.approx(
        1.5
    )
    assert chain["max_chain"] == 3


def test_report_contains_max_chain_distribution() -> None:
    result = create_experiment_result()

    chain = JsonExperimentReporter().to_dict(
        result
    )["kinnan_chain"]

    assert chain["max_chain_distribution"] == [
        {
            "chain_length": 0,
            "games": 1,
        },
        {
            "chain_length": 1,
            "games": 1,
        },
        {
            "chain_length": 2,
            "games": 1,
        },
        {
            "chain_length": 3,
            "games": 1,
        },
    ]


def test_report_contains_first_chain_turns() -> None:
    result = create_experiment_result()

    chain = JsonExperimentReporter().to_dict(
        result
    )["kinnan_chain"]

    assert chain["first_chain_turns"] == [
        3,
        4,
    ]


def test_report_contains_turn_chain_statistics() -> None:
    result = create_experiment_result()

    chain = JsonExperimentReporter().to_dict(
        result
    )["kinnan_chain"]

    assert chain["turn_chain_statistics"] == [
        {
            "turn": 3,
            "chains_started": 1,
            "chains_started_rate": pytest.approx(0.25),
            "chains_through_turn": 1,
            "chain_rate_through_turn": pytest.approx(0.25),
        },
        {
            "turn": 4,
            "chains_started": 1,
            "chains_started_rate": pytest.approx(0.25),
            "chains_through_turn": 2,
            "chain_rate_through_turn": pytest.approx(0.5),
        },
    ]


def test_empty_chain_summary_is_serialized() -> None:
    config = SimulationConfig(
        games=2,
    )

    result = ExperimentResult(
        config=config,
        game_results=(),
        summary=SimulationSummary.from_results(
            games_requested=config.games,
            results=(),
        ),
    )

    chain = JsonExperimentReporter().to_dict(
        result
    )["kinnan_chain"]

    assert chain == {
        "games": 0,
        "games_with_activation": 0,
        "games_with_chain": 0,
        "overall_chain_rate": 0.0,
        "activation_game_chain_rate": 0.0,
        "total_activations": 0,
        "chain_activations": 0,
        "activation_chain_rate": 0.0,
        "average_longest_chain": 0.0,
        "max_chain": 0,
        "max_chain_distribution": [],
        "first_chain_turns": [],
        "turn_chain_statistics": [],
    }


def test_kinnan_chain_report_is_valid_json() -> None:
    result = create_experiment_result()
    reporter = JsonExperimentReporter()

    serialized = reporter.to_json(result)
    decoded = json.loads(serialized)

    assert decoded["kinnan_chain"] == (
        reporter.to_dict(result)["kinnan_chain"]
    )


def test_written_json_contains_kinnan_chain(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    output_path = tmp_path / "experiment.json"

    JsonExperimentReporter().write(
        result,
        output_path,
    )

    decoded = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert decoded["kinnan_chain"]["games"] == 4
    assert (
        decoded["kinnan_chain"]["games_with_chain"]
        == 2
    )


def test_reporter_does_not_modify_chain_summary() -> None:
    result = create_experiment_result()
    original_chain = result.summary.kinnan_chain

    reporter = JsonExperimentReporter()

    reporter.to_dict(result)
    reporter.to_json(result)

    assert result.summary.kinnan_chain is original_chain