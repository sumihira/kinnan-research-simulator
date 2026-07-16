from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from krs.cards.card import Card
from krs.decks.deck import Deck
from krs.decks.implementation_audit import (
    CardImplementationAuditEntry,
    CardImplementationStatus,
    DeckImplementationAudit,
)
from krs.report.bundle import (
    ExperimentReportBundlePaths,
    ExperimentReportBundleWriter,
)
from krs.report.deck_implementation_markdown import (
    DeckImplementationMarkdownReporter,
)
from krs.simulation.experiment import (
    ExperimentResult,
    SimulationSummary,
)
from krs.simulation.file_run_service import (
    FileSimulationRunResult,
    FileSimulationRunService,
)
from krs.simulation.monte_carlo import MonteCarloSimulator
from krs.simulation.simulation_config import SimulationConfig
from krs.simulation.simulation_factory import SimulationFactory


def create_card(
    *,
    card_id: str,
    name: str,
    type_line: str,
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line=type_line,
    )


def create_config() -> SimulationConfig:
    return SimulationConfig(
        strategy_name="balanced",
        games=2,
        max_turns=6,
        seed=12345,
    )


def create_deck() -> Deck:
    return Deck(
        name="Kinnan",
        commander=create_card(
            card_id="kinnan",
            name="Kinnan, Bonder Prodigy",
            type_line=(
                "Legendary Creature — Human Druid"
            ),
        ),
        cards=[
            create_card(
                card_id="forest",
                name="Forest",
                type_line="Basic Land — Forest",
            ),
        ],
    )


def create_experiment(
    config: SimulationConfig,
) -> ExperimentResult:
    return ExperimentResult(
        config=config,
        game_results=(),
        summary=SimulationSummary.from_results(
            games_requested=config.games,
            results=(),
        ),
    )


def create_audit() -> DeckImplementationAudit:
    return DeckImplementationAudit(
        deck_name="Kinnan",
        entries=(
            CardImplementationAuditEntry(
                card_name="Kinnan, Bonder Prodigy",
                quantity=1,
                is_commander=True,
                has_oracle_text=True,
                status=(
                    CardImplementationStatus.CONFIGURED
                ),
            ),
            CardImplementationAuditEntry(
                card_name="Forest",
                quantity=1,
                is_commander=False,
                has_oracle_text=False,
                status=(
                    CardImplementationStatus.ORACLE_ONLY
                ),
            ),
        ),
    )


def create_report_paths(
    output_directory: Path,
) -> ExperimentReportBundlePaths:
    return ExperimentReportBundlePaths(
        output_directory=output_directory,
        json_path=output_directory / "experiment.json",
        analysis_json_path=output_directory / "analysis.json",
        html_path=output_directory / "experiment.html",
        analysis_html_path=output_directory / "analysis.html",
        excel_path=output_directory / "experiment.xlsx",
        summary_markdown_path=output_directory / "summary.md",
        analysis_markdown_path=output_directory / "analysis.md",
        csv_summary_path=(
            output_directory / "csv" / "summary.csv"
        ),
        csv_games_path=(
            output_directory / "csv" / "games.csv"
        ),
    )


