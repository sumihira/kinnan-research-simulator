from dataclasses import dataclass

from krs.actions.action import Action
from krs.cards.card import Card
from krs.mana.mana_cost import ManaCost


@dataclass(slots=True, frozen=True, kw_only=True)
class CastSpellAction(Action):
    card: Card
    cost: ManaCost