from dataclasses import dataclass

from krs.actions.action import Action
from krs.game.permanent import Permanent
from krs.mana.mana import Mana


@dataclass(slots=True, frozen=True, kw_only=True)
class TapPermanentAction(Action):
    """
    Tap a permanent to produce mana.

    Version 1 initially supports basic-land mana abilities.
    """

    permanent: Permanent
    mana: Mana