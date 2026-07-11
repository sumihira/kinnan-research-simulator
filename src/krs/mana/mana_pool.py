from __future__ import annotations

from collections import Counter

from krs.mana.mana import Mana
from krs.mana.mana_cost import ManaCost


class ManaPool:
    """
    Floating mana currently available.

    ManaPool manages the current mana balance and mana-cost payment.
    """

    _GENERIC_PAYMENT_ORDER = (
        Mana.COLORLESS,
        Mana.WHITE,
        Mana.BLUE,
        Mana.BLACK,
        Mana.RED,
        Mana.GREEN,
    )

    def __init__(self) -> None:
        self._mana: Counter[Mana] = Counter()

    def add(self, mana: Mana, amount: int = 1) -> None:
        if amount <= 0:
            raise ValueError("Mana amount must be greater than zero.")

        self._mana[mana] += amount

    def remove(self, mana: Mana, amount: int = 1) -> None:
        if amount <= 0:
            raise ValueError("Mana amount must be greater than zero.")

        if self._mana[mana] < amount:
            raise ValueError("Not enough mana.")

        self._mana[mana] -= amount

    def count(self, mana: Mana) -> int:
        return self._mana[mana]

    def clear(self) -> None:
        self._mana.clear()

    def total(self) -> int:
        return sum(self._mana.values())

    def can_pay(self, cost: ManaCost) -> bool:
        """
        Return whether this pool can pay the specified mana cost.

        Colored and colorless requirements are reserved first.
        Generic cost is then paid from the remaining mana.
        """
        return self._create_payment_plan(cost) is not None

    def pay(self, cost: ManaCost) -> None:
        """
        Pay a mana cost atomically.

        If payment is impossible, the mana pool is not modified.
        """
        payment_plan = self._create_payment_plan(cost)

        if payment_plan is None:
            raise ValueError("Mana cost cannot be paid.")

        for mana, amount in payment_plan.items():
            self._mana[mana] -= amount

    def _create_payment_plan(
        self,
        cost: ManaCost,
    ) -> Counter[Mana] | None:
        available = self._mana.copy()
        payment: Counter[Mana] = Counter()

        required_mana = {
            Mana.WHITE: cost.white,
            Mana.BLUE: cost.blue,
            Mana.BLACK: cost.black,
            Mana.RED: cost.red,
            Mana.GREEN: cost.green,
            Mana.COLORLESS: cost.colorless,
        }

        # 色マナおよび無色マナの固定要求を先に支払う
        for mana, required_amount in required_mana.items():
            if available[mana] < required_amount:
                return None

            available[mana] -= required_amount
            payment[mana] += required_amount

        # 残ったマナから不特定マナを支払う
        generic_remaining = cost.generic

        for mana in self._GENERIC_PAYMENT_ORDER:
            if generic_remaining == 0:
                break

            amount = min(available[mana], generic_remaining)

            available[mana] -= amount
            payment[mana] += amount
            generic_remaining -= amount

        if generic_remaining > 0:
            return None

        return payment

    def __repr__(self) -> str:
        return f"ManaPool({dict(self._mana)})"