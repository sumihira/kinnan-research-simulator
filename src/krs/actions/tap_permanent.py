from dataclasses import dataclass

from krs.actions.action import Action
from krs.game.permanent import Permanent
from krs.mana.mana import Mana


@dataclass(slots=True, frozen=True, kw_only=True)
class TapPermanentAction(Action):
    """
    Tap a permanent to activate one of its mana abilities.

    `mana` selects the desired produced mana type when the
    ability can produce multiple types.
    """

    permanent: Permanent
    mana: Mana
    ability_index: int = 0

    def __post_init__(self) -> None:
        if self.ability_index < 0:
            raise ValueError(
                "Ability index must not be negative."
            )