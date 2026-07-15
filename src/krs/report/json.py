from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from krs.simulation.experiment import ExperimentResult
from krs.simulation.runner import GoldfishRunResult
from krs.simulation.simulation_config import SimulationConfig


JsonObject = dict[str, Any]


@dataclass(frozen=True, slots=True)
class JsonExperimentReporter:
    """
    Converts ExperimentResult into JSON-compatible data.

    The reporter performs presentation and serialization only. It does not
    calculate simulation statistics or modify ExperimentResult.
    """

    indent: int | None = 2

    def __post_init__(self) -> None:
        if self.indent is not None and self.indent < 0:
            raise ValueError(
                "indent must not be negative."
            )

    def to_dict(
        self,
        result: ExperimentResult,
    ) -> JsonObject:
        """
        Convert one ExperimentResult into a JSON-compatible dictionary.
        """
        return {
            "config": self._config_to_dict(result.config),
            "summary": self._summary_to_dict(result),
            "games": [
                self._game_result_to_dict(
                    game_id=game_id,
                    result=game_result,
                )
                for game_id, game_result in enumerate(
                    result.game_results
                )
            ],
        }

    def to_json(
        self,
        result: ExperimentResult,
    ) -> str:
        """
        Serialize one ExperimentResult into a JSON string.
        """
        return json.dumps(
            self.to_dict(result),
            ensure_ascii=False,
            indent=self.indent,
            sort_keys=True,
        )

    def write(
        self,
        result: ExperimentResult,
        path: str | Path,
    ) -> Path:
        """
        Write one ExperimentResult to a UTF-8 JSON file.

        Missing parent directories are created automatically. The resolved
        Path supplied by the caller is returned after writing.
        """
        output_path = Path(path)

        if output_path.exists() and output_path.is_dir():
            raise ValueError(
                f"JSON report path is a directory: {output_path}"
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            self.to_json(result) + "\n",
            encoding="utf-8",
        )

        return output_path

    @staticmethod
    def _config_to_dict(
        config: SimulationConfig,
    ) -> JsonObject:
        """Convert SimulationConfig into JSON-compatible data."""
        return {
            "strategy_name": config.strategy_name,
            "games": config.games,
            "max_turns": config.max_turns,
            "seed": config.seed,
            "mulligan_enabled": config.mulligan_enabled,
            "save_replays": config.save_replays,
            "workers": config.workers,
        }

    @staticmethod
    def _summary_to_dict(
        result: ExperimentResult,
    ) -> JsonObject:
        """Convert the experiment summary into JSON-compatible data."""
        summary = result.summary

        return {
            "games_requested": summary.games_requested,
            "games_completed": summary.games_completed,
            "wins": summary.wins,
            "non_wins": summary.non_wins,
            "win_rate": summary.win_rate,
            "turn_limit_games": summary.turn_limit_games,
            "total_turns_started": summary.total_turns_started,
            "average_turns_started": (
                summary.average_turns_started
            ),
            "total_kinnan_activations": (
                summary.total_kinnan_activations
            ),
            "average_kinnan_activations": (
                summary.average_kinnan_activations
            ),
            "fastest_win_turn": summary.fastest_win_turn,
        }

    @staticmethod
    def _game_result_to_dict(
        *,
        game_id: int,
        result: GoldfishRunResult,
    ) -> JsonObject:
        """Convert one GoldfishRunResult into JSON-compatible data."""
        return {
            "game_id": game_id,
            "turns_started": result.turns_started,
            "kinnan_activations": result.kinnan_activations,
            "reached_turn_limit": result.reached_turn_limit,
            "game_over": result.game_over,
            "winner": result.winner,
        }