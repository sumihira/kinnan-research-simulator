from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from krs.simulation.experiment import ExperimentResult
from krs.statistics.experiment_analysis import (
    ExperimentAnalysis,
    ExperimentAnalysisCalculator,
)


JsonObject = dict[str, Any]


@dataclass(frozen=True, slots=True)
class ExperimentAnalysisReporter:
    """
    Converts complete experiment statistics into JSON-compatible data.

    Statistical calculations are delegated to ExperimentAnalysisCalculator.
    The reporter only transforms and serializes the completed analysis.
    """

    analysis_calculator: ExperimentAnalysisCalculator = field(
        default_factory=ExperimentAnalysisCalculator,
    )
    indent: int | None = 2

    def __post_init__(self) -> None:
        if self.indent is not None and self.indent < 0:
            raise ValueError(
                "indent must not be negative."
            )

    def analyze(
        self,
        result: ExperimentResult,
    ) -> ExperimentAnalysis:
        """
        Calculate complete statistical analysis for one experiment.
        """
        return self.analysis_calculator.calculate(result)

    def to_dict(
        self,
        result: ExperimentResult,
    ) -> JsonObject:
        """
        Calculate and convert analysis into JSON-compatible data.
        """
        analysis = self.analyze(result)

        return self.analysis_to_dict(analysis)

    def analysis_to_dict(
        self,
        analysis: ExperimentAnalysis,
    ) -> JsonObject:
        """
        Convert an existing ExperimentAnalysis into serializable data.
        """
        experiment_statistics = (
            analysis.experiment_statistics
        )
        win_turn_statistics = (
            analysis.win_turn_statistics
        )
        confidence_interval = (
            experiment_statistics
            .win_rate_confidence_interval
        )

        return {
            "overview": {
                "games_completed": analysis.games_completed,
                "wins": analysis.wins,
                "non_wins": analysis.non_wins,
                "win_rate": analysis.win_rate,
                "win_rate_percent": (
                    analysis.win_rate_percent
                ),
                "has_wins": analysis.has_wins,
            },
            "confidence_interval": {
                "confidence_level": (
                    confidence_interval.confidence_level
                ),
                "wins": confidence_interval.wins,
                "games": confidence_interval.games,
                "observed_rate": (
                    confidence_interval.observed_rate
                ),
                "lower_bound": (
                    confidence_interval.lower_bound
                ),
                "upper_bound": (
                    confidence_interval.upper_bound
                ),
                "width": confidence_interval.width,
                "margin_below": (
                    confidence_interval.margin_below
                ),
                "margin_above": (
                    confidence_interval.margin_above
                ),
                "observed_percent": (
                    confidence_interval.observed_percent
                ),
                "lower_percent": (
                    confidence_interval.lower_percent
                ),
                "upper_percent": (
                    confidence_interval.upper_percent
                ),
            },
            "experiment_statistics": {
                "turn_limit_games": (
                    experiment_statistics.turn_limit_games
                ),
                "turn_limit_rate": (
                    experiment_statistics.turn_limit_rate
                ),
                "turn_limit_percent": (
                    experiment_statistics.turn_limit_percent
                ),
                "average_turns_started": (
                    experiment_statistics
                    .average_turns_started
                ),
                "turn_standard_deviation": (
                    experiment_statistics
                    .turn_standard_deviation
                ),
                "average_kinnan_activations": (
                    experiment_statistics
                    .average_kinnan_activations
                ),
                "kinnan_activation_standard_deviation": (
                    experiment_statistics
                    .kinnan_activation_standard_deviation
                ),
                "fastest_win_turn": (
                    experiment_statistics.fastest_win_turn
                ),
            },
            "win_turn_statistics": {
                "wins": win_turn_statistics.wins,
                "win_rate": win_turn_statistics.win_rate,
                "win_rate_percent": (
                    win_turn_statistics.win_rate_percent
                ),
                "has_wins": win_turn_statistics.has_wins,
                "fastest_win_turn": (
                    win_turn_statistics.fastest_win_turn
                ),
                "slowest_win_turn": (
                    win_turn_statistics.slowest_win_turn
                ),
                "average_win_turn": (
                    win_turn_statistics.average_win_turn
                ),
                "median_win_turn": (
                    win_turn_statistics.median_win_turn
                ),
                "percentile_90_win_turn": (
                    win_turn_statistics
                    .percentile_90_win_turn
                ),
                "percentile_95_win_turn": (
                    win_turn_statistics
                    .percentile_95_win_turn
                ),
                "win_turn_standard_deviation": (
                    win_turn_statistics
                    .win_turn_standard_deviation
                ),
            },
        }

    def to_json(
        self,
        result: ExperimentResult,
    ) -> str:
        """
        Calculate and serialize analysis into a JSON string.
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
        Write statistical analysis to a UTF-8 JSON file.

        Missing parent directories are created automatically.
        """
        output_path = Path(path)

        if output_path.exists() and output_path.is_dir():
            raise ValueError(
                "Analysis report path is a directory: "
                f"{output_path}"
            )

        if output_path.suffix.casefold() != ".json":
            raise ValueError(
                "Analysis report path must use the .json extension."
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