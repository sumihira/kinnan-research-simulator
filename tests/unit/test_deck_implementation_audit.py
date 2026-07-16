from pathlib import Path

import pytest

from krs.cards.card import Card
from krs.cards.card_config_loader import (
    CardConfigLoader,
)
from krs.decks.deck import Deck
from krs.decks.implementation_audit import (
    CardImplementationStatus,
    DeckImplementationAuditor,
)


def create_card(
    *,
    card_id: str,
    name: str,
    oracle_text: str,
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text=oracle_text,
        type_line="Creature",
    )


def write_config(
    directory: Path,
    *,
    filename: str,
    card_name: str,
) -> None:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        directory / filename
    ).write_text(
        (
            f"card_name: {card_name}\n"
            "abilities: {}\n"
        ),
        encoding="utf-8",
    )


def test_audit_classifies_configured_and_oracle_only_cards(
    tmp_path: Path,
) -> None:
    config_directory = tmp_path / "cards"

    write_config(
        config_directory,
        filename="kinnan.yaml",
        card_name="Kinnan, Bonder Prodigy",
    )
    write_config(
        config_directory,
        filename="sol_ring.yaml",
        card_name="Sol Ring",
    )

    deck = Deck(
        name="Kinnan",
        commander=create_card(
            card_id="kinnan",
            name="Kinnan, Bonder Prodigy",
            oracle_text="Kinnan oracle text",
        ),
        cards=[
            create_card(
                card_id="sol-ring",
                name="Sol Ring",
                oracle_text="{T}: Add {C}{C}.",
            ),
            create_card(
                card_id="birds",
                name="Birds of Paradise",
                oracle_text=(
                    "{T}: Add one mana of any color."
                ),
            ),
        ],
    )

    audit = DeckImplementationAuditor(
        CardConfigLoader(
            config_directory
        )
    ).audit(deck)

    assert audit.total_cards == 3
    assert audit.unique_cards == 3
    assert audit.configured_cards == 2
    assert audit.oracle_only_cards == 1
    assert audit.configured_unique_cards == 2
    assert audit.oracle_only_unique_cards == 1
    assert audit.implementation_rate == pytest.approx(
        2 / 3
    )

    assert audit.entries[0].card_name == (
        "Kinnan, Bonder Prodigy"
    )
    assert audit.entries[0].is_commander is True
    assert (
        audit.entries[0].status
        is CardImplementationStatus.CONFIGURED
    )

    assert (
        audit.oracle_only_entries[0].card_name
        == "Birds of Paradise"
    )
    assert (
        audit.oracle_only_entries[0].status
        is CardImplementationStatus.ORACLE_ONLY
    )


def test_audit_aggregates_duplicate_card_quantities(
    tmp_path: Path,
) -> None:
    config_directory = tmp_path / "cards"

    write_config(
        config_directory,
        filename="kinnan.yaml",
        card_name="Kinnan, Bonder Prodigy",
    )

    forest = create_card(
        card_id="forest",
        name="Forest",
        oracle_text="",
    )

    deck = Deck(
        name="Kinnan",
        commander=create_card(
            card_id="kinnan",
            name="Kinnan, Bonder Prodigy",
            oracle_text="Kinnan oracle text",
        ),
        cards=[
            forest,
            forest,
            forest,
        ],
    )

    audit = DeckImplementationAuditor(
        CardConfigLoader(
            config_directory
        )
    ).audit(deck)

    forest_entry = next(
        entry
        for entry in audit.entries
        if entry.card_name == "Forest"
    )

    assert audit.total_cards == 4
    assert audit.unique_cards == 2
    assert forest_entry.quantity == 3
    assert forest_entry.has_oracle_text is False
    assert (
        forest_entry.status
        is CardImplementationStatus.ORACLE_ONLY
    )


def test_configured_entries_are_returned_separately(
    tmp_path: Path,
) -> None:
    config_directory = tmp_path / "cards"

    write_config(
        config_directory,
        filename="kinnan.yaml",
        card_name="Kinnan, Bonder Prodigy",
    )

    deck = Deck(
        name="Kinnan",
        commander=create_card(
            card_id="kinnan",
            name="Kinnan, Bonder Prodigy",
            oracle_text="Kinnan oracle text",
        ),
        cards=[
            create_card(
                card_id="birds",
                name="Birds of Paradise",
                oracle_text=(
                    "{T}: Add one mana of any color."
                ),
            ),
        ],
    )

    audit = DeckImplementationAuditor(
        CardConfigLoader(
            config_directory
        )
    ).audit(deck)

    assert len(audit.configured_entries) == 1
    assert (
        audit.configured_entries[0].card_name
        == "Kinnan, Bonder Prodigy"
    )

    assert len(audit.oracle_only_entries) == 1
    assert (
        audit.oracle_only_entries[0].card_name
        == "Birds of Paradise"
    )


def test_audit_requires_existing_config_directory(
    tmp_path: Path,
) -> None:
    deck = Deck(
        name="Kinnan",
        commander=create_card(
            card_id="kinnan",
            name="Kinnan, Bonder Prodigy",
            oracle_text="Kinnan oracle text",
        ),
    )

    auditor = DeckImplementationAuditor(
        CardConfigLoader(
            tmp_path / "missing"
        )
    )

    with pytest.raises(
        FileNotFoundError,
        match="Card config directory not found",
    ):
        auditor.audit(deck)