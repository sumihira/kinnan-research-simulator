from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from krs.replay.replay import Replay
from krs.replay.replay_statistics import (
    ReplayCount,
    ReplayStatistics,
)


CountData = dict[str, int]
ReplayStatisticsData = dict[
    str,
    int | None | CountData,
]


@dataclass(frozen=True, slots=True)
class ReplayStatisticsJsonReporter:
    """
    Serializes ReplayStatistics to JSON-compatible data.

    The reporter can receive either a Replay or an already calculated
    ReplayStatistics instance. Input values are never modified.
    """

    indent: int | None = 2

    def __post_init__(self) -> None:
        if (
            self.indent is not None
            and self.indent < 0
        ):
            raise ValueError(
                "indent must not be negative."
            )

    def to_dict(
        self,
        replay: Replay,
    ) -> ReplayStatisticsData:
        """
        Calculate ReplayStatistics and convert them to dictionary data.
        """
        statistics = ReplayStatistics.from_replay(
            replay
        )

        return self.statistics_to_dict(
            statistics
        )

    def statistics_to_dict(
        self,
        statistics: ReplayStatistics,
    ) -> ReplayStatisticsData:
        """
        Convert ReplayStatistics into JSON-compatible dictionary data.
        """
        return {
            "event_count": statistics.event_count,
            "turn_count": statistics.turn_count,
            "max_turn": statistics.max_turn,
            "game_start_count": (
                statistics.game_start_count
            ),
            "game_end_count": (
                statistics.game_end_count
            ),
            "action_counts": self._counts_to_dict(
                statistics.action_counts
            ),
            "phase_counts": self._counts_to_dict(
                statistics.phase_counts
            ),
        }

    def to_json(
        self,
        replay: Replay,
    ) -> str:
        """
        Calculate ReplayStatistics and return a JSON document.
        """
        return self._serialize(
            self.to_dict(replay)
        )

    def statistics_to_json(
        self,
        statistics: ReplayStatistics,
    ) -> str:
        """
        Convert existing ReplayStatistics to a JSON document.
        """
        return self._serialize(
            self.statistics_to_dict(
                statistics
            )
        )

    def write(
        self,
        replay: Replay,
        path: str | Path,
    ) -> Path:
        """
        Calculate statistics and write them as UTF-8 JSON.
        """
        return self._write_text(
            self.to_json(replay),
            path,
        )

    def write_statistics(
        self,
        statistics: ReplayStatistics,
        path: str | Path,
    ) -> Path:
        """
        Write existing ReplayStatistics as UTF-8 JSON.
        """
        return self._write_text(
            self.statistics_to_json(
                statistics
            ),
            path,
        )

    def _serialize(
        self,
        data: ReplayStatisticsData,
    ) -> str:
        """
        Serialize statistics data while preserving Unicode text.
        """
        return json.dumps(
            data,
            ensure_ascii=False,
            indent=self.indent,
        )

    @staticmethod
    def _counts_to_dict(
        counts: tuple[ReplayCount, ...],
    ) -> CountData:
        """
        Convert sorted ReplayCount values into stable dictionary data.
        """
        return {
            item.name: item.count
            for item in counts
        }

    @staticmethod
    def _validate_output_path(
        path: str | Path,
    ) -> Path:
        """
        Validate and normalize a JSON output path.
        """
        output_path = Path(path)

        if (
            output_path.exists()
            and output_path.is_dir()
        ):
            raise ValueError(
                "Replay statistics JSON path is a directory: "
                f"{output_path}"
            )

        if output_path.suffix.casefold() != ".json":
            raise ValueError(
                "Replay statistics JSON path must use "
                "the .json extension."
            )

        return output_path

    @classmethod
    def _write_text(
        cls,
        content: str,
        path: str | Path,
    ) -> Path:
        """
        Write one validated UTF-8 JSON document.
        """
        output_path = cls._validate_output_path(
            path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            content,
            encoding="utf-8",
        )

        return output_path