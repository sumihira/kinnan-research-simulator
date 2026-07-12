from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class SimulationConfig:
    """
    Configuration for one simulation run.

    Version 1 contains only the minimum fields required to build
    a GameEngine and execute Goldfish games.
    """

    strategy_name: str = "balanced"
    games: int = 1_000
    max_turns: int = 6
    seed: int | None = None
    mulligan_enabled: bool = True
    save_replays: bool = False

    def __post_init__(self) -> None:
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

        object.__setattr__(
            self,
            "strategy_name",
            normalized_strategy,
        )