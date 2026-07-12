import pytest

from krs.actions.return_commander import ReturnCommanderAction


def test_return_commander_action_stores_permanent_id() -> None:
    action = ReturnCommanderAction(
        player_id=0,
        turn_number=2,
        permanent_id=5,
    )

    assert action.permanent_id == 5


@pytest.mark.parametrize("permanent_id", [0, -1, -10])
def test_return_commander_action_rejects_invalid_id(
    permanent_id: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="Permanent ID must be greater than zero",
    ):
        ReturnCommanderAction(
            player_id=0,
            turn_number=2,
            permanent_id=permanent_id,
        )