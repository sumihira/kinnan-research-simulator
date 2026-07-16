from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from krs.decks.implementation_audit import (
    CardImplementationAuditEntry,
    DeckImplementationAudit,
)


@dataclass(frozen=True, slots=True)
class DeckImplementationMarkdownReporter:
    """
    Creates a Markdown report from DeckImplementationAudit.

    The reporter presents implementation coverage and missing card
    configurations. It does not inspect cards or recalculate audit status.
    """

    title: str = "Deck Implementation Audit"

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError(
                "title must not be empty."
            )

    def to_markdown(
        self,
        audit: DeckImplementationAudit,
    ) -> str:
        """Convert one deck implementation audit to Markdown."""
        sections = (
            self._render_title(),
            self._render_summary(audit),
            self._render_configured_cards(audit),
            self._render_missing_cards(audit),
        )

        return "\n\n---\n\n".join(sections) + "\n"

    def write(
        self,
        audit: DeckImplementationAudit,
        path: str | Path,
    ) -> Path:
        """
        Write a UTF-8 Markdown implementation audit report.

        Missing parent directories are created automatically.
        """
        output_path = Path(path)

        if output_path.exists() and output_path.is_dir():
            raise ValueError(
                "Deck implementation report path is a directory: "
                f"{output_path}"
            )

        if output_path.suffix.casefold() not in {
            ".md",
            ".markdown",
        }:
            raise ValueError(
                "Deck implementation report path must use "
                "the .md or .markdown extension."
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            self.to_markdown(audit),
            encoding="utf-8",
        )

        return output_path

    def _render_title(self) -> str:
        """Render the report title."""
        return f"# {self._escape_text(self.title)}"

    def _render_summary(
        self,
        audit: DeckImplementationAudit,
    ) -> str:
        """Render deck implementation coverage values."""
        rows = (
            (
                "Deck",
                audit.deck_name,
            ),
            (
                "Total cards",
                f"{audit.total_cards:,}",
            ),
            (
                "Unique cards",
                f"{audit.unique_cards:,}",
            ),
            (
                "Configured cards",
                f"{audit.configured_cards:,}",
            ),
            (
                "Oracle-only cards",
                f"{audit.oracle_only_cards:,}",
            ),
            (
                "Configured unique cards",
                f"{audit.configured_unique_cards:,}",
            ),
            (
                "Oracle-only unique cards",
                f"{audit.oracle_only_unique_cards:,}",
            ),
            (
                "Implementation rate",
                f"{audit.implementation_rate * 100.0:.3f}%",
            ),
        )

        rendered_rows = "\n".join(
            (
                f"| {self._escape_text(metric)} "
                f"| {self._escape_text(value)} |"
            )
            for metric, value in rows
        )

        return "\n".join(
            (
                "## Coverage Summary",
                "",
                "| Metric | Value |",
                "|:--|--:|",
                rendered_rows,
            )
        )

    def _render_configured_cards(
        self,
        audit: DeckImplementationAudit,
    ) -> str:
        """Render cards that already have config/cards definitions."""
        entries = self._sorted_entries(
            audit.configured_entries
        )

        if not entries:
            content = (
                "> No cards currently have executable "
                "card configurations."
            )
        else:
            content = self._render_card_table(
                entries,
                include_priority=False,
            )

        return "\n".join(
            (
                "## Configured Cards",
                "",
                content,
            )
        )

    def _render_missing_cards(
        self,
        audit: DeckImplementationAudit,
    ) -> str:
        """
        Render cards that require config/cards definitions.

        The row number represents the recommended configuration order.
        Commander entries are first, followed by cards with Oracle text,
        and finally cards without Oracle text.
        """
        entries = self._sorted_entries(
            audit.oracle_only_entries
        )

        if not entries:
            content = (
                "> Every card has an executable card configuration."
            )
        else:
            content = self._render_card_table(
                entries,
                include_priority=True,
            )

        return "\n".join(
            (
                "## Missing Card Configurations",
                "",
                content,
            )
        )

    @classmethod
    def _render_card_table(
        cls,
        entries: tuple[
            CardImplementationAuditEntry,
            ...,
        ],
        *,
        include_priority: bool,
    ) -> str:
        """Render implementation entries as a Markdown table."""
        if include_priority:
            header = "\n".join(
                (
                    (
                        "| Priority | Card | Quantity | "
                        "Commander | Oracle |"
                    ),
                    "|--:|:--|--:|:--:|:--:|",
                )
            )
        else:
            header = "\n".join(
                (
                    (
                        "| Card | Quantity | "
                        "Commander | Oracle |"
                    ),
                    "|:--|--:|:--:|:--:|",
                )
            )

        rows = "\n".join(
            cls._render_card_row(
                entry=entry,
                priority=(
                    index
                    if include_priority
                    else None
                ),
            )
            for index, entry in enumerate(
                entries,
                start=1,
            )
        )

        return f"{header}\n{rows}"

    @classmethod
    def _render_card_row(
        cls,
        *,
        entry: CardImplementationAuditEntry,
        priority: int | None,
    ) -> str:
        """Render one card implementation row."""
        commander = cls._format_boolean(
            entry.is_commander
        )
        oracle = cls._format_boolean(
            entry.has_oracle_text
        )
        card_name = cls._escape_text(
            entry.card_name
        )

        if priority is None:
            return (
                f"| {card_name} "
                f"| {entry.quantity:,} "
                f"| {commander} "
                f"| {oracle} |"
            )

        return (
            f"| {priority:,} "
            f"| {card_name} "
            f"| {entry.quantity:,} "
            f"| {commander} "
            f"| {oracle} |"
        )

    @staticmethod
    def _sorted_entries(
        entries: tuple[
            CardImplementationAuditEntry,
            ...,
        ],
    ) -> tuple[
        CardImplementationAuditEntry,
        ...,
    ]:
        """Return entries in recommended implementation order."""
        return tuple(
            sorted(
                entries,
                key=lambda entry: (
                    not entry.is_commander,
                    not entry.has_oracle_text,
                    entry.card_name.casefold(),
                ),
            )
        )

    @staticmethod
    def _format_boolean(
        value: bool,
    ) -> str:
        """Format a boolean value for the report."""
        return "Yes" if value else "No"

    @staticmethod
    def _escape_text(
        value: str,
    ) -> str:
        """Escape Markdown table separators and line breaks."""
        return (
            str(value)
            .replace("\\", "\\\\")
            .replace("|", "\\|")
            .replace("\r\n", "<br>")
            .replace("\n", "<br>")
            .replace("\r", "<br>")
        )