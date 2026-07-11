import pytest

from krs.cards.card import Card
from krs.decks.deck import Deck


def create_card(
    card_id: str,
    name: str,
    *,
    type_line: str = "Artifact",
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line=type_line,
    )


def create_commander() -> Card:
    return create_card(
        "kinnan-id",
        "Kinnan, Bonder Prodigy",
        type_line="Legendary Creature — Human Druid",
    )


def create_main_deck(size: int = 99) -> list[Card]:
    return [
        create_card(
            f"card-{index}",
            f"Card {index}",
        )
        for index in range(size)
    ]


def test_deck_can_be_created() -> None:
    commander = create_commander()
    main_deck = create_main_deck()

    deck = Deck(
        name="Kinnan Current List",
        commander=commander,
        cards=main_deck,
    )

    assert deck.name == "Kinnan Current List"
    assert deck.commander == commander
    assert deck.cards == main_deck


def test_deck_total_card_count_includes_commander() -> None:
    deck = Deck(
        name="Kinnan",
        commander=create_commander(),
        cards=create_main_deck(),
    )

    assert deck.main_deck_count == 99
    assert deck.total_card_count == 100


def test_deck_cards_are_not_shared_between_instances() -> None:
    first = Deck(
        name="First",
        commander=create_commander(),
    )
    second = Deck(
        name="Second",
        commander=create_commander(),
    )

    first.cards.append(create_card("sol-ring", "Sol Ring"))

    assert len(first.cards) == 1
    assert len(second.cards) == 0


def test_deck_preserves_duplicate_entries() -> None:
    sol_ring = create_card("sol-ring", "Sol Ring")

    deck = Deck(
        name="Invalid Test Deck",
        commander=create_commander(),
        cards=[sol_ring, sol_ring],
    )

    assert deck.cards == [sol_ring, sol_ring]
    assert deck.main_deck_count == 2


def test_deck_can_return_all_cards() -> None:
    commander = create_commander()
    cards = [
        create_card("sol-ring", "Sol Ring"),
        create_card("basalt", "Basalt Monolith"),
    ]

    deck = Deck(
        name="Kinnan",
        commander=commander,
        cards=cards,
    )

    assert deck.all_cards == [
        commander,
        *cards,
    ]


def test_all_cards_returns_a_new_list() -> None:
    deck = Deck(
        name="Kinnan",
        commander=create_commander(),
        cards=create_main_deck(2),
    )

    result = deck.all_cards
    result.clear()

    assert deck.total_card_count == 3


def test_deck_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="Deck name must not be empty"):
        Deck(
            name="",
            commander=create_commander(),
        )