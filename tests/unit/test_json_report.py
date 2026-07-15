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


def create_game_result(
    *,
    turns_started: int,
    kinnan_activations: int,
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


def create_experiment_result() -> ExperimentResult:
    config = SimulationConfig(
        strategy_name="combo",
        games=3,
        max_turns=8,
        seed=12345,
        mulligan_enabled=False,
        save_replays=True,
        workers=4,
    )

    game_results = (
        create_game_result(
            turns_started=3,
            kinnan_activations=2,
            game_over=True,
            winner="Player",
        ),
        create_game_result(
            turns_started=5,
            kinnan_activations=1,
            game_over=True,
            winner="Player",
        ),
        create_game_result(
            turns_started=8,
            kinnan_activations=0,
            reached_turn_limit=True,
        ),
    )

    summary = SimulationSummary.from_results(
        games_requested=config.games,
        results=game_results,
    )

    return ExperimentResult(
        config=config,
        game_results=game_results,
        summary=summary,
    )


def test_to_dict_contains_config() -> None:
    result = create_experiment_result()
    reporter = JsonExperimentReporter()

    report = reporter.to_dict(result)

    assert report["config"] == {
        "strategy_name": "combo",
        "games": 3,
        "max_turns": 8,
        "seed": 12345,
        "mulligan_enabled": False,
        "save_replays": True,
        "workers": 4,
    }


def test_to_dict_contains_summary() -> None:
    result = create_experiment_result()
    reporter = JsonExperimentReporter()

    report = reporter.to_dict(result)

    assert report["summary"] == {
        "games_requested": 3,
        "games_completed": 3,
        "wins": 2,
        "non_wins": 1,
        "win_rate": pytest.approx(2 / 3),
        "turn_limit_games": 1,
        "total_turns_started": 16,
        "average_turns_started": pytest.approx(16 / 3),
        "total_kinnan_activations": 3,
        "average_kinnan_activations": pytest.approx(1.0),
        "fastest_win_turn": 3,
    }


def test_to_dict_contains_ordered_game_results() -> None:
    result = create_experiment_result()
    reporter = JsonExperimentReporter()

    report = reporter.to_dict(result)

    assert report["games"] == [
        {
            "game_id": 0,
            "turns_started": 3,
            "kinnan_activations": 2,
            "reached_turn_limit": False,
            "game_over": True,
            "winner": "Player",
        },
        {
            "game_id": 1,
            "turns_started": 5,
            "kinnan_activations": 1,
            "reached_turn_limit": False,
            "game_over": True,
            "winner": "Player",
        },
        {
            "game_id": 2,
            "turns_started": 8,
            "kinnan_activations": 0,
            "reached_turn_limit": True,
            "game_over": False,
            "winner": None,
        },
    ]


def test_to_json_returns_valid_json() -> None:
    result = create_experiment_result()
    reporter = JsonExperimentReporter()

    serialized = reporter.to_json(result)
    decoded = json.loads(serialized)

    assert decoded == reporter.to_dict(result)


def test_to_json_preserves_unicode() -> None:
    config = SimulationConfig(
        games=1,
    )
    game_results = (
        create_game_result(
            turns_started=2,
            kinnan_activations=1,
            game_over=True,
            winner="プレイヤー",
        ),
    )
    result = ExperimentResult(
        config=config,
        game_results=game_results,
        summary=SimulationSummary.from_results(
            games_requested=1,
            results=game_results,
        ),
    )

    serialized = JsonExperimentReporter().to_json(result)

    assert "プレイヤー" in serialized
    assert "\\u30d7" not in serialized


def test_write_creates_json_file(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = JsonExperimentReporter()

    output_path = tmp_path / "experiment.json"

    returned_path = reporter.write(
        result,
        output_path,
    )

    assert returned_path == output_path
    assert output_path.exists()

    decoded = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert decoded == reporter.to_dict(result)


def test_write_creates_missing_parent_directories(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = JsonExperimentReporter()

    output_path = (
        tmp_path
        / "reports"
        / "monte_carlo"
        / "experiment.json"
    )

    reporter.write(
        result,
        output_path,
    )

    assert output_path.is_file()


def test_write_adds_trailing_newline(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = JsonExperimentReporter()

    output_path = tmp_path / "experiment.json"

    reporter.write(
        result,
        output_path,
    )

    assert output_path.read_text(
        encoding="utf-8",
    ).endswith("\n")


def test_write_rejects_directory_path(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = JsonExperimentReporter()

    with pytest.raises(
        ValueError,
        match="JSON report path is a directory",
    ):
        reporter.write(
            result,
            tmp_path,
        )


def test_reporter_supports_compact_json() -> None:
    result = create_experiment_result()
    reporter = JsonExperimentReporter(
        indent=None,
    )

    serialized = reporter.to_json(result)

    assert "\n" not in serialized


def test_reporter_rejects_negative_indent() -> None:
    with pytest.raises(
        ValueError,
        match="indent must not be negative.",
    ):
        JsonExperimentReporter(
            indent=-1,
        )


def test_reporter_does_not_modify_experiment_result() -> None:
    result = create_experiment_result()
    original_results = result.game_results
    original_summary = result.summary

    reporter = JsonExperimentReporter()

    reporter.to_dict(result)
    reporter.to_json(result)

    assert result.game_results is original_results
    assert result.summary is original_summary