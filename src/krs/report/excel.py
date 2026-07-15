from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from openpyxl import Workbook
from openpyxl.styles import Alignment
from openpyxl.styles import Border
from openpyxl.styles import Font
from openpyxl.styles import PatternFill
from openpyxl.styles import Side
from openpyxl.worksheet.table import Table
from openpyxl.worksheet.table import TableStyleInfo
from openpyxl.worksheet.worksheet import Worksheet

from krs.simulation.experiment import ExperimentResult
from krs.simulation.runner import GoldfishRunResult


SUMMARY_SHEET_NAME: Final = "Summary"
GAMES_SHEET_NAME: Final = "Games"

HEADER_FILL: Final = "1F4E78"
HEADER_FONT_COLOR: Final = "FFFFFF"
SECTION_FILL: Final = "D9EAF7"
WIN_FILL: Final = "E2F0D9"
NON_WIN_FILL: Final = "FFFFFF"
BORDER_COLOR: Final = "D9E1F2"


@dataclass(frozen=True, slots=True)
class ExcelExperimentReporter:
    """
    Creates a formatted Excel workbook from ExperimentResult.

    The reporter serializes existing simulation configuration, summary, and
    game results. It does not recalculate statistics or mutate the supplied
    ExperimentResult.
    """

    title: str = "Kinnan Research Simulator Report"

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be empty.")

    def create_workbook(
        self,
        result: ExperimentResult,
    ) -> Workbook:
        """Create an in-memory Excel workbook for one experiment."""
        workbook = Workbook()

        summary_sheet = workbook.active

        if summary_sheet is None:
            raise RuntimeError(
                "Workbook did not create an active worksheet."
            )

        summary_sheet.title = SUMMARY_SHEET_NAME
        games_sheet = workbook.create_sheet(
            title=GAMES_SHEET_NAME,
        )

        self._populate_summary_sheet(
            summary_sheet,
            result,
        )
        self._populate_games_sheet(
            games_sheet,
            result,
        )

        return workbook

    def write(
        self,
        result: ExperimentResult,
        path: str | Path,
    ) -> Path:
        """
        Create and save an Excel report.

        Missing parent directories are created automatically.
        """
        output_path = Path(path)

        if output_path.exists() and output_path.is_dir():
            raise ValueError(
                f"Excel report path is a directory: {output_path}"
            )

        if output_path.suffix.casefold() != ".xlsx":
            raise ValueError(
                "Excel report path must use the .xlsx extension."
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        workbook = self.create_workbook(result)

        try:
            workbook.save(output_path)
        finally:
            workbook.close()

        return output_path

    def _populate_summary_sheet(
        self,
        sheet: Worksheet,
        result: ExperimentResult,
    ) -> None:
        """Populate the Summary worksheet."""
        config = result.config
        summary = result.summary

        sheet.merge_cells("A1:B1")
        sheet["A1"] = self.title
        sheet["A1"].font = Font(
            bold=True,
            size=16,
            color=HEADER_FONT_COLOR,
        )
        sheet["A1"].fill = PatternFill(
            fill_type="solid",
            fgColor=HEADER_FILL,
        )
        sheet["A1"].alignment = Alignment(
            horizontal="center",
            vertical="center",
        )
        sheet.row_dimensions[1].height = 28

        rows: tuple[tuple[str, object], ...] = (
            ("Configuration", None),
            ("Strategy", config.strategy_name),
            ("Games requested", config.games),
            ("Maximum turns", config.max_turns),
            ("Seed", config.seed),
            ("Workers", config.workers),
            ("Mulligan enabled", config.mulligan_enabled),
            ("Save replays", config.save_replays),
            ("Summary", None),
            ("Games completed", summary.games_completed),
            ("Wins", summary.wins),
            ("Non-wins", summary.non_wins),
            ("Win rate", summary.win_rate),
            ("Turn-limit games", summary.turn_limit_games),
            (
                "Total turns started",
                summary.total_turns_started,
            ),
            (
                "Average turns started",
                summary.average_turns_started,
            ),
            (
                "Total Kinnan activations",
                summary.total_kinnan_activations,
            ),
            (
                "Average Kinnan activations",
                summary.average_kinnan_activations,
            ),
            (
                "Fastest win turn",
                summary.fastest_win_turn,
            ),
        )

        current_row = 3

        for label, value in rows:
            if value is None and label in {
                "Configuration",
                "Summary",
            }:
                self._write_section_header(
                    sheet,
                    row=current_row,
                    label=label,
                )
            else:
                sheet.cell(
                    row=current_row,
                    column=1,
                    value=label,
                )
                sheet.cell(
                    row=current_row,
                    column=2,
                    value=value,
                )
                self._style_summary_row(
                    sheet,
                    row=current_row,
                )

            current_row += 1

        win_rate_row = self._find_label_row(
            sheet,
            "Win rate",
        )
        average_turns_row = self._find_label_row(
            sheet,
            "Average turns started",
        )
        average_activations_row = self._find_label_row(
            sheet,
            "Average Kinnan activations",
        )

        sheet.cell(
            row=win_rate_row,
            column=2,
        ).number_format = "0.00%"

        sheet.cell(
            row=average_turns_row,
            column=2,
        ).number_format = "0.000"

        sheet.cell(
            row=average_activations_row,
            column=2,
        ).number_format = "0.000"

        sheet.column_dimensions["A"].width = 31
        sheet.column_dimensions["B"].width = 22
        sheet.freeze_panes = "A3"
        sheet.sheet_view.showGridLines = False
        sheet.auto_filter.ref = f"A3:B{current_row - 1}"

    def _populate_games_sheet(
        self,
        sheet: Worksheet,
        result: ExperimentResult,
    ) -> None:
        """Populate the Games worksheet."""
        headers = (
            "game_id",
            "turns_started",
            "kinnan_activations",
            "reached_turn_limit",
            "game_over",
            "winner",
        )

        for column, header in enumerate(
            headers,
            start=1,
        ):
            cell = sheet.cell(
                row=1,
                column=column,
                value=header,
            )
            self._style_header_cell(cell)

        for game_id, game_result in enumerate(
            result.game_results,
            start=0,
        ):
            self._write_game_row(
                sheet,
                row=game_id + 2,
                game_id=game_id,
                result=game_result,
            )

        last_row = len(result.game_results) + 1
        last_column = len(headers)

        if result.game_results:
            table = Table(
                displayName="GamesTable",
                ref=f"A1:F{last_row}",
            )
            table.tableStyleInfo = TableStyleInfo(
                name="TableStyleMedium2",
                showFirstColumn=False,
                showLastColumn=False,
                showRowStripes=True,
                showColumnStripes=False,
            )
            sheet.add_table(table)
        else:
            sheet.auto_filter.ref = "A1:F1"

        sheet.freeze_panes = "A2"
        sheet.sheet_view.showGridLines = False

        widths = {
            "A": 12,
            "B": 16,
            "C": 21,
            "D": 21,
            "E": 14,
            "F": 24,
        }

        for column, width in widths.items():
            sheet.column_dimensions[column].width = width

        for row in sheet.iter_rows(
            min_row=2,
            max_row=last_row,
            min_col=1,
            max_col=last_column,
        ):
            for cell in row:
                cell.alignment = Alignment(
                    horizontal="center",
                    vertical="center",
                )

    def _write_game_row(
        self,
        sheet: Worksheet,
        *,
        row: int,
        game_id: int,
        result: GoldfishRunResult,
    ) -> None:
        """Write one Goldfish game result."""
        values = (
            game_id,
            result.turns_started,
            result.kinnan_activations,
            result.reached_turn_limit,
            result.game_over,
            result.winner,
        )

        is_win = (
            result.game_over
            and result.winner is not None
        )
        fill_color = (
            WIN_FILL
            if is_win
            else NON_WIN_FILL
        )

        for column, value in enumerate(
            values,
            start=1,
        ):
            cell = sheet.cell(
                row=row,
                column=column,
                value=value,
            )
            cell.fill = PatternFill(
                fill_type="solid",
                fgColor=fill_color,
            )
            cell.border = self._thin_border()

    @classmethod
    def _write_section_header(
        cls,
        sheet: Worksheet,
        *,
        row: int,
        label: str,
    ) -> None:
        """Write one Summary section heading."""
        sheet.merge_cells(
            start_row=row,
            start_column=1,
            end_row=row,
            end_column=2,
        )

        cell = sheet.cell(
            row=row,
            column=1,
            value=label,
        )
        cell.font = Font(
            bold=True,
        )
        cell.fill = PatternFill(
            fill_type="solid",
            fgColor=SECTION_FILL,
        )
        cell.alignment = Alignment(
            horizontal="left",
            vertical="center",
        )
        cell.border = cls._thin_border()

        sheet.cell(
            row=row,
            column=2,
        ).border = cls._thin_border()

    @classmethod
    def _style_summary_row(
        cls,
        sheet: Worksheet,
        *,
        row: int,
    ) -> None:
        """Apply formatting to one Summary data row."""
        label_cell = sheet.cell(
            row=row,
            column=1,
        )
        value_cell = sheet.cell(
            row=row,
            column=2,
        )

        label_cell.font = Font(
            bold=True,
        )
        label_cell.fill = PatternFill(
            fill_type="solid",
            fgColor="F3F6F9",
        )

        for cell in (
            label_cell,
            value_cell,
        ):
            cell.border = cls._thin_border()
            cell.alignment = Alignment(
                vertical="center",
            )

    @classmethod
    def _style_header_cell(
        cls,
        cell: object,
    ) -> None:
        """Apply shared header styling."""
        if not hasattr(cell, "font"):
            raise TypeError("Expected an Excel cell.")

        cell.font = Font(  # type: ignore[attr-defined]
            bold=True,
            color=HEADER_FONT_COLOR,
        )
        cell.fill = PatternFill(  # type: ignore[attr-defined]
            fill_type="solid",
            fgColor=HEADER_FILL,
        )
        cell.alignment = Alignment(  # type: ignore[attr-defined]
            horizontal="center",
            vertical="center",
        )
        cell.border = cls._thin_border()  # type: ignore[attr-defined]

    @staticmethod
    def _find_label_row(
        sheet: Worksheet,
        label: str,
    ) -> int:
        """Return the row containing one Summary label."""
        for row in range(
            1,
            sheet.max_row + 1,
        ):
            if sheet.cell(
                row=row,
                column=1,
            ).value == label:
                return row

        raise ValueError(
            f"Summary label not found: {label}"
        )

    @staticmethod
    def _thin_border() -> Border:
        """Return the shared thin cell border."""
        side = Side(
            style="thin",
            color=BORDER_COLOR,
        )

        return Border(
            left=side,
            right=side,
            top=side,
            bottom=side,
        )