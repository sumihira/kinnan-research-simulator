from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from krs.replay.replay import Replay
from krs.replay.replay_event import ReplayEvent


ReplayEventData = dict[str, int | str]
ReplayData = dict[
    str,
    int | list[ReplayEventData],
]


@dataclass(frozen=True, slots=True)
class ReplayJsonReporter:
    """
    Serializes Replay data to JSON.

    The reporter reads Replay and ReplayEvent values without modifying them.
    Event insertion order is preserved in the resulting JSON document.
    """

    indent: int | None = 2

    def __post_init__(self) -> None:
        if self.indent is not None and self.indent < 0:
            raise ValueError(
                "indent must not be negative."
            )

    def to_dict(
        self,
        replay: Replay,
    ) -> ReplayData:
        """
        Convert a Replay into JSON-compatible dictionary data.
        """
        return {
            "event_count": replay.event_count,
            "events": [
                self._event_to_dict(event)
                for event in replay.events
            ],
        }

    def to_json(
        self,
        replay: Replay,
    ) -> str:
        """
        Convert a Replay into a JSON string.

        Unicode characters are written directly instead of being converted
        into ASCII escape sequences.
        """
        return json.dumps(
            self.to_dict(replay),
            ensure_ascii=False,
            indent=self.indent,
        )

    def write(
        self,
        replay: Replay,
        path: str | Path,
    ) -> Path:
        """
        Write a Replay JSON document using UTF-8 encoding.

        Missing parent directories are created automatically. Existing files
        are overwritten.
        """
        output_path = Path(path)

        if output_path.exists() and output_path.is_dir():
            raise ValueError(
                "Replay JSON path is a directory: "
                f"{output_path}"
            )

        if output_path.suffix.casefold() != ".json":
            raise ValueError(
                "Replay JSON path must use the .json extension."
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            self.to_json(replay),
            encoding="utf-8",
        )

        return output_path

    @staticmethod
    def _event_to_dict(
        event: ReplayEvent,
    ) -> ReplayEventData:
        """
        Convert one immutable ReplayEvent to JSON-compatible data.
        """
        return {
            "turn": event.turn,
            "phase": event.phase,
            "action": event.action,
            "description": event.description,
        }