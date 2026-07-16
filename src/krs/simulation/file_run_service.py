from __future__ import annotations

from dataclasses import dataclass, field
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
from krs.simulation.simulation_config import SimulationConfig
from krs.simulation.simulation_factory import SimulationFactory


@dataclass(frozen=True, slots=True)
class FileSimulationRunResult:
    """
    Stores the result of one file-based Monte Carlo simulation.

    The loaded configuration and deck are retained together with the
    implementation audit, experiment result, and generated report paths.
    """

    config: SimulationConfig
    deck: Deck
    audit: DeckImplementationAudit
    experiment: ExperimentResult
    report_paths: ExperimentReportBundlePaths
    audit_markdown_path: Path

    def __post_init__(self) -> None:
        if self.config.games != self.experiment.summary.games_requested:
            raise ValueError(
                "config.games must equal experiment games_requested."
            )

        if self.deck.name != self.audit.deck_name:
            raise ValueError(
                "deck.name must equal audit.deck_name."
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

    The service is an orchestration layer only. Deck loading, simulation,
    statistics, and report serialization remain delegated to existing
    components.
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
    ) -> FileSimulationRunResult:
        """
        Load, audit, simulate, and report one deck.

        Card configurations may be incomplete. Missing configurations are
        reported by the audit and cards without executable configuration
        remain available as Oracle-data-only cards.
        """
        output_path = Path(output_directory)

        config, deck, simulator = (
            self.simulation_factory
            .create_monte_carlo_run_from_files(
                simulation_config_path=simulation_config_path,
                deck_path=deck_path,
                card_cache_path=card_cache_path,
                card_config_directory=card_config_directory,
                deck_name=deck_name,
            )
        )

        audit = DeckImplementationAuditor(
            CardConfigLoader(
                Path(card_config_directory)
            )
        ).audit(deck)

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
            config=config,
            deck=deck,
            audit=audit,
            experiment=experiment,
            report_paths=report_paths,
            audit_markdown_path=audit_markdown_path,
        )