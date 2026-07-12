from __future__ import annotations

from pathlib import Path

from krs.ai.evaluator import CardEvaluator
from krs.ai.kinnan_hit_selector import KinnanHitSelector
from krs.ai.strategy_config import StrategyConfig
from krs.ai.strategy_loader import StrategyLoader


class StrategyFactory:
    """
    Creates AI components from strategy configuration files.
    """

    def __init__(
        self,
        strategy_directory: str | Path = "config/strategies",
        loader: StrategyLoader | None = None,
    ) -> None:
        self._strategy_directory = Path(strategy_directory)
        self._loader = loader or StrategyLoader()

    def load_config(
        self,
        strategy_name: str,
    ) -> StrategyConfig:
        normalized_name = self._normalize_name(
            strategy_name
        )

        strategy_path = (
            self._strategy_directory
            / f"{normalized_name}.yaml"
        )

        config = self._loader.load(strategy_path)

        if config.name.casefold() != normalized_name.casefold():
            raise ValueError(
                "Strategy file name and configured name do not match: "
                f"{normalized_name} != {config.name}"
            )

        return config

    def create_kinnan_hit_selector(
        self,
        strategy_name: str,
    ) -> KinnanHitSelector:
        config = self.load_config(strategy_name)

        evaluator = CardEvaluator.from_strategy(
            config
        )

        return KinnanHitSelector(
            evaluator=evaluator
        )

    @staticmethod
    def _normalize_name(
        strategy_name: str,
    ) -> str:
        normalized = strategy_name.strip().casefold()

        if not normalized:
            raise ValueError(
                "Strategy name must not be empty."
            )

        if not all(
            character.isalnum() or character == "_"
            for character in normalized
        ):
            raise ValueError(
                "Strategy name may only contain letters, "
                "numbers, and underscores."
            )

        return normalized