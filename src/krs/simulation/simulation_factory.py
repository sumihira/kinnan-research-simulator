from __future__ import annotations

from pathlib import Path

from krs.ai.strategy_factory import StrategyFactory
from krs.cards.cache import CardCache
from krs.cards.card_config_loader import CardConfigLoader
from krs.cards.card_enricher import CardEnricher
from krs.cards.card_loader import CardLoader
from krs.decks.deck import Deck
from krs.decks.deck_loader import DeckLoader
from krs.engine.game_engine import GameEngine
from krs.simulation.experiment_manager import ExperimentManager
from krs.simulation.monte_carlo import MonteCarloSimulator
from krs.simulation.simulation_config import SimulationConfig
from krs.simulation.simulation_config_loader import (
    SimulationConfigLoader,
)
from krs.simulation.simulator import GoldfishSimulator
from krs.simulation.simulator_factory import (
    GoldfishSimulatorFactory,
)


class SimulationFactory:
    """
    Builds simulation components from configuration and data files.

    The factory acts as the simulation composition root. It creates
    configuration, card caches, enriched decks, engines, simulators,
    experiment management, and the public Monte Carlo entry point.
    """

    def __init__(
        self,
        *,
        config_loader: SimulationConfigLoader | None = None,
        strategy_factory: StrategyFactory | None = None,
    ) -> None:
        self._config_loader = (
            config_loader or SimulationConfigLoader()
        )
        self._strategy_factory = (
            strategy_factory or StrategyFactory()
        )

    def load_config(
        self,
        path: str | Path,
    ) -> SimulationConfig:
        """Load one SimulationConfig from YAML."""
        return self._config_loader.load(path)

    def load_deck(
        self,
        *,
        deck_path: str | Path,
        card_cache_path: str | Path,
        card_config_directory: str | Path | None = None,
        deck_name: str | None = None,
    ) -> Deck:
        """
        Load and enrich one deck from project data files.

        Card names in the deck CSV are resolved through a local Scryfall
        JSON cache. When a card configuration directory is supplied,
        project-specific executable abilities are added through
        CardEnricher.

        Oracle text and other base card information come from the Scryfall
        cache. Executable game behavior comes from config/cards YAML.
        """
        card_cache = CardCache.load_json(
            card_cache_path
        )

        card_loader = CardLoader.from_cache(
            card_cache,
            enricher=self._create_card_enricher(
                card_config_directory
            ),
        )

        return DeckLoader(
            card_loader
        ).load_csv(
            deck_path,
            deck_name=deck_name,
        )

    def load_config_and_deck(
        self,
        *,
        simulation_config_path: str | Path,
        deck_path: str | Path,
        card_cache_path: str | Path,
        card_config_directory: str | Path | None = None,
        deck_name: str | None = None,
    ) -> tuple[SimulationConfig, Deck]:
        """
        Load the configuration and enriched deck required by a simulation.
        """
        config = self.load_config(
            simulation_config_path
        )
        deck = self.load_deck(
            deck_path=deck_path,
            card_cache_path=card_cache_path,
            card_config_directory=card_config_directory,
            deck_name=deck_name,
        )

        return config, deck

    def create_game_engine(
        self,
        config: SimulationConfig,
    ) -> GameEngine:
        """Create a strategy-configured GameEngine."""
        return GameEngine.from_strategy(
            config.strategy_name,
            strategy_factory=self._strategy_factory,
        )

    def create_simulator_factory(
        self,
        config: SimulationConfig,
    ) -> GoldfishSimulatorFactory:
        """
        Create a factory that builds isolated Goldfish simulators.

        Every generated simulator receives a fresh GameEngine configured
        through this SimulationFactory's StrategyFactory.
        """
        return GoldfishSimulatorFactory(
            config=config,
            game_engine_factory=(
                lambda: self.create_game_engine(config)
            ),
        )

    def create_goldfish_simulator(
        self,
        config: SimulationConfig,
    ) -> GoldfishSimulator:
        """Create one GoldfishSimulator."""
        simulator_factory = self.create_simulator_factory(
            config,
        )

        return simulator_factory.create()

    def create_experiment_manager(
        self,
        config: SimulationConfig,
    ) -> ExperimentManager:
        """
        Create an ExperimentManager for sequential or parallel execution.
        """
        simulator_factory = self.create_simulator_factory(
            config,
        )
        simulator = simulator_factory.create()

        return ExperimentManager(
            simulator=simulator,
            simulator_factory=simulator_factory,
        )

    def create_monte_carlo_simulator(
        self,
        config: SimulationConfig,
    ) -> MonteCarloSimulator:
        """Create the public Monte Carlo simulation entry point."""
        experiment_manager = self.create_experiment_manager(
            config,
        )

        return MonteCarloSimulator(
            experiment_manager=experiment_manager,
        )

    def create_monte_carlo_run_from_files(
        self,
        *,
        simulation_config_path: str | Path,
        deck_path: str | Path,
        card_cache_path: str | Path,
        card_config_directory: str | Path | None = None,
        deck_name: str | None = None,
    ) -> tuple[
        SimulationConfig,
        Deck,
        MonteCarloSimulator,
    ]:
        """
        Build everything required for one file-based Monte Carlo run.

        The returned simulator is ready to execute with:

            result = simulator.run(deck)
        """
        config, deck = self.load_config_and_deck(
            simulation_config_path=simulation_config_path,
            deck_path=deck_path,
            card_cache_path=card_cache_path,
            card_config_directory=card_config_directory,
            deck_name=deck_name,
        )

        simulator = self.create_monte_carlo_simulator(
            config
        )

        return config, deck, simulator

    def create_from_file(
        self,
        path: str | Path,
    ) -> tuple[SimulationConfig, GameEngine]:
        """
        Load configuration and create a GameEngine.

        This method is retained for compatibility with existing callers.
        """
        config = self.load_config(path)
        engine = self.create_game_engine(config)

        return config, engine

    def create_monte_carlo_from_file(
        self,
        path: str | Path,
    ) -> tuple[SimulationConfig, MonteCarloSimulator]:
        """
        Load configuration and create a complete Monte Carlo simulator.
        """
        config = self.load_config(path)
        simulator = self.create_monte_carlo_simulator(
            config,
        )

        return config, simulator

    @staticmethod
    def _create_card_enricher(
        card_config_directory: str | Path | None,
    ) -> CardEnricher | None:
        """
        Create a CardEnricher when executable card configs are requested.

        Omitting the directory loads base Scryfall card information only.
        """
        if card_config_directory is None:
            return None

        return CardEnricher(
            CardConfigLoader(
                Path(card_config_directory)
            )
        )