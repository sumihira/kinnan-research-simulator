from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import load_workbook

from krs.report.excel import ExcelExperimentReporter
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


def find_summary_value(
    sheet: object,
    label: str,
) -> object:
    for row in range(
        1,
        sheet.max_row + 1,  # type: ignore[attr-defined]
    ):
        if (
            sheet.cell(  # type: ignore[attr-defined]
                row=row,
                column=1,
            ).value
            == label
        ):
            return sheet.cell(  # type: ignore[attr-defined]
                row=row,
                column=2,
            ).value

    raise AssertionError(
        f"Summary label not found: {label}"
    )


def test_create_workbook_creates_expected_sheets() -> None:
    result = create_experiment_result()

    workbook = ExcelExperimentReporter().create_workbook(
        result
    )

    try:
        assert workbook.sheetnames == [
            "Summary",
            "Games",
        ]
    finally:
        workbook.close()


def test_summary_sheet_contains_title() -> None:
    result = create_experiment_result()

    workbook = ExcelExperimentReporter(
        title="KRS Analysis",
    ).create_workbook(result)

    try:
        sheet = workbook["Summary"]

        assert sheet["A1"].value == "KRS Analysis"
        assert sheet.merged_cells.ranges
    finally:
        workbook.close()


def test_summary_sheet_contains_configuration() -> None:
    result = create_experiment_result()

    workbook = ExcelExperimentReporter().create_workbook(
        result
    )

    try:
        sheet = workbook["Summary"]

        assert find_summary_value(
            sheet,
            "Strategy",
        ) == "combo"
        assert find_summary_value(
            sheet,
            "Games requested",
        ) == 3
        assert find_summary_value(
            sheet,
            "Maximum turns",
        ) == 8
        assert find_summary_value(
            sheet,
            "Seed",
        ) == 12345
        assert find_summary_value(
            sheet,
            "Workers",
        ) == 4
        assert find_summary_value(
            sheet,
            "Mulligan enabled",
        ) is False
        assert find_summary_value(
            sheet,
            "Save replays",
        ) is True
    finally:
        workbook.close()


def test_summary_sheet_contains_summary_values() -> None:
    result = create_experiment_result()

    workbook = ExcelExperimentReporter().create_workbook(
        result
    )

    try:
        sheet = workbook["Summary"]

        assert find_summary_value(
            sheet,
            "Games completed",
        ) == 3
        assert find_summary_value(
            sheet,
            "Wins",
        ) == 2
        assert find_summary_value(
            sheet,
            "Non-wins",
        ) == 1
        assert find_summary_value(
            sheet,
            "Win rate",
        ) == pytest.approx(2 / 3)
        assert find_summary_value(
            sheet,
            "Turn-limit games",
        ) == 1
        assert find_summary_value(
            sheet,
            "Total turns started",
        ) == 16
        assert find_summary_value(
            sheet,
            "Average turns started",
        ) == pytest.approx(16 / 3)
        assert find_summary_value(
            sheet,
            "Total Kinnan activations",
        ) == 3
        assert find_summary_value(
            sheet,
            "Average Kinnan activations",
        ) == pytest.approx(1.0)
        assert find_summary_value(
            sheet,
            "Fastest win turn",
        ) == 3
    finally:
        workbook.close()


def test_games_sheet_contains_headers() -> None:
    result = create_experiment_result()

    workbook = ExcelExperimentReporter().create_workbook(
        result
    )

    try:
        sheet = workbook["Games"]

        headers = tuple(
            sheet.cell(
                row=1,
                column=column,
            ).value
            for column in range(
                1,
                7,
            )
        )

        assert headers == (
            "game_id",
            "turns_started",
            "kinnan_activations",
            "reached_turn_limit",
            "game_over",
            "winner",
        )
    finally:
        workbook.close()


