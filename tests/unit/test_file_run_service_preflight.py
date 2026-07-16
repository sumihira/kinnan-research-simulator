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
    ExperimentReportBundleWriter,
)
from krs.report.deck_implementation_markdown import (
    DeckImplementationMarkdownReporter,
)
from krs.simulation.file_run_service import (
    FileSimulationRunService,
)
from krs.simulation.monte_carlo import MonteCarloSimulator
from krs.simulation.preflight import (
    SimulationPreflightIssue,
    SimulationPreflightResult,
    SimulationPreflightValidator,
)
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
        oracle_text="Oracle text",
        type_line=type_line,
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
                has_oracle_text=True,
                status=(
                    CardImplementationStatus.CONFIGURED
                ),
            ),
        ),
    )


def create_preflight(
    *,
    ready: bool,
) -> SimulationPreflightResult:
    issues = (
        ()
        if ready
        else (
            SimulationPreflightIssue(
                code="invalid_deck_size",
                message="Deck size is invalid.",
            ),
        )
    )

    return SimulationPreflightResult(
        deck_name="Kinnan",
        total_cards=100 if ready else 2,
        main_deck_cards=99 if ready else 1,
        unique_cards=2,
        configured_unique_cards=2,
        oracle_only_unique_cards=0,
        land_cards=1,
        mana_source_cards=1,
        blue_source_cards=1,
        green_source_cards=1,
        issues=issues,
    )


def test_blocking_preflight_prevents_simulator_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = SimulationConfig(
        games=10,
    )
    deck = create_deck()
    audit = create_audit()

    simulation_factory = Mock(
        spec=SimulationFactory,
    )
    simulation_factory.load_config_and_deck.return_value = (
        config,
        deck,
    )

    report_writer = Mock(
        spec=ExperimentReportBundleWriter,
    )
    audit_reporter = Mock(
        spec=DeckImplementationMarkdownReporter,
    )
    preflight_validator = Mock(
        spec=SimulationPreflightValidator,
    )
    preflight_validator.validate.return_value = (
        create_preflight(
            ready=False,
        )
    )

    auditor = Mock()
    auditor.audit.return_value = audit

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
        preflight_validator=preflight_validator,
    )

    with pytest.raises(
        ValueError,
        match=(
            "Simulation preflight blocked execution: "
            "invalid_deck_size"
        ),
    ):
        service.run(
            simulation_config_path=tmp_path / "simulation.yaml",
            deck_path=tmp_path / "kinnan.csv",
            card_cache_path=tmp_path / "cards.json",
            card_config_directory=tmp_path / "cards",
            output_directory=tmp_path / "reports",
        )

    (
        simulation_factory
        .create_monte_carlo_simulator
        .assert_not_called()
    )
    report_writer.write.assert_not_called()
    audit_reporter.write.assert_not_called()


def test_ready_preflight_allows_simulator_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = SimulationConfig(
        games=10,
    )
    deck = create_deck()
    audit = create_audit()

    simulation_factory = Mock(
        spec=SimulationFactory,
    )
    simulation_factory.load_config_and_deck.return_value = (
        config,
        deck,
    )

    simulator = Mock(
        spec=MonteCarloSimulator,
    )
    (
        simulation_factory
        .create_monte_carlo_simulator
        .return_value
    ) = simulator

    report_writer = Mock(
        spec=ExperimentReportBundleWriter,
    )
    audit_reporter = Mock(
        spec=DeckImplementationMarkdownReporter,
    )
    preflight_validator = Mock(
        spec=SimulationPreflightValidator,
    )
    preflight_validator.validate.return_value = (
        create_preflight(
            ready=True,
        )
    )

    auditor = Mock()
    auditor.audit.return_value = audit

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
        preflight_validator=preflight_validator,
    )

    # The test stops after confirming the simulator is reached.
    simulator.run.side_effect = RuntimeError(
        "simulator reached"
    )

    with pytest.raises(
        RuntimeError,
        match="simulator reached",
    ):
        service.run(
            simulation_config_path=tmp_path / "simulation.yaml",
            deck_path=tmp_path / "kinnan.csv",
            card_cache_path=tmp_path / "cards.json",
            card_config_directory=tmp_path / "cards",
            output_directory=tmp_path / "reports",
        )

    (
        simulation_factory
        .create_monte_carlo_simulator
        .assert_called_once_with(config)
    )
    simulator.run.assert_called_once_with(
        deck,
        player_id=0,
        player_name="Player",
    )