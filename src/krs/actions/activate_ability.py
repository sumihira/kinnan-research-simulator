from dataclasses import dataclass

from krs.actions.action import Action
from krs.game.permanent import Permanent


@dataclass(slots=True, frozen=True, kw_only=True)
class ActivateAbilityAction(Action):
    source: Permanent
    ability_index: int = 0