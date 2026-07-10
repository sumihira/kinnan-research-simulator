import pytest

from krs.mana.mana import Mana
from krs.mana.mana_pool import ManaPool


def test_new_mana_pool_is_empty() -> None:
    pool = ManaPool()

    assert pool.total() == 0
    assert pool.count(Mana.WHITE) == 0
    assert pool.count(Mana.BLUE) == 0
    assert pool.count(Mana.BLACK) == 0
    assert pool.count(Mana.RED) == 0
    assert pool.count(Mana.GREEN) == 0
    assert pool.count(Mana.COLORLESS) == 0


def test_add_single_mana() -> None:
    pool = ManaPool()

    pool.add(Mana.GREEN)

    assert pool.count(Mana.GREEN) == 1
    assert pool.total() == 1


def test_add_multiple_mana() -> None:
    pool = ManaPool()

    pool.add(Mana.BLUE, 2)
    pool.add(Mana.GREEN, 3)
    pool.add(Mana.COLORLESS, 1)

    assert pool.count(Mana.BLUE) == 2
    assert pool.count(Mana.GREEN) == 3
    assert pool.count(Mana.COLORLESS) == 1
    assert pool.total() == 6


def test_add_same_mana_multiple_times() -> None:
    pool = ManaPool()

    pool.add(Mana.BLUE, 2)
    pool.add(Mana.BLUE, 3)

    assert pool.count(Mana.BLUE) == 5
    assert pool.total() == 5


def test_remove_mana() -> None:
    pool = ManaPool()
    pool.add(Mana.COLORLESS, 3)

    pool.remove(Mana.COLORLESS, 2)

    assert pool.count(Mana.COLORLESS) == 1
    assert pool.total() == 1


def test_remove_all_mana_of_one_type() -> None:
    pool = ManaPool()
    pool.add(Mana.GREEN, 2)

    pool.remove(Mana.GREEN, 2)

    assert pool.count(Mana.GREEN) == 0
    assert pool.total() == 0


def test_remove_more_mana_than_available_raises_error() -> None:
    pool = ManaPool()
    pool.add(Mana.BLUE, 1)

    with pytest.raises(ValueError, match="Not enough mana"):
        pool.remove(Mana.BLUE, 2)

    # 失敗した場合、残高が変更されていないことも確認する
    assert pool.count(Mana.BLUE) == 1


def test_remove_from_empty_pool_raises_error() -> None:
    pool = ManaPool()

    with pytest.raises(ValueError, match="Not enough mana"):
        pool.remove(Mana.GREEN)


def test_clear_removes_all_mana() -> None:
    pool = ManaPool()
    pool.add(Mana.WHITE, 1)
    pool.add(Mana.BLUE, 2)
    pool.add(Mana.GREEN, 3)
    pool.add(Mana.COLORLESS, 4)

    pool.clear()

    assert pool.total() == 0
    assert pool.count(Mana.WHITE) == 0
    assert pool.count(Mana.BLUE) == 0
    assert pool.count(Mana.GREEN) == 0
    assert pool.count(Mana.COLORLESS) == 0


def test_different_mana_types_are_stored_separately() -> None:
    pool = ManaPool()

    pool.add(Mana.BLUE, 2)
    pool.add(Mana.GREEN, 1)

    assert pool.count(Mana.BLUE) == 2
    assert pool.count(Mana.GREEN) == 1
    assert pool.count(Mana.RED) == 0
    assert pool.total() == 3


def test_repr_contains_mana_pool_name() -> None:
    pool = ManaPool()
    pool.add(Mana.BLUE, 1)

    assert "ManaPool" in repr(pool)

@pytest.mark.parametrize("amount", [0, -1, -10])
def test_add_rejects_non_positive_amount(amount: int) -> None:
    pool = ManaPool()

    with pytest.raises(
        ValueError,
        match="Mana amount must be greater than zero",
    ):
        pool.add(Mana.GREEN, amount)


@pytest.mark.parametrize("amount", [0, -1, -10])
def test_remove_rejects_non_positive_amount(amount: int) -> None:
    pool = ManaPool()
    pool.add(Mana.GREEN, 3)

    with pytest.raises(
        ValueError,
        match="Mana amount must be greater than zero",
    ):
        pool.remove(Mana.GREEN, amount)

    assert pool.count(Mana.GREEN) == 3