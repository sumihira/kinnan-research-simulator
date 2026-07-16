from pathlib import Path

import pytest

from krs.decks.implementation_audit import (
    CardImplementationAuditEntry,
    CardImplementationStatus,
    DeckImplementationAudit,
)
from krs.report.deck_implementation_markdown import (
    DeckImplementationMarkdownReporter,
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
                card_name="Sol Ring",
                quantity=1,
                is_commander=False,
                has_oracle_text=True,
                status=(
                    CardImplementationStatus.CONFIGURED
                ),
            ),
            CardImplementationAuditEntry(
                card_name="Birds of Paradise",
                quantity=1,
                is_commander=False,
                has_oracle_text=True,
                status=(
                    CardImplementationStatus.ORACLE_ONLY
                ),
            ),
            CardImplementationAuditEntry(
                card_name="Bloom Tender",
                quantity=1,
                is_commander=False,
                has_oracle_text=True,
                status=(
                    CardImplementationStatus.ORACLE_ONLY
                ),
            ),
            CardImplementationAuditEntry(
                card_name="Forest",
                quantity=3,
                is_commander=False,
                has_oracle_text=False,
                status=(
                    CardImplementationStatus.ORACLE_ONLY
                ),
            ),
        ),
    )


def test_report_contains_default_title() -> None:
    markdown = (
        DeckImplementationMarkdownReporter()
        .to_markdown(create_audit())
    )

    assert markdown.startswith(
        "# Deck Implementation Audit"
    )
    assert markdown.endswith("\n")


def test_report_supports_custom_title() -> None:
    markdown = DeckImplementationMarkdownReporter(
        title="Kinnan Card Coverage",
    ).to_markdown(create_audit())

    assert markdown.startswith(
        "# Kinnan Card Coverage"
    )


def test_report_contains_coverage_summary() -> None:
    markdown = (
        DeckImplementationMarkdownReporter()
        .to_markdown(create_audit())
    )

    assert "## Coverage Summary" in markdown
    assert "| Deck | Kinnan |" in markdown
    assert "| Total cards | 7 |" in markdown
    assert "| Unique cards | 5 |" in markdown
    assert "| Configured cards | 2 |" in markdown
    assert "| Oracle-only cards | 5 |" in markdown
    assert "| Configured unique cards | 2 |" in markdown
    assert "| Oracle-only unique cards | 3 |" in markdown
    assert "| Implementation rate | 28.571% |" in markdown


def test_report_contains_configured_cards() -> None:
    markdown = (
        DeckImplementationMarkdownReporter()
        .to_markdown(create_audit())
    )

    assert "## Configured Cards" in markdown
    assert (
        "| Kinnan, Bonder Prodigy | 1 | Yes | Yes |"
        in markdown
    )
    assert "| Sol Ring | 1 | No | Yes |" in markdown


def test_report_contains_missing_cards_in_priority_order() -> None:
    markdown = (
        DeckImplementationMarkdownReporter()
        .to_markdown(create_audit())
    )

    birds_position = markdown.index(
        "| 1 | Birds of Paradise"
    )
    bloom_position = markdown.index(
        "| 2 | Bloom Tender"
    )
    forest_position = markdown.index(
        "| 3 | Forest"
    )

    assert birds_position < bloom_position < forest_position


def test_report_prioritizes_commander() -> None:
    audit = DeckImplementationAudit(
        deck_name="Kinnan",
        entries=(
            CardImplementationAuditEntry(
                card_name="Kinnan, Bonder Prodigy",
                quantity=1,
                is_commander=True,
                has_oracle_text=True,
                status=(
                    CardImplementationStatus.ORACLE_ONLY
                ),
            ),
            CardImplementationAuditEntry(
                card_name="Birds of Paradise",
                quantity=1,
                is_commander=False,
                has_oracle_text=True,
                status=(
                    CardImplementationStatus.ORACLE_ONLY
                ),
            ),
        ),
    )

    markdown = (
        DeckImplementationMarkdownReporter()
        .to_markdown(audit)
    )

    assert (
        "| 1 | Kinnan, Bonder Prodigy "
        "| 1 | Yes | Yes |"
        in markdown
    )
    assert (
        "| 2 | Birds of Paradise "
        "| 1 | No | Yes |"
        in markdown
    )


def test_report_supports_no_missing_cards() -> None:
    audit = DeckImplementationAudit(
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
        ),
    )

    markdown = (
        DeckImplementationMarkdownReporter()
        .to_markdown(audit)
    )

    assert (
        "> Every card has an executable card configuration."
        in markdown
    )


def test_report_supports_no_configured_cards() -> None:
    audit = DeckImplementationAudit(
        deck_name="Kinnan",
        entries=(
            CardImplementationAuditEntry(
                card_name="Kinnan, Bonder Prodigy",
                quantity=1,
                is_commander=True,
                has_oracle_text=True,
                status=(
                    CardImplementationStatus.ORACLE_ONLY
                ),
            ),
        ),
    )

    markdown = (
        DeckImplementationMarkdownReporter()
        .to_markdown(audit)
    )

    assert (
        "> No cards currently have executable "
        "card configurations."
        in markdown
    )


def test_write_creates_markdown_file(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "reports" / "audit.md"

    written_path = (
        DeckImplementationMarkdownReporter()
        .write(
            create_audit(),
            output_path,
        )
    )

    assert written_path == output_path
    assert output_path.exists()
    assert (
        "## Missing Card Configurations"
        in output_path.read_text(
            encoding="utf-8",
        )
    )


def test_write_rejects_invalid_extension(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "must use the .md or .markdown extension"
        ),
    ):
        (
            DeckImplementationMarkdownReporter()
            .write(
                create_audit(),
                tmp_path / "audit.txt",
            )
        )


def test_report_escapes_markdown_table_separator() -> None:
    audit = DeckImplementationAudit(
        deck_name="Kinnan | Test",
        entries=(
            CardImplementationAuditEntry(
                card_name="Kinnan | Test",
                quantity=1,
                is_commander=True,
                has_oracle_text=True,
                status=(
                    CardImplementationStatus.CONFIGURED
                ),
            ),
        ),
    )

    markdown = (
        DeckImplementationMarkdownReporter()
        .to_markdown(audit)
    )

    assert "| Deck | Kinnan \\| Test |" in markdown
    assert "| Kinnan \\| Test | 1 | Yes | Yes |" in markdown