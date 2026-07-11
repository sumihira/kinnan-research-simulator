from dataclasses import dataclass

from krs.actions.action import Action
from krs.cards.card import Card


@dataclass(slots=True, frozen=True, kw_only=True)
class PlayLandAction(Action):
    card: Card