def test_run_loads_simulates_and_writes_reports(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = create_config()
    deck = create_deck()
    experiment = create_experiment(config)
    output_directory = tmp_path / "reports"
    report_paths = create_report_paths(
        output_directory
    )

    simulator = Mock(
        spec=MonteCarloSimulator,
    )
    simulator.run.return_value = experiment

    simulation_factory = Mock(
        spec=SimulationFactory,
    )
    (
        simulation_factory
        .create_monte_carlo_run_from_files
        .return_value
    ) = (
        config,
        deck,
        simulator,
    )

    report_writer = Mock(
        spec=ExperimentReportBundleWriter,
    )
    report_writer.write.return_value = report_paths

    audit_reporter = Mock(
        spec=DeckImplementationMarkdownReporter,
    )
    audit_markdown_path = (
        output_directory
        / "deck_implementation_audit.md"
    )
    audit_reporter.write.return_value = (
        audit_markdown_path
    )

    expected_audit = create_audit()

    auditor = Mock()
    auditor.audit.return_value = expected_audit

    monkeypatch.setattr(
        (
            "krs.simulation.file_run_service."
            "DeckImplementationAuditor"
        ),
        lambda loader: auditor,
    )

    service = FileSimulationRunService(
        simulation_factory=simulation_factory,
        report_writer=report_writer,
        audit_reporter=audit_reporter,
    )

    result = service.run(
        simulation_config_path=tmp_path / "simulation.yaml",
        deck_path=tmp_path / "kinnan.csv",
        card_cache_path=tmp_path / "cards.json",
        card_config_directory=tmp_path / "card_configs",
        output_directory=output_directory,
        player_id=7,
        player_name="Kinnan Player",
    )

    assert result == FileSimulationRunResult(
        config=config,
        deck=deck,
        audit=expected_audit,
        experiment=experiment,
        report_paths=report_paths,
        audit_markdown_path=audit_markdown_path,
    )

    (
        simulation_factory
        .create_monte_carlo_run_from_files
        .assert_called_once_with(
            simulation_config_path=(
                tmp_path / "simulation.yaml"
            ),
            deck_path=tmp_path / "kinnan.csv",
            card_cache_path=tmp_path / "cards.json",
            card_config_directory=(
                tmp_path / "card_configs"
            ),
            deck_name=None,
        )
    )

    simulator.run.assert_called_once_with(
        deck,
        player_id=7,
        player_name="Kinnan Player",
    )
    auditor.audit.assert_called_once_with(deck)
    report_writer.write.assert_called_once_with(
        experiment,
        output_directory,
    )
    audit_reporter.write.assert_called_once_with(
        expected_audit,
        audit_markdown_path,
    )


def test_run_forwards_deck_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = create_config()
    deck = create_deck()
    experiment = create_experiment(config)

    simulator = Mock(
        spec=MonteCarloSimulator,
    )
    simulator.run.return_value = experiment

    simulation_factory = Mock(
        spec=SimulationFactory,
    )
    (
        simulation_factory
        .create_monte_carlo_run_from_files
        .return_value
    ) = (
        config,
        deck,
        simulator,
    )

    report_writer = Mock(
        spec=ExperimentReportBundleWriter,
    )
    report_writer.write.return_value = (
        create_report_paths(tmp_path)
    )

    audit_reporter = Mock(
        spec=DeckImplementationMarkdownReporter,
    )
    audit_reporter.write.return_value = (
        tmp_path / "deck_implementation_audit.md"
    )

    auditor = Mock()
    auditor.audit.return_value = create_audit()

    monkeypatch.setattr(
        (
            "krs.simulation.file_run_service."
            "DeckImplementationAuditor"
        ),
        lambda loader: auditor,
    )

    FileSimulationRunService(
        simulation_factory=simulation_factory,
        report_writer=report_writer,
        audit_reporter=audit_reporter,
    ).run(
        simulation_config_path=tmp_path / "simulation.yaml",
        deck_path=tmp_path / "kinnan.csv",
        card_cache_path=tmp_path / "cards.json",
        card_config_directory=tmp_path / "cards",
        output_directory=tmp_path,
        deck_name="Kinnan Production",
    )

    (
        simulation_factory
        .create_monte_carlo_run_from_files
        .assert_called_once_with(
            simulation_config_path=(
                tmp_path / "simulation.yaml"
            ),
            deck_path=tmp_path / "kinnan.csv",
            card_cache_path=tmp_path / "cards.json",
            card_config_directory=tmp_path / "cards",
            deck_name="Kinnan Production",
        )
    )


def test_service_rejects_nested_audit_filename() -> None:
    with pytest.raises(
        ValueError,
        match="must be a filename only",
    ):
        FileSimulationRunService(
            audit_filename=(
                "reports/deck_implementation_audit.md"
            )
        )


def test_service_rejects_invalid_audit_extension() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "must use the .md or .markdown extension"
        ),
    ):
        FileSimulationRunService(
            audit_filename="audit.txt",
        )