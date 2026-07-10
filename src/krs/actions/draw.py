from dataclasses import dataclass

from .action import Action


@dataclass(slots=True, frozen=True)
class DrawAction(Action):
    amount: int = 1