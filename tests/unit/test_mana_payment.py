import pytest

from krs.mana.mana import Mana
from krs.mana.mana_cost import ManaCost
from krs.mana.mana_pool import ManaPool


def test_can_pay_exact_colored_cost() -> None:
    pool = ManaPool()
    pool.add(Mana.BLUE)
    pool.add(Mana.GREEN)

    cost = ManaCost(blue=1, green=1)

    assert pool.can_pay(cost) is True


def test_cannot_pay_when_required_color_is_missing() -> None:
    pool = ManaPool()
    pool.add(Mana.BLUE, 2)

    cost = ManaCost(blue=1, green=1)

    assert pool.can_pay(cost) is False


def test_generic_cost_can_be_paid_with_any_mana() -> None:
    pool = ManaPool()
    pool.add(Mana.BLUE)
    pool.add(Mana.GREEN)
    pool.add(Mana.COLORLESS)

    cost = ManaCost(generic=3)

    assert pool.can_pay(cost) is True


def test_colorless_requirement_requires_colorless_mana() -> None:
    pool = ManaPool()
    pool.add(Mana.BLUE, 2)

    cost = ManaCost(colorless=1)

    assert pool.can_pay(cost) is False


def test_generic_cost_can_use_colorless_mana() -> None:
    pool = ManaPool()
    pool.add(Mana.COLORLESS, 2)

    cost = ManaCost(generic=2)

    assert pool.can_pay(cost) is True


def test_pay_removes_exact_colored_mana() -> None:
    pool = ManaPool()
    pool.add(Mana.BLUE, 2)
    pool.add(Mana.GREEN, 1)

    pool.pay(ManaCost(blue=1, green=1))

    assert pool.count(Mana.BLUE) == 1
    assert pool.count(Mana.GREEN) == 0
    assert pool.total() == 1


def test_pay_reserves_colored_requirements_before_generic() -> None:
    pool = ManaPool()
    pool.add(Mana.BLUE, 1)
    pool.add(Mana.COLORLESS, 2)

    pool.pay(ManaCost(generic=2, blue=1))

    assert pool.total() == 0


def test_generic_payment_uses_colorless_first() -> None:
    pool = ManaPool()
    pool.add(Mana.COLORLESS, 1)
    pool.add(Mana.BLUE, 1)
    pool.add(Mana.GREEN, 1)

    pool.pay(ManaCost(generic=1))

    assert pool.count(Mana.COLORLESS) == 0
    assert pool.count(Mana.BLUE) == 1
    assert pool.count(Mana.GREEN) == 1


def test_pay_handles_kinnan_activation_cost() -> None:
    pool = ManaPool()
    pool.add(Mana.COLORLESS, 5)
    pool.add(Mana.GREEN, 1)
    pool.add(Mana.BLUE, 1)

    cost = ManaCost(
        generic=5,
        green=1,
        blue=1,
    )

    assert pool.can_pay(cost) is True

    pool.pay(cost)

    assert pool.total() == 0


def test_pay_fails_when_total_mana_is_insufficient() -> None:
    pool = ManaPool()
    pool.add(Mana.BLUE, 1)
    pool.add(Mana.GREEN, 1)

    cost = ManaCost(
        generic=1,
        blue=1,
        green=1,
    )

    assert pool.can_pay(cost) is False

    with pytest.raises(ValueError, match="Mana cost cannot be paid"):
        pool.pay(cost)


def test_failed_payment_does_not_modify_pool() -> None:
    pool = ManaPool()
    pool.add(Mana.BLUE, 2)

    cost = ManaCost(
        blue=1,
        green=1,
    )

    with pytest.raises(ValueError):
        pool.pay(cost)

    assert pool.count(Mana.BLUE) == 2
    assert pool.count(Mana.GREEN) == 0
    assert pool.total() == 2


def test_zero_cost_can_always_be_paid() -> None:
    pool = ManaPool()

    assert pool.can_pay(ManaCost()) is True

    pool.pay(ManaCost())

    assert pool.total() == 0