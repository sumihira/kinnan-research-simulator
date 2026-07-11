import pytest

from krs.game.phase import Phase
from krs.game.turn import Turn


@pytest.mark.parametrize(
    ("current_phase", "expected_phase"),
    [
        (Phase.UNTAP, Phase.UPKEEP),
        (Phase.UPKEEP, Phase.DRAW),
        (Phase.DRAW, Phase.MAIN),
        (Phase.MAIN, Phase.END),
    ],
)
def test_next_phase_returns_expected_phase(
    current_phase: Phase,
    expected_phase: Phase,
) -> None:
    assert Turn.next_phase(current_phase) is expected_phase


def test_end_phase_has_no_next_phase() -> None:
    with pytest.raises(
        ValueError,
        match="END phase has no next phase",
    ):
        Turn.next_phase(Phase.END)