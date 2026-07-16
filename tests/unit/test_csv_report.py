from __future__ import annotations

import csv
from pathlib import Path

import pytest

from krs.report.csv import (
    CsvExperimentReporter,
    CsvReportPaths,
)
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
            winner="プレイヤー",
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


def read_csv_rows(
    path: Path,
) -> list[dict[str, str]]:
    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(
            csv.DictReader(file)
        )


def test_write_creates_summary_and_games_files(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = CsvExperimentReporter()

    paths = reporter.write(
        result,
        tmp_path,
    )

    assert paths == CsvReportPaths(
        summary_path=tmp_path / "summary.csv",
        games_path=tmp_path / "games.csv",
    )
    assert paths.summary_path.is_file()
    assert paths.games_path.is_file()


def test_write_creates_missing_output_directory(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = CsvExperimentReporter()

    output_directory = (
        tmp_path
        / "reports"
        / "experiment"
    )

    reporter.write(
        result,
        output_directory,
    )

    assert (
        output_directory
        / "summary.csv"
    ).is_file()
    assert (
        output_directory
        / "games.csv"
    ).is_file()


def test_summary_csv_contains_configuration_values(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = CsvExperimentReporter()

    paths = reporter.write(
        result,
        tmp_path,
    )

    rows = read_csv_rows(
        paths.summary_path,
    )

    assert len(rows) == 1

    row = rows[0]

    assert row["strategy_name"] == "combo"
    assert row["games"] == "3"
    assert row["max_turns"] == "8"
    assert row["seed"] == "12345"
    assert row["mulligan_enabled"] == "False"
    assert row["save_replays"] == "True"
    assert row["workers"] == "4"


def test_summary_csv_contains_summary_values(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = CsvExperimentReporter()

    paths = reporter.write(
        result,
        tmp_path,
    )

    row = read_csv_rows(
        paths.summary_path,
    )[0]

    assert row["games_requested"] == "3"
    assert row["games_completed"] == "3"
    assert row["wins"] == "2"
    assert row["non_wins"] == "1"
    assert float(row["win_rate"]) == pytest.approx(
        2 / 3
    )
    assert row["turn_limit_games"] == "1"
    assert row["total_turns_started"] == "16"
    assert float(
        row["average_turns_started"]
    ) == pytest.approx(16 / 3)
    assert row["total_kinnan_activations"] == "3"
    assert float(
        row["average_kinnan_activations"]
    ) == pytest.approx(1.0)
    assert row["fastest_win_turn"] == "3"


def test_games_csv_contains_ordered_results(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = CsvExperimentReporter()

    paths = reporter.write(
        result,
        tmp_path,
    )

    rows = read_csv_rows(
        paths.games_path,
    )

    assert rows == [
        {
            "game_id": "0",
            "turns_started": "3",
            "kinnan_activations": "2",
            "reached_turn_limit": "False",
            "game_over": "True",
            "winner": "Player",
        },
        {
            "game_id": "1",
            "turns_started": "5",
            "kinnan_activations": "1",
            "reached_turn_limit": "False",
            "game_over": "True",
            "winner": "プレイヤー",
        },
        {
            "game_id": "2",
            "turns_started": "8",
            "kinnan_activations": "0",
            "reached_turn_limit": "True",
            "game_over": "False",
            "winner": "",
        },
    ]


def test_games_csv_preserves_unicode(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = CsvExperimentReporter()

    paths = reporter.write(
        result,
        tmp_path,
    )

    content = paths.games_path.read_text(
        encoding="utf-8",
    )

    assert "プレイヤー" in content


def test_csv_files_use_expected_headers(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = CsvExperimentReporter()

    paths = reporter.write(
        result,
        tmp_path,
    )

    with paths.summary_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        summary_reader = csv.reader(file)
        summary_header = next(summary_reader)

    with paths.games_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        games_reader = csv.reader(file)
        games_header = next(games_reader)

    assert summary_header == [
        "strategy_name",
        "games",
        "max_turns",
        "seed",
        "mulligan_enabled",
        "save_replays",
        "workers",
        "games_requested",
        "games_completed",
        "wins",
        "non_wins",
        "win_rate",
        "turn_limit_games",
        "total_turns_started",
        "average_turns_started",
        "total_kinnan_activations",
        "average_kinnan_activations",
        "fastest_win_turn",
        "kinnan_chain_games",
        "kinnan_activation_games",
        "kinnan_chain_games_count",
        "kinnan_overall_chain_rate",
        "kinnan_activation_game_chain_rate",
        "kinnan_total_chain_activations",
        "kinnan_chain_activations",
        "kinnan_activation_chain_rate",
        "kinnan_average_longest_chain",
        "kinnan_max_chain",
    ]

    assert games_header == [
        "game_id",
        "turns_started",
        "kinnan_activations",
        "reached_turn_limit",
        "game_over",
        "winner",
    ]


def test_write_summary_supports_custom_path(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = CsvExperimentReporter()

    output_path = (
        tmp_path
        / "custom"
        / "result-summary.csv"
    )

    returned_path = reporter.write_summary(
        result,
        output_path,
    )

    assert returned_path == output_path
    assert output_path.is_file()


def test_write_games_supports_custom_path(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = CsvExperimentReporter()

    output_path = (
        tmp_path
        / "custom"
        / "result-games.csv"
    )

    returned_path = reporter.write_games(
        result,
        output_path,
    )

    assert returned_path == output_path
    assert output_path.is_file()


def test_write_rejects_file_as_output_directory(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = CsvExperimentReporter()

    output_file = tmp_path / "existing.txt"
    output_file.write_text(
        "content",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=(
            "CSV report output path is not "
            "a directory"
        ),
    ):
        reporter.write(
            result,
            output_file,
        )


def test_write_summary_rejects_directory_path(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = CsvExperimentReporter()

    with pytest.raises(
        ValueError,
        match="CSV report path is a directory",
    ):
        reporter.write_summary(
            result,
            tmp_path,
        )


def test_write_games_rejects_directory_path(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = CsvExperimentReporter()

    with pytest.raises(
        ValueError,
        match="CSV report path is a directory",
    ):
        reporter.write_games(
            result,
            tmp_path,
        )


def test_custom_filenames_are_supported(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    reporter = CsvExperimentReporter(
        summary_filename="experiment-summary.csv",
        games_filename="experiment-games.csv",
    )

    paths = reporter.write(
        result,
        tmp_path,
    )

    assert paths.summary_path == (
        tmp_path
        / "experiment-summary.csv"
    )
    assert paths.games_path == (
        tmp_path
        / "experiment-games.csv"
    )


@pytest.mark.parametrize(
    ("field_name", "summary_filename", "games_filename"),
    [
        (
            "summary_filename",
            "",
            "games.csv",
        ),
        (
            "games_filename",
            "summary.csv",
            " ",
        ),
    ],
)
def test_reporter_rejects_empty_filenames(
    field_name: str,
    summary_filename: str,
    games_filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=rf"{field_name} must not be empty.",
    ):
        CsvExperimentReporter(
            summary_filename=summary_filename,
            games_filename=games_filename,
        )


@pytest.mark.parametrize(
    ("field_name", "summary_filename", "games_filename"),
    [
        (
            "summary_filename",
            "reports/summary.csv",
            "games.csv",
        ),
        (
            "games_filename",
            "summary.csv",
            "reports/games.csv",
        ),
    ],
)
def test_reporter_rejects_directory_in_filename(
    field_name: str,
    summary_filename: str,
    games_filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            rf"{field_name} must not contain "
            r"a directory."
        ),
    ):
        CsvExperimentReporter(
            summary_filename=summary_filename,
            games_filename=games_filename,
        )


@pytest.mark.parametrize(
    ("field_name", "summary_filename", "games_filename"),
    [
        (
            "summary_filename",
            "summary.json",
            "games.csv",
        ),
        (
            "games_filename",
            "summary.csv",
            "games.txt",
        ),
    ],
)
def test_reporter_requires_csv_extension(
    field_name: str,
    summary_filename: str,
    games_filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=rf"{field_name} must use the .csv extension.",
    ):
        CsvExperimentReporter(
            summary_filename=summary_filename,
            games_filename=games_filename,
        )


def test_reporter_rejects_identical_filenames() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "summary_filename and games_filename "
            "must be different."
        ),
    ):
        CsvExperimentReporter(
            summary_filename="result.csv",
            games_filename="result.csv",
        )


def test_none_seed_is_written_as_empty_value(
    tmp_path: Path,
) -> None:
    config = SimulationConfig(
        games=1,
        seed=None,
    )
    game_results = (
        create_game_result(
            turns_started=6,
            kinnan_activations=0,
            reached_turn_limit=True,
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

    paths = CsvExperimentReporter().write(
        result,
        tmp_path,
    )

    row = read_csv_rows(
        paths.summary_path,
    )[0]

    assert row["seed"] == ""


def test_no_win_fastest_turn_is_written_as_empty_value(
    tmp_path: Path,
) -> None:
    config = SimulationConfig(
        games=1,
    )
    game_results = (
        create_game_result(
            turns_started=6,
            kinnan_activations=0,
            reached_turn_limit=True,
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

    paths = CsvExperimentReporter().write(
        result,
        tmp_path,
    )

    row = read_csv_rows(
        paths.summary_path,
    )[0]

    assert row["fastest_win_turn"] == ""


def test_csv_report_does_not_modify_experiment_result(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    original_results = result.game_results
    original_summary = result.summary
    original_config = result.config

    CsvExperimentReporter().write(
        result,
        tmp_path,
    )

    assert result.game_results is original_results
    assert result.summary is original_summary
    assert result.config is original_config