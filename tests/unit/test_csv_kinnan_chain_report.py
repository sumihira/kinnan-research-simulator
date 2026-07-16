from __future__ import annotations

import csv
from pathlib import Path

import pytest

from krs.report.csv import CsvExperimentReporter
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
    chain: KinnanChainSnapshot,
) -> GoldfishRunResult:
    return GoldfishRunResult(
        turns_started=5,
        kinnan_activations=chain.activation_count,
        reached_turn_limit=True,
        game_over=False,
        winner=None,
        kinnan_chain=chain,
    )


def create_experiment_result() -> ExperimentResult:
    config = SimulationConfig(
        strategy_name="kinnan-chain",
        games=4,
        max_turns=6,
        seed=12345,
    )

    one_hit = create_chain_snapshot(
        hit_card_ids=("card-1",),
        turn=2,
    )
    two_hit_chain = create_chain_snapshot(
        hit_card_ids=(
            "card-2",
            "card-3",
        ),
        turn=3,
    )
    three_hit_chain = create_chain_snapshot(
        hit_card_ids=(
            "card-4",
            "card-5",
            "card-6",
        ),
        turn=4,
        misses=1,
    )

    game_results = (
        create_game_result(
            KinnanChainSnapshot.empty()
        ),
        create_game_result(one_hit),
        create_game_result(two_hit_chain),
        create_game_result(three_hit_chain),
    )

    return ExperimentResult(
        config=config,
        game_results=game_results,
        summary=SimulationSummary.from_results(
            games_requested=config.games,
            results=game_results,
        ),
    )


def read_summary_row(
    path: Path,
) -> dict[str, str]:
    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1

    return rows[0]


def test_summary_csv_contains_kinnan_chain_counts(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    path = CsvExperimentReporter().write_summary(
        result,
        tmp_path / "summary.csv",
    )

    row = read_summary_row(path)

    assert row["kinnan_chain_games"] == "4"
    assert row["kinnan_activation_games"] == "3"
    assert row["kinnan_chain_games_count"] == "2"
    assert row["kinnan_total_chain_activations"] == "7"
    assert row["kinnan_chain_activations"] == "5"
    assert row["kinnan_max_chain"] == "3"


def test_summary_csv_contains_kinnan_chain_rates(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    path = CsvExperimentReporter().write_summary(
        result,
        tmp_path / "summary.csv",
    )

    row = read_summary_row(path)

    assert float(
        row["kinnan_overall_chain_rate"]
    ) == pytest.approx(0.5)

    assert float(
        row["kinnan_activation_game_chain_rate"]
    ) == pytest.approx(2 / 3)

    assert float(
        row["kinnan_activation_chain_rate"]
    ) == pytest.approx(5 / 7)

    assert float(
        row["kinnan_average_longest_chain"]
    ) == pytest.approx(1.5)


def test_empty_summary_csv_contains_zero_chain_values(
    tmp_path: Path,
) -> None:
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

    path = CsvExperimentReporter().write_summary(
        result,
        tmp_path / "summary.csv",
    )

    row = read_summary_row(path)

    assert row["kinnan_chain_games"] == "0"
    assert row["kinnan_activation_games"] == "0"
    assert row["kinnan_chain_games_count"] == "0"
    assert float(
        row["kinnan_overall_chain_rate"]
    ) == 0.0
    assert float(
        row["kinnan_activation_game_chain_rate"]
    ) == 0.0
    assert row["kinnan_total_chain_activations"] == "0"
    assert row["kinnan_chain_activations"] == "0"
    assert float(
        row["kinnan_activation_chain_rate"]
    ) == 0.0
    assert float(
        row["kinnan_average_longest_chain"]
    ) == 0.0
    assert row["kinnan_max_chain"] == "0"


def test_games_csv_structure_is_unchanged(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    path = CsvExperimentReporter().write_games(
        result,
        tmp_path / "games.csv",
    )

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    assert reader.fieldnames == [
        "game_id",
        "turns_started",
        "kinnan_activations",
        "reached_turn_limit",
        "game_over",
        "winner",
    ]
    assert len(rows) == 4


def test_csv_report_does_not_modify_chain_summary(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    original_chain = result.summary.kinnan_chain

    CsvExperimentReporter().write_summary(
        result,
        tmp_path / "summary.csv",
    )

    assert result.summary.kinnan_chain is original_chain