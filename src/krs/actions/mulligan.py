from dataclasses import dataclass

from krs.actions.action import Action


@dataclass(slots=True, frozen=True, kw_only=True)
class MulliganAction(Action):
    """
    Return the current hand to the library, shuffle, and draw seven cards.

    Bottoming cards is handled separately by BottomCardsAction.
    """

    pass