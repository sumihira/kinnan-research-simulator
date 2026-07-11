import pytest

from krs.actions.bottom_cards import BottomCardsAction
from krs.actions.mulligan import MulliganAction


def test_mulligan_action_can_be_created() -> None:
    action = MulliganAction(
        player_id=0,
        turn_number=1,
    )

    assert action.player_id == 0
    assert action.turn_number == 1


def test_bottom_cards_action_stores_card_ids() -> None:
    action = BottomCardsAction(
        player_id=0,
        turn_number=1,
        card_ids=("card-1", "card-2"),
    )

    assert action.card_ids == (
        "card-1",
        "card-2",
    )


def test_bottom_cards_action_rejects_empty_selection() -> None:
    with pytest.raises(
        ValueError,
        match="At least one card must be selected",
    ):
        BottomCardsAction(
            player_id=0,
            turn_number=1,
            card_ids=(),
        )


def test_bottom_cards_action_rejects_duplicate_ids() -> None:
    with pytest.raises(
        ValueError,
        match="must not contain duplicates",
    ):
        BottomCardsAction(
            player_id=0,
            turn_number=1,
            card_ids=("card-1", "card-1"),
        )