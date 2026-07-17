from __future__ import annotations

from dataclasses import dataclass

from krs.report.localization import normalize_locale


@dataclass(frozen=True, slots=True, kw_only=True)
class SimulationConfig:
    """
    Configuration for one simulation run.

    The configuration controls report locale, strategy selection, game
    count, turn limits, deterministic seeds, and experiment execution
    concurrency.

    The Python-level default locale remains English for backward
    compatibility with existing tests and direct API users.

    Application YAML configuration may select Japanese as the normal
    command-line default.
    """

    locale: str = "ja"
    strategy_name: str = "balanced"
    games: int = 1_000
    max_turns: int = 6
    seed: int | None = None
    mulligan_enabled: bool = True
    save_replays: bool = False
    workers: int = 1

    def __post_init__(self) -> None:
        normalized_locale = normalize_locale(
            self.locale
        )
        normalized_strategy = (
            self.strategy_name
            .strip()
            .casefold()
        )

        if not normalized_strategy:
            raise ValueError(
                "Strategy name must not be empty."
            )

        if self.games <= 0:
            raise ValueError(
                "Number of games must be greater than zero."
            )

        if self.max_turns <= 0:
            raise ValueError(
                "Maximum turns must be greater than zero."
            )

        if self.workers <= 0:
            raise ValueError(
                "Number of workers must be greater than zero."
            )

        object.__setattr__(
            self,
            "locale",
            normalized_locale,
        )
        object.__setattr__(
            self,
            "strategy_name",
            normalized_strategy,
        )