from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from krs.simulation.simulation_config import SimulationConfig


class SimulationConfigLoader:
    """
    Loads SimulationConfig from a YAML file.

    Both the canonical keys and the legacy project keys are supported:

    - workers / parallel_workers
    - replay.enabled / save_replays

    Canonical nested or direct keys take priority when both forms are
    present.
    """

    def load(
        self,
        path: str | Path,
    ) -> SimulationConfig:
        config_path = Path(path)

        if not config_path.exists():
            raise FileNotFoundError(
                f"Simulation config file not found: {config_path}"
            )

        if not config_path.is_file():
            raise ValueError(
                f"Simulation config path is not a file: {config_path}"
            )

        with config_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            raw_data = yaml.safe_load(file)

        if raw_data is None:
            raise ValueError(
                "Simulation configuration must not be empty."
            )

        if not isinstance(raw_data, dict):
            raise ValueError(
                "Simulation configuration must be a mapping."
            )

        return self._parse(raw_data)

    def _parse(
        self,
        raw_data: dict[str, Any],
    ) -> SimulationConfig:
        strategy = raw_data.get(
            "strategy",
            "balanced",
        )
        games = raw_data.get(
            "games",
            1_000,
        )
        max_turns = raw_data.get(
            "max_turns",
            6,
        )
        seed = raw_data.get(
            "seed",
        )
        workers = self._read_workers(raw_data)

        mulligan = raw_data.get(
            "mulligan",
            {},
        )
        replay = raw_data.get(
            "replay",
            {},
        )

        if not isinstance(strategy, str):
            raise ValueError(
                "strategy must be a string."
            )

        games = self._read_integer(
            games,
            field_name="games",
        )
        max_turns = self._read_integer(
            max_turns,
            field_name="max_turns",
        )
        workers = self._read_integer(
            workers,
            field_name="workers",
        )

        if seed is not None:
            seed = self._read_integer(
                seed,
                field_name="seed",
            )

        if not isinstance(mulligan, dict):
            raise ValueError(
                "mulligan must be a mapping."
            )

        if not isinstance(replay, dict):
            raise ValueError(
                "replay must be a mapping."
            )

        mulligan_enabled = self._read_boolean(
            mulligan.get(
                "enabled",
                True,
            ),
            field_name="mulligan.enabled",
        )

        save_replays = self._read_save_replays(
            raw_data=raw_data,
            replay=replay,
        )

        return SimulationConfig(
            strategy_name=strategy,
            games=games,
            max_turns=max_turns,
            seed=seed,
            mulligan_enabled=mulligan_enabled,
            save_replays=save_replays,
            workers=workers,
        )

    @staticmethod
    def _read_workers(
        raw_data: dict[str, Any],
    ) -> Any:
        """
        Read worker count with backward-compatible key support.

        The canonical workers key takes priority over parallel_workers.
        """
        if "workers" in raw_data:
            return raw_data["workers"]

        if "parallel_workers" in raw_data:
            return raw_data["parallel_workers"]

        return 1

    def _read_save_replays(
        self,
        *,
        raw_data: dict[str, Any],
        replay: dict[str, Any],
    ) -> bool:
        """
        Read replay output configuration.

        replay.enabled takes priority over the legacy top-level
        save_replays key.
        """
        if "enabled" in replay:
            value = replay["enabled"]
            field_name = "replay.enabled"
        elif "save_replays" in raw_data:
            value = raw_data["save_replays"]
            field_name = "save_replays"
        else:
            value = False
            field_name = "replay.enabled"

        return self._read_boolean(
            value,
            field_name=field_name,
        )

    @staticmethod
    def _read_integer(
        value: Any,
        *,
        field_name: str,
    ) -> int:
        if isinstance(value, bool):
            raise ValueError(
                f"{field_name} must be an integer."
            )

        if not isinstance(value, int):
            raise ValueError(
                f"{field_name} must be an integer."
            )

        return value

    @staticmethod
    def _read_boolean(
        value: Any,
        *,
        field_name: str,
    ) -> bool:
        if not isinstance(value, bool):
            raise ValueError(
                f"{field_name} must be a boolean."
            )

        return value