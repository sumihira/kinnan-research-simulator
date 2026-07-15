from __future__ import annotations

from dataclasses import dataclass

from krs.decks.deck import Deck
from krs.simulation.experiment import ExperimentResult
from krs.simulation.experiment_manager import ExperimentManager


@dataclass(frozen=True, slots=True)
class MonteCarloDeckResult:
    """
    Stores one deck and its completed simulation experiment.

    Retaining the deck together with its result allows callers to compare
    multiple deck configurations without relying on tuple position.
    """

    deck: Deck
    experiment: ExperimentResult


@dataclass(slots=True)
class MonteCarloSimulator:
    """
    Provides the public entry point for Monte Carlo simulation.

    Game execution, concurrency, deterministic game ordering, and result
    aggregation remain delegated to ExperimentManager.
    """

    experiment_manager: ExperimentManager

    def run(
        self,
        deck: Deck,
        *,
        player_id: int = 0,
        player_name: str = "Player",
    ) -> ExperimentResult:
        """
        Run one configured Monte Carlo experiment for a deck.
        """
        return self.experiment_manager.run(
            deck,
            player_id=player_id,
            player_name=player_name,
        )

    def run_many(
        self,
        decks: tuple[Deck, ...],
        *,
        player_id: int = 0,
        player_name: str = "Player",
    ) -> tuple[MonteCarloDeckResult, ...]:
        """
        Run the configured experiment once for every supplied deck.

        Deck order is preserved in the returned tuple. Each deck experiment
        may internally execute games sequentially or concurrently according
        to its ExperimentManager configuration.
        """
        if not decks:
            raise ValueError(
                "At least one deck is required for Monte Carlo simulation."
            )

        return tuple(
            MonteCarloDeckResult(
                deck=deck,
                experiment=self.run(
                    deck,
                    player_id=player_id,
                    player_name=player_name,
                ),
            )
            for deck in decks
        )