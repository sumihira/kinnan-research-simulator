from dataclasses import dataclass

from krs.actions.action import Action
from krs.cards.card import Card
from krs.mana.mana_cost import ManaCost


@dataclass(slots=True, frozen=True, kw_only=True)
class CastCommanderAction(Action):
    """
    Cast a commander from the command zone.

    `base_cost` does not include commander tax.
    ActionExecutor calculates the current additional generic cost.
    """

    card: Card
    base_cost: ManaCost