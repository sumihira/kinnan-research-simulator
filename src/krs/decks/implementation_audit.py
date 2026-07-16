from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum

from krs.cards.cache import CardCache
from krs.cards.card import Card
from krs.cards.card_config_loader import CardConfigLoader
from krs.decks.deck import Deck


class CardImplementationStatus(StrEnum):
    """Implementation state of one card name in a loaded deck."""

    CONFIGURED = "configured"
    ORACLE_ONLY = "oracle_only"


@dataclass(frozen=True, slots=True)
class CardImplementationAuditEntry:
    """Audit information for one unique card name in a deck."""

    card_name: str
    quantity: int
    is_commander: bool
    has_oracle_text: bool
    status: CardImplementationStatus

    def __post_init__(self) -> None:
        if not self.card_name.strip():
            raise ValueError(
                "card_name must not be empty."
            )

        if self.quantity < 1:
            raise ValueError(
                "quantity must be at least 1."
            )

    @property
    def has_executable_config(self) -> bool:
        """Return whether the card has a config/cards definition."""
        return (
            self.status
            is CardImplementationStatus.CONFIGURED
        )


@dataclass(frozen=True, slots=True)
class DeckImplementationAudit:
    """Immutable implementation coverage report for one loaded deck."""

    deck_name: str
    entries: tuple[
        CardImplementationAuditEntry,
        ...,
    ]

    def __post_init__(self) -> None:
        if not self.deck_name.strip():
            raise ValueError(
                "deck_name must not be empty."
            )

        normalized_names = tuple(
            CardCache.normalize_name(
                entry.card_name
            )
            for entry in self.entries
        )

        if (
            len(normalized_names)
            != len(set(normalized_names))
        ):
            raise ValueError(
                "Audit entries must have unique card names."
            )

        commander_count = sum(
            entry.is_commander
            for entry in self.entries
        )

        if commander_count != 1:
            raise ValueError(
                "Audit must contain exactly one commander."
            )

    @property
    def total_cards(self) -> int:
        """Return total card quantity including the commander."""
        return sum(
            entry.quantity
            for entry in self.entries
        )

    @property
    def unique_cards(self) -> int:
        """Return the number of unique card names."""
        return len(self.entries)

    @property
    def configured_cards(self) -> int:
        """Return total quantity backed by card configuration."""
        return sum(
            entry.quantity
            for entry in self.entries
            if entry.has_executable_config
        )

    @property
    def oracle_only_cards(self) -> int:
        """Return total quantity without executable configuration."""
        return (
            self.total_cards
            - self.configured_cards
        )

    @property
    def configured_unique_cards(self) -> int:
        """Return unique card names backed by configuration."""
        return sum(
            entry.has_executable_config
            for entry in self.entries
        )

    @property
    def oracle_only_unique_cards(self) -> int:
        """Return unique card names without configuration."""
        return (
            self.unique_cards
            - self.configured_unique_cards
        )

    @property
    def implementation_rate(self) -> float:
        """Return quantity-weighted implementation coverage."""
        if self.total_cards == 0:
            return 0.0

        return (
            self.configured_cards
            / self.total_cards
        )

    @property
    def configured_entries(
        self,
    ) -> tuple[
        CardImplementationAuditEntry,
        ...,
    ]:
        """Return cards with executable configuration."""
        return tuple(
            entry
            for entry in self.entries
            if entry.has_executable_config
        )

    @property
    def oracle_only_entries(
        self,
    ) -> tuple[
        CardImplementationAuditEntry,
        ...,
    ]:
        """Return cards that currently have Oracle data only."""
        return tuple(
            entry
            for entry in self.entries
            if not entry.has_executable_config
        )


@dataclass(frozen=True, slots=True)
class DeckImplementationAuditor:
    """Builds implementation coverage reports for enriched decks."""

    card_config_loader: CardConfigLoader

    def audit(
        self,
        deck: Deck,
    ) -> DeckImplementationAudit:
        """Audit one loaded deck against config/cards."""
        quantities = Counter(
            CardCache.normalize_name(card.name)
            for card in deck.all_cards
        )

        cards_by_name = (
            self._cards_by_normalized_name(deck)
        )

        commander_name = CardCache.normalize_name(
            deck.commander.name
        )

        entries = tuple(
            self._create_entry(
                card=cards_by_name[normalized_name],
                quantity=quantity,
                is_commander=(
                    normalized_name
                    == commander_name
                ),
            )
            for normalized_name, quantity
            in sorted(
                quantities.items(),
                key=lambda item: (
                    item[0] != commander_name,
                    cards_by_name[
                        item[0]
                    ].name.casefold(),
                ),
            )
        )

        return DeckImplementationAudit(
            deck_name=deck.name,
            entries=entries,
        )

    def _create_entry(
        self,
        *,
        card: Card,
        quantity: int,
        is_commander: bool,
    ) -> CardImplementationAuditEntry:
        config = (
            self.card_config_loader
            .load_by_card_name(card.name)
        )

        status = (
            CardImplementationStatus.CONFIGURED
            if config is not None
            else CardImplementationStatus.ORACLE_ONLY
        )

        return CardImplementationAuditEntry(
            card_name=card.name,
            quantity=quantity,
            is_commander=is_commander,
            has_oracle_text=bool(
                card.oracle_text.strip()
            ),
            status=status,
        )

    @staticmethod
    def _cards_by_normalized_name(
        deck: Deck,
    ) -> dict[str, Card]:
        cards_by_name: dict[str, Card] = {}

        for card in deck.all_cards:
            normalized_name = (
                CardCache.normalize_name(
                    card.name
                )
            )

            cards_by_name.setdefault(
                normalized_name,
                card,
            )

        return cards_by_name