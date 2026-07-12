from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from krs.ai.evaluator import CardEvaluator
from krs.ai.strategy_config import StrategyConfig


class StrategyLoader:
    """
    Loads and validates AI strategy configuration files.
    """

    def load(
        self,
        path: str | Path,
    ) -> StrategyConfig:
        config_path = Path(path)

        if not config_path.exists():
            raise FileNotFoundError(
                f"Strategy file not found: {config_path}"
            )

        if not config_path.is_file():
            raise ValueError(
                f"Strategy path is not a file: {config_path}"
            )

        with config_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            raw_data = yaml.safe_load(file)

        if raw_data is None:
            raise ValueError(
                "Strategy configuration must not be empty."
            )

        if not isinstance(raw_data, dict):
            raise ValueError(
                "Strategy configuration must be a mapping."
            )

        return self._parse(raw_data)

    def create_evaluator(
        self,
        config: StrategyConfig,
    ) -> CardEvaluator:
        return CardEvaluator(
            mana_value_weight=config.mana_value_weight,
            mana_ability_bonus=config.mana_ability_bonus,
            untap_bonus=config.untap_bonus,
            copy_bonus=config.copy_bonus,
            combo_bonus=config.combo_bonus,
            custom_scores=config.custom_scores,
            combo_card_ids=config.combo_card_ids,
        )

    def _parse(
        self,
        raw_data: dict[str, Any],
    ) -> StrategyConfig:
        name = raw_data.get("name")

        if not isinstance(name, str):
            raise ValueError(
                "Strategy configuration requires a string name."
            )

        weights = raw_data.get("weights", {})

        if not isinstance(weights, dict):
            raise ValueError(
                "Strategy weights must be a mapping."
            )

        custom_scores = raw_data.get(
            "custom_scores",
            {},
        )

        if not isinstance(custom_scores, dict):
            raise ValueError(
                "custom_scores must be a mapping."
            )

        combo_card_ids = raw_data.get(
            "combo_card_ids",
            [],
        )

        if not isinstance(combo_card_ids, list):
            raise ValueError(
                "combo_card_ids must be a list."
            )

        return StrategyConfig(
            name=name,
            mana_value_weight=self._read_number(
                weights,
                "mana_value",
                1.0,
            ),
            mana_ability_bonus=self._read_number(
                weights,
                "mana_ability",
                2.0,
            ),
            untap_bonus=self._read_number(
                weights,
                "untap",
                5.0,
            ),
            copy_bonus=self._read_number(
                weights,
                "copy",
                4.0,
            ),
            combo_bonus=self._read_number(
                weights,
                "combo",
                3.0,
            ),
            custom_scores={
                str(card_id): self._ensure_number(
                    value,
                    field_name=(
                        f"custom_scores.{card_id}"
                    ),
                )
                for card_id, value
                in custom_scores.items()
            },
            combo_card_ids=frozenset(
                str(card_id)
                for card_id in combo_card_ids
            ),
        )

    @staticmethod
    def _read_number(
        data: dict[str, Any],
        key: str,
        default: float,
    ) -> float:
        if key not in data:
            return default

        return StrategyLoader._ensure_number(
            data[key],
            field_name=f"weights.{key}",
        )

    @staticmethod
    def _ensure_number(
        value: Any,
        *,
        field_name: str,
    ) -> float:
        if isinstance(value, bool):
            raise ValueError(
                f"{field_name} must be numeric."
            )

        if not isinstance(value, int | float):
            raise ValueError(
                f"{field_name} must be numeric."
            )

        return float(value)