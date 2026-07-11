import random

import pytest

from krs.game.library import Library


def test_new_library_is_empty() -> None:
    library: Library[str] = Library()

    assert len(library) == 0
    assert list(library) == []


def test_draw_removes_top_card() -> None:
    library = Library(
        cards=[
            "Forest",
            "Island",
            "Sol Ring",
        ]
    )

    drawn = library.draw()

    assert drawn == "Forest"
    assert list(library) == [
        "Island",
        "Sol Ring",
    ]


def test_draw_from_empty_library_raises_error() -> None:
    library: Library[str] = Library()

    with pytest.raises(
        IndexError,
        match="Cannot draw from an empty library",
    ):
        library.draw()


def test_draw_many_preserves_top_order() -> None:
    library = Library(
        cards=[
            "Forest",
            "Island",
            "Sol Ring",
            "Kinnan",
        ]
    )

    drawn = library.draw_many(3)

    assert drawn == [
        "Forest",
        "Island",
        "Sol Ring",
    ]
    assert list(library) == ["Kinnan"]


def test_draw_many_rejects_negative_amount() -> None:
    library = Library(cards=["Forest"])

    with pytest.raises(
        ValueError,
        match="Draw amount must not be negative",
    ):
        library.draw_many(-1)


def test_draw_many_is_atomic_when_not_enough_cards() -> None:
    library = Library(
        cards=[
            "Forest",
            "Island",
        ]
    )

    with pytest.raises(
        IndexError,
        match="Not enough cards in library",
    ):
        library.draw_many(3)

    assert list(library) == [
        "Forest",
        "Island",
    ]


def test_peek_does_not_remove_cards() -> None:
    library = Library(
        cards=[
            "Forest",
            "Island",
            "Sol Ring",
        ]
    )

    result = library.peek(2)

    assert result == [
        "Forest",
        "Island",
    ]
    assert list(library) == [
        "Forest",
        "Island",
        "Sol Ring",
    ]


def test_peek_returns_new_list() -> None:
    library = Library(
        cards=[
            "Forest",
            "Island",
        ]
    )

    result = library.peek(2)
    result.clear()

    assert list(library) == [
        "Forest",
        "Island",
    ]


def test_peek_more_than_library_size_returns_all_cards() -> None:
    library = Library(
        cards=[
            "Forest",
            "Island",
        ]
    )

    assert library.peek(5) == [
        "Forest",
        "Island",
    ]


def test_put_on_bottom_appends_card() -> None:
    library = Library(cards=["Forest"])

    library.put_on_bottom("Island")

    assert list(library) == [
        "Forest",
        "Island",
    ]


def test_put_many_on_bottom_preserves_order() -> None:
    library = Library(cards=["Forest"])

    library.put_many_on_bottom(
        [
            "Island",
            "Sol Ring",
        ]
    )

    assert list(library) == [
        "Forest",
        "Island",
        "Sol Ring",
    ]


def test_add_on_top_inserts_card_at_top() -> None:
    library = Library(
        cards=[
            "Island",
            "Sol Ring",
        ]
    )

    library.add_on_top("Forest")

    assert list(library) == [
        "Forest",
        "Island",
        "Sol Ring",
    ]


def test_shuffle_is_reproducible_with_same_seed() -> None:
    cards = [str(index) for index in range(20)]

    first = Library(cards=list(cards))
    second = Library(cards=list(cards))

    first.shuffle(random.Random(12345))
    second.shuffle(random.Random(12345))

    assert list(first) == list(second)


def test_shuffle_changes_order() -> None:
    cards = [str(index) for index in range(20)]
    library = Library(cards=list(cards))

    library.shuffle(random.Random(12345))

    assert list(library) != cards