import pytest

from krs.actions.activate_kinnan import ActivateKinnanAction


def test_activate_kinnan_action_stores_values() -> None:
    action = ActivateKinnanAction(
        player_id=0,
        turn_number=3,
        source_permanent_id=10,
        selected_card_id="creature-id",
    )

    assert action.source_permanent_id == 10
    assert action.selected_card_id == "creature-id"


def test_activate_kinnan_action_allows_no_selection() -> None:
    action = ActivateKinnanAction(
        player_id=0,
        turn_number=3,
        source_permanent_id=10,
    )

    assert action.selected_card_id is None


@pytest.mark.parametrize(
    "source_permanent_id",
    [0, -1, -10],
)
def test_activate_kinnan_rejects_invalid_source_id(
    source_permanent_id: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="Source permanent ID must be greater than zero",
    ):
        ActivateKinnanAction(
            player_id=0,
            turn_number=3,
            source_permanent_id=source_permanent_id,
        )


def test_activate_kinnan_rejects_empty_selected_card_id() -> None:
    with pytest.raises(
        ValueError,
        match="Selected card ID must not be empty",
    ):
        ActivateKinnanAction(
            player_id=0,
            turn_number=3,
            source_permanent_id=1,
            selected_card_id="",
        )