from dataclasses import dataclass

from krs.actions.action import Action


@dataclass(slots=True, frozen=True, kw_only=True)
class DrawAction(Action):
    amount: int = 1

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError(
                "Draw amount must be greater than zero."
            )