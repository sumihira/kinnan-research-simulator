import pytest

from krs.actions.draw import DrawAction


def test_draw_action_defaults_to_one_card() -> None:
    action = DrawAction(
        player_id=0,
        turn_number=1,
    )

    assert action.amount == 1


@pytest.mark.parametrize("amount", [1, 2, 7])
def test_draw_action_accepts_positive_amount(
    amount: int,
) -> None:
    action = DrawAction(
        player_id=0,
        turn_number=1,
        amount=amount,
    )

    assert action.amount == amount


@pytest.mark.parametrize("amount", [0, -1, -10])
def test_draw_action_rejects_non_positive_amount(
    amount: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="Draw amount must be greater than zero",
    ):
        DrawAction(
            player_id=0,
            turn_number=1,
            amount=amount,
        )