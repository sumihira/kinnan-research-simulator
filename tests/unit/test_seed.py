from __future__ import annotations

import pytest

from krs.simulation.seed import derive_game_seed


def test_derive_game_seed_uses_base_seed_for_first_game() -> None:
    result = derive_game_seed(
        base_seed=12345,
        game_id=0,
    )

    assert result == 12345


def test_derive_game_seed_adds_game_id() -> None:
    result = derive_game_seed(
        base_seed=12345,
        game_id=7,
    )

    assert result == 12352


def test_derive_game_seed_returns_none_without_base_seed() -> None:
    result = derive_game_seed(
        base_seed=None,
        game_id=100,
    )

    assert result is None


def test_derive_game_seed_is_reproducible() -> None:
    first = derive_game_seed(
        base_seed=500,
        game_id=20,
    )
    second = derive_game_seed(
        base_seed=500,
        game_id=20,
    )

    assert first == second


def test_derive_game_seed_produces_different_game_seeds() -> None:
    first = derive_game_seed(
        base_seed=500,
        game_id=20,
    )
    second = derive_game_seed(
        base_seed=500,
        game_id=21,
    )

    assert first != second


@pytest.mark.parametrize(
    "game_id",
    [
        -1,
        -10,
        -100,
    ],
)
def test_derive_game_seed_rejects_negative_game_id(
    game_id: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="game_id must not be negative.",
    ):
        derive_game_seed(
            base_seed=500,
            game_id=game_id,
        )