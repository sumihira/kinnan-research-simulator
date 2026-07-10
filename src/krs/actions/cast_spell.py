from dataclasses import dataclass

from krs.cards.card import Card
from .action import Action


@dataclass(slots=True, frozen=True)
class CastSpellAction(Action):
    card: Card