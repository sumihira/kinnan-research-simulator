from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from krs.simulation.experiment import ExperimentResult
from krs.simulation.runner import GoldfishRunResult


MarkdownRows = tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class ExperimentSummaryMarkdownReporter:
    """
    Creates a Markdown report from ExperimentResult.

    The reporter serializes existing simulation configuration, aggregate
    summary values, and individual game results. It does not recalculate
    statistics or modify the supplied ExperimentResult.
    """

    title: str = "Goldfish Experiment Report"

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be empty.")

    def to_markdown(
        self,
        result: ExperimentResult,
    ) -> str:
        """
        Convert one ExperimentResult into a complete Markdown report.
        """
        sections = (
            self._render_title(),
            self._render_configuration(result),
            self._render_summary(result),
            self._render_games(result),
        )

        return "\n\n---\n\n".join(sections) + "\n"

    def write(
        self,
        result: ExperimentResult,
        path: str | Path,
    ) -> Path:
        """
        Write a UTF-8 Markdown experiment report.

        Missing parent directories are created automatically.
        """
        output_path = Path(path)

        if output_path.exists() and output_path.is_dir():
            raise ValueError(
                "Summary Markdown report path is a directory: "
                f"{output_path}"
            )

        if output_path.suffix.casefold() not in {
            ".md",
            ".markdown",
        }:
            raise ValueError(
                "Summary Markdown report path must use "
                "the .md or .markdown extension."
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            self.to_markdown(result),
            encoding="utf-8",
        )

        return output_path

    def _render_title(self) -> str:
        """
        Render the report title.
        """
        return f"# {self._escape_text(self.title)}"

    def _render_configuration(
        self,
        result: ExperimentResult,
    ) -> str:
        """
        Render simulation configuration values.
        """
        config = result.config

        seed = (
            str(config.seed)
            if config.seed is not None
            else "None"
        )

        rows: MarkdownRows = (
            (
                "Strategy",
                config.strategy_name,
            ),
            (
                "Games requested",
                f"{config.games:,}",
            ),
            (
                "Maximum turns",
                f"{config.max_turns:,}",
            ),
            (
                "Seed",
                seed,
            ),
            (
                "Workers",
                f"{config.workers:,}",
            ),
            (
                "Mulligan enabled",
                self._format_boolean(
                    config.mulligan_enabled
                ),
            ),
            (
                "Save replays",
                self._format_boolean(
                    config.save_replays
                ),
            ),
        )

        return self._render_section(
            title="Simulation Configuration",
            table=self._render_metric_table(rows),
        )

    def _render_summary(
        self,
        result: ExperimentResult,
    ) -> str:
        """
        Render aggregate simulation and Kinnan-chain results.
        """
        summary = result.summary
        chain = summary.kinnan_chain

        fastest_win_turn = (
            str(summary.fastest_win_turn)
            if summary.fastest_win_turn is not None
            else "N/A"
        )

        rows: MarkdownRows = (
            (
                "Games requested",
                f"{summary.games_requested:,}",
            ),
            (
                "Games completed",
                f"{summary.games_completed:,}",
            ),
            (
                "Wins",
                f"{summary.wins:,}",
            ),
            (
                "Non-wins",
                f"{summary.non_wins:,}",
            ),
            (
                "Win rate",
                f"{summary.win_rate * 100.0:.3f}%",
            ),
            (
                "Turn-limit games",
                f"{summary.turn_limit_games:,}",
            ),
            (
                "Total turns started",
                f"{summary.total_turns_started:,}",
            ),
            (
                "Average turns started",
                f"{summary.average_turns_started:.3f}",
            ),
            (
                "Total Kinnan activations",
                f"{summary.total_kinnan_activations:,}",
            ),
            (
                "Average Kinnan activations",
                f"{summary.average_kinnan_activations:.3f}",
            ),
            (
                "Fastest win turn",
                fastest_win_turn,
            ),
            (
                "Kinnan chain games",
                f"{chain.games:,}",
            ),
            (
                "Kinnan activation games",
                f"{chain.games_with_activation:,}",
            ),
            (
                "Kinnan chain-established games",
                f"{chain.games_with_chain:,}",
            ),
            (
                "Overall Kinnan chain rate",
                f"{chain.overall_chain_rate * 100.0:.3f}%",
            ),
            (
                "Activation-game Kinnan chain rate",
                (
                    f"{chain.activation_game_chain_rate * 100.0:.3f}%"
                ),
            ),
            (
                "Total tracked Kinnan activations",
                f"{chain.total_activations:,}",
            ),
            (
                "Kinnan chain activations",
                f"{chain.chain_activations:,}",
            ),
            (
                "Activation-based Kinnan chain rate",
                f"{chain.activation_chain_rate * 100.0:.3f}%",
            ),
            (
                "Average maximum chain length",
                f"{chain.average_longest_chain:.3f}",
            ),
            (
                "Maximum chain length",
                f"{chain.max_chain:,}",
            ),
        )

        return self._render_section(
            title="Summary",
            table=self._render_metric_table(rows),
        )

    def _render_games(
        self,
        result: ExperimentResult,
    ) -> str:
        """
        Render individual Goldfish game results in game ID order.
        """
        if not result.game_results:
            content = (
                "> No individual game results are available."
            )
        else:
            content = self._render_games_table(
                result.game_results
            )

        return self._render_section(
            title="Individual Games",
            table=content,
        )

    @classmethod
    def _render_games_table(
        cls,
        game_results: tuple[GoldfishRunResult, ...],
    ) -> str:
        """
        Render individual game results as a Markdown table.
        """
        header = "\n".join(
            (
                (
                    "| Game ID | Result | Turns started | "
                    "Kinnan activations | Turn limit | Winner |"
                ),
                (
                    "|--:|:--:|--:|--:|:--:|:--|"
                ),
            )
        )

        rendered_rows = "\n".join(
            cls._render_game_row(
                game_id=game_id,
                result=game_result,
            )
            for game_id, game_result in enumerate(
                game_results
            )
        )

        return "\n".join(
            (
                header,
                rendered_rows,
            )
        )

    @classmethod
    def _render_game_row(
        cls,
        *,
        game_id: int,
        result: GoldfishRunResult,
    ) -> str:
        """
        Render one individual game row.
        """
        is_win = (
            result.game_over
            and result.winner is not None
        )

        game_status = (
            "Win"
            if is_win
            else "Non-win"
        )

        winner = (
            result.winner
            if result.winner is not None
            else ""
        )

        values = (
            str(game_id),
            game_status,
            str(result.turns_started),
            str(result.kinnan_activations),
            cls._format_boolean(
                result.reached_turn_limit
            ),
            winner,
        )

        escaped_values = tuple(
            cls._escape_table_cell(value)
            for value in values
        )

        return (
            f"| {escaped_values[0]} "
            f"| {escaped_values[1]} "
            f"| {escaped_values[2]} "
            f"| {escaped_values[3]} "
            f"| {escaped_values[4]} "
            f"| {escaped_values[5]} |"
        )

    @classmethod
    def _render_section(
        cls,
        *,
        title: str,
        table: str,
    ) -> str:
        """
        Render one level-two heading followed by section content.
        """
        return "\n\n".join(
            (
                f"## {cls._escape_text(title)}",
                table,
            )
        )

    @classmethod
    def _render_metric_table(
        cls,
        rows: MarkdownRows,
    ) -> str:
        """
        Render a two-column GitHub-compatible Markdown table.
        """
        header = "\n".join(
            (
                "| Metric | Value |",
                "|:--|--:|",
            )
        )

        rendered_rows = "\n".join(
            (
                f"| {cls._escape_table_cell(label)} "
                f"| {cls._escape_table_cell(value)} |"
            )
            for label, value in rows
        )

        return "\n".join(
            (
                header,
                rendered_rows,
            )
        )

    @staticmethod
    def _format_boolean(
        value: bool,
    ) -> str:
        """
        Format a boolean for human-readable Markdown.
        """
        return "Yes" if value else "No"

    @staticmethod
    def _escape_table_cell(
        value: str,
    ) -> str:
        """
        Escape characters that can break a Markdown table cell.
        """
        return (
            value
            .replace("\\", "\\\\")
            .replace("|", "\\|")
            .replace("\r\n", "<br>")
            .replace("\n", "<br>")
            .replace("\r", "<br>")
        )

    @staticmethod
    def _escape_text(
        value: str,
    ) -> str:
        """
        Escape common Markdown control characters in headings.
        """
        escaped_characters = {
            "\\": "\\\\",
            "`": "\\`",
            "*": "\\*",
            "_": "\\_",
            "{": "\\{",
            "}": "\\}",
            "[": "\\[",
            "]": "\\]",
            "<": "\\<",
            ">": "\\>",
            "#": "\\#",
            "+": "\\+",
            "-": "\\-",
            "!": "\\!",
            "|": "\\|",
        }

        return "".join(
            escaped_characters.get(
                character,
                character,
            )
            for character in value
        )