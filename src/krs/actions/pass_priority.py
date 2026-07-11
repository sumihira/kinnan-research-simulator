from dataclasses import dataclass

from krs.actions.action import Action


@dataclass(slots=True, frozen=True, kw_only=True)
class PassPriorityAction(Action):
    pass