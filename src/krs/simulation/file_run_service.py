from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path

from krs.cards.card_config_loader import CardConfigLoader
from krs.decks.deck import Deck
from krs.decks.implementation_audit import (
    DeckImplementationAudit,
    DeckImplementationAuditor,
)
from krs.report.bundle import (
    ExperimentReportBundlePaths,
    ExperimentReportBundleWriter,
)
from krs.report.deck_implementation_markdown import (
    DeckImplementationMarkdownReporter,
)
from krs.simulation.experiment import ExperimentResult
from krs.simulation.preflight import (
    SimulationPreflightResult,
    SimulationPreflightValidator,
)
from krs.simulation.simulation_config import SimulationConfig
from krs.simulation.simulation_factory import SimulationFactory


@dataclass(frozen=True, slots=True)
class SimulationConfigOverrides:
    """
    Optional runtime overrides for one simulation run.

    None means that the value loaded from YAML is retained.
    """

    games: int | None = None
    max_turns: int | None = None
    seed: int | None = None
    seed_is_overridden: bool = False
    workers: int | None = None

    def __post_init__(self) -> None:
        if self.games is not None and self.games < 1:
            raise ValueError(
                "games override must be at least 1."
            )

        if self.max_turns is not None and self.max_turns < 1:
            raise ValueError(
                "max_turns override must be at least 1."
            )

        if self.workers is not None and self.workers < 1:
            raise ValueError(
                "workers override must be at least 1."
            )

        if (
            self.seed is not None
            and not self.seed_is_overridden
        ):
            raise ValueError(
                "seed requires seed_is_overridden=True."
            )

    @property
    def has_overrides(self) -> bool:
        """Return whether at least one setting is overridden."""
        return (
            self.games is not None
            or self.max_turns is not None
            or self.seed_is_overridden
            or self.workers is not None
        )

    def apply(
        self,
        config: SimulationConfig,
    ) -> SimulationConfig:
        """Return a config with the requested values replaced."""
        if not self.has_overrides:
            return config

        replacement_values: dict[str, int | None] = {}

        if self.games is not None:
            replacement_values["games"] = self.games

        if self.max_turns is not None:
            replacement_values["max_turns"] = self.max_turns

        if self.seed_is_overridden:
            replacement_values["seed"] = self.seed

        if self.workers is not None:
            replacement_values["workers"] = self.workers

        return replace(
            config,
            **replacement_values,
        )


@dataclass(frozen=True, slots=True)
class FileSimulationRunResult:
    """
    Result of one file-based Monte Carlo simulation.
    """

    config: SimulationConfig
    deck: Deck
    audit: DeckImplementationAudit
    preflight: SimulationPreflightResult
    experiment: ExperimentResult
    report_paths: ExperimentReportBundlePaths
    audit_markdown_path: Path

    def __post_init__(self) -> None:
        if not self.preflight.ready:
            raise ValueError(
                "FileSimulationRunResult requires a ready preflight."
            )

        if (
            self.config.games
            != self.experiment.summary.games_requested
        ):
            raise ValueError(
                "config.games must equal experiment games_requested."
            )

        if self.deck.name != self.audit.deck_name:
            raise ValueError(
                "deck.name must equal audit.deck_name."
            )

        if self.deck.name != self.preflight.deck_name:
            raise ValueError(
                "deck.name must equal preflight.deck_name."
            )

        if (
            self.audit_markdown_path
            == self.report_paths.output_directory
        ):
            raise ValueError(
                "audit_markdown_path must be a file path."
            )

        if (
            self.report_paths.output_directory
            not in self.audit_markdown_path.parents
        ):
            raise ValueError(
                "audit_markdown_path must be inside "
                "the report output directory."
            )


@dataclass(frozen=True, slots=True)
class FileSimulationRunService:
    """
    Runs a complete simulation from project data files.

    Loading, auditing, preflight validation, Monte Carlo execution, and
    report generation are coordinated here while their implementation
    remains delegated to dedicated components.
    """

    simulation_factory: SimulationFactory = field(
        default_factory=SimulationFactory,
    )
    report_writer: ExperimentReportBundleWriter = field(
        default_factory=ExperimentReportBundleWriter,
    )
    audit_reporter: DeckImplementationMarkdownReporter = field(
        default_factory=DeckImplementationMarkdownReporter,
    )
    preflight_validator: SimulationPreflightValidator = field(
        default_factory=SimulationPreflightValidator,
    )
    audit_filename: str = "deck_implementation_audit.md"

    def __post_init__(self) -> None:
        audit_path = Path(self.audit_filename)

        if audit_path.name != self.audit_filename:
            raise ValueError(
                "audit_filename must be a filename only."
            )

        if audit_path.suffix.casefold() not in {
            ".md",
            ".markdown",
        }:
            raise ValueError(
                "audit_filename must use the .md or "
                ".markdown extension."
            )

    def run(
        self,
        *,
        simulation_config_path: str | Path,
        deck_path: str | Path,
        card_cache_path: str | Path,
        card_config_directory: str | Path,
        output_directory: str | Path,
        deck_name: str | None = None,
        player_id: int = 0,
        player_name: str = "Player",
        config_overrides: SimulationConfigOverrides | None = None,
    ) -> FileSimulationRunResult:
        """
        Load, validate, simulate, and report one deck.

        Blocking preflight issues prevent Monte Carlo execution.
        Non-blocking warnings are retained in the returned result.
        """
        output_path = Path(output_directory)
        overrides = (
            config_overrides
            or SimulationConfigOverrides()
        )

        config, deck = (
            self.simulation_factory.load_config_and_deck(
                simulation_config_path=simulation_config_path,
                deck_path=deck_path,
                card_cache_path=card_cache_path,
                card_config_directory=card_config_directory,
                deck_name=deck_name,
            )
        )

        effective_config = overrides.apply(
            config
        )

        audit = DeckImplementationAuditor(
            CardConfigLoader(
                Path(card_config_directory)
            )
        ).audit(deck)

        preflight = self.preflight_validator.validate(
            deck=deck,
            audit=audit,
        )

        self._raise_for_blocking_preflight(
            preflight
        )

        simulator = (
            self.simulation_factory
            .create_monte_carlo_simulator(
                effective_config
            )
        )

        experiment = simulator.run(
            deck,
            player_id=player_id,
            player_name=player_name,
        )

        report_paths = self.report_writer.write(
            experiment,
            output_path,
        )

        audit_markdown_path = (
            output_path / self.audit_filename
        )

        self.audit_reporter.write(
            audit,
            audit_markdown_path,
        )

        return FileSimulationRunResult(
            config=effective_config,
            deck=deck,
            audit=audit,
            preflight=preflight,
            experiment=experiment,
            report_paths=report_paths,
            audit_markdown_path=audit_markdown_path,
        )

    @staticmethod
    def _raise_for_blocking_preflight(
        preflight: SimulationPreflightResult,
    ) -> None:
        """Raise one readable error for blocking preflight issues."""
        if preflight.ready:
            return

        messages = "; ".join(
            (
                f"{issue.code}: {issue.message}"
            )
            for issue in preflight.blocking_issues
        )

        raise ValueError(
            "Simulation preflight blocked execution: "
            f"{messages}"
        )