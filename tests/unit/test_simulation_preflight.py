from __future__ import annotations

from types import MappingProxyType

from krs.abilities.mana_ability import ManaAbility
from krs.cards.card import Card
from krs.decks.deck import Deck
from krs.decks.implementation_audit import (
    CardImplementationAuditEntry,
    CardImplementationStatus,
    DeckImplementationAudit,
)
from krs.mana.mana import Mana
from krs.simulation.preflight import (
    SimulationPreflightValidator,
)


def create_card(
    *,
    card_id: str,
    name: str,
    type_line: str,
    oracle_text: str = "Oracle text",
    mana_abilities: tuple[ManaAbility, ...] = (),
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text=oracle_text,
        type_line=type_line,
        mana_abilities=mana_abilities,
    )


def mana_ability(
    produced_mana: dict[Mana, int],
) -> ManaAbility:
    return ManaAbility(
        produced_mana=MappingProxyType(
            produced_mana
        ),
        requires_tap=True,
    )


def create_deck() -> Deck:
    commander = create_card(
        card_id="kinnan",
        name="Kinnan, Bonder Prodigy",
        type_line="Legendary Creature — Human Druid",
    )

    cards = [
        create_card(
            card_id="forest",
            name="Forest",
            type_line="Basic Land — Forest",
            oracle_text="",
        ),
        create_card(
            card_id="island",
            name="Island",
            type_line="Basic Land — Island",
            oracle_text="",
        ),
    ]

    cards.extend(
        create_card(
            card_id=f"card-{index}",
            name=f"Card {index}",
            type_line="Creature",
        )
        for index in range(97)
    )

    return Deck(
        name="Kinnan",
        commander=commander,
        cards=cards,
    )


def create_audit(
    deck: Deck,
) -> DeckImplementationAudit:
    entries = tuple(
        CardImplementationAuditEntry(
            card_name=card.name,
            quantity=1,
            is_commander=(
                card.name
                == "Kinnan, Bonder Prodigy"
            ),
            has_oracle_text=bool(
                card.oracle_text.strip()
            ),
            status=(
                CardImplementationStatus.CONFIGURED
            ),
        )
        for card in deck.all_cards
    )

    return DeckImplementationAudit(
        deck_name=deck.name,
        entries=entries,
    )


def test_valid_deck_passes_preflight() -> None:
    deck = create_deck()
    audit = create_audit(deck)

    result = SimulationPreflightValidator().validate(
        deck=deck,
        audit=audit,
    )

    assert result.ready is True
    assert result.total_cards == 100
    assert result.main_deck_cards == 99
    assert result.blue_source_cards == 1
    assert result.green_source_cards == 1
    assert result.blocking_issues == ()


def test_invalid_deck_size_blocks_simulation() -> None:
    deck = create_deck()
    deck.cards.pop()
    audit = create_audit(deck)

    result = SimulationPreflightValidator().validate(
        deck=deck,
        audit=audit,
    )

    assert result.ready is False
    assert any(
        issue.code == "invalid_deck_size"
        for issue in result.blocking_issues
    )


def test_missing_blue_source_blocks_simulation() -> None:
    deck = create_deck()

    island = next(
        card
        for card in deck.cards
        if card.name == "Island"
    )
    deck.cards.remove(island)

    deck.cards.append(
        create_card(
            card_id="replacement",
            name="Replacement",
            type_line="Creature",
        )
    )

    audit = create_audit(deck)

    result = SimulationPreflightValidator().validate(
        deck=deck,
        audit=audit,
    )

    assert result.ready is False
    assert any(
        issue.code == "missing_blue_source"
        for issue in result.blocking_issues
    )


def test_oracle_only_cards_create_warning() -> None:
    deck = create_deck()
    audit = create_audit(deck)

    first_entry = audit.entries[1]

    updated_entries = (
        audit.entries[0],
        CardImplementationAuditEntry(
            card_name=first_entry.card_name,
            quantity=first_entry.quantity,
            is_commander=first_entry.is_commander,
            has_oracle_text=first_entry.has_oracle_text,
            status=CardImplementationStatus.ORACLE_ONLY,
        ),
        *audit.entries[2:],
    )

    partial_audit = DeckImplementationAudit(
        deck_name=audit.deck_name,
        entries=updated_entries,
    )

    result = SimulationPreflightValidator().validate(
        deck=deck,
        audit=partial_audit,
    )

    assert result.ready is True
    assert any(
        issue.code == "partial_card_implementation"
        for issue in result.warnings
    )