def test_games_sheet_contains_ordered_game_results() -> None:
    result = create_experiment_result()

    workbook = ExcelExperimentReporter().create_workbook(
        result
    )

    try:
        sheet = workbook["Games"]

        assert tuple(
            sheet.cell(
                row=row,
                column=1,
            ).value
            for row in range(
                2,
                5,
            )
        ) == (
            0,
            1,
            2,
        )

        assert tuple(
            sheet.cell(
                row=2,
                column=column,
            ).value
            for column in range(
                1,
                7,
            )
        ) == (
            0,
            3,
            2,
            False,
            True,
            "Player",
        )

        assert tuple(
            sheet.cell(
                row=3,
                column=column,
            ).value
            for column in range(
                1,
                7,
            )
        ) == (
            1,
            5,
            1,
            False,
            True,
            "プレイヤー",
        )

        assert tuple(
            sheet.cell(
                row=4,
                column=column,
            ).value
            for column in range(
                1,
                7,
            )
        ) == (
            2,
            8,
            0,
            True,
            False,
            None,
        )
    finally:
        workbook.close()


def test_games_sheet_contains_excel_table() -> None:
    result = create_experiment_result()

    workbook = ExcelExperimentReporter().create_workbook(
        result
    )

    try:
        sheet = workbook["Games"]

        assert "GamesTable" in sheet.tables
        assert sheet.tables["GamesTable"].ref == "A1:F4"
    finally:
        workbook.close()


def test_workbook_uses_frozen_panes() -> None:
    result = create_experiment_result()

    workbook = ExcelExperimentReporter().create_workbook(
        result
    )

    try:
        assert workbook["Summary"].freeze_panes == "A3"
        assert workbook["Games"].freeze_panes == "A2"
    finally:
        workbook.close()


def test_summary_uses_expected_number_formats() -> None:
    result = create_experiment_result()

    workbook = ExcelExperimentReporter().create_workbook(
        result
    )

    try:
        sheet = workbook["Summary"]

        for row in range(
            1,
            sheet.max_row + 1,
        ):
            label = sheet.cell(
                row=row,
                column=1,
            ).value

            if label == "Win rate":
                assert (
                    sheet.cell(
                        row=row,
                        column=2,
                    ).number_format
                    == "0.00%"
                )

            if label in {
                "Average turns started",
                "Average Kinnan activations",
            }:
                assert (
                    sheet.cell(
                        row=row,
                        column=2,
                    ).number_format
                    == "0.000"
                )
    finally:
        workbook.close()


def test_write_creates_xlsx_file(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    output_path = tmp_path / "experiment.xlsx"

    returned_path = ExcelExperimentReporter().write(
        result,
        output_path,
    )

    assert returned_path == output_path
    assert output_path.is_file()

    workbook = load_workbook(output_path)

    try:
        assert workbook.sheetnames == [
            "Summary",
            "Games",
        ]
        assert (
            workbook["Games"]["F3"].value
            == "プレイヤー"
        )
    finally:
        workbook.close()


def test_write_creates_parent_directories(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    output_path = (
        tmp_path
        / "reports"
        / "excel"
        / "experiment.xlsx"
    )

    ExcelExperimentReporter().write(
        result,
        output_path,
    )

    assert output_path.is_file()


def test_write_rejects_directory_path(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    with pytest.raises(
        ValueError,
        match="Excel report path is a directory",
    ):
        ExcelExperimentReporter().write(
            result,
            tmp_path,
        )


@pytest.mark.parametrize(
    "filename",
    (
        "report.xls",
        "report.csv",
        "report",
    ),
)
def test_write_rejects_invalid_extension(
    tmp_path: Path,
    filename: str,
) -> None:
    result = create_experiment_result()

    with pytest.raises(
        ValueError,
        match=(
            "Excel report path must use "
            "the .xlsx extension."
        ),
    ):
        ExcelExperimentReporter().write(
            result,
            tmp_path / filename,
        )


@pytest.mark.parametrize(
    "title",
    (
        "",
        " ",
        "\t",
    ),
)
def test_reporter_rejects_empty_title(
    title: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="title must not be empty.",
    ):
        ExcelExperimentReporter(
            title=title,
        )


def test_excel_report_does_not_modify_experiment_result(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()

    original_config = result.config
    original_summary = result.summary
    original_results = result.game_results

    ExcelExperimentReporter().write(
        result,
        tmp_path / "experiment.xlsx",
    )

    assert result.config is original_config
    assert result.summary is original_summary
    assert result.game_results is original_results