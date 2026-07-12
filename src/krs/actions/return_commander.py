from dataclasses import dataclass

from krs.actions.action import Action


@dataclass(slots=True, frozen=True, kw_only=True)
class ReturnCommanderAction(Action):
    """
    Return a commander permanent from the battlefield
    to its owner's command zone.

    Version 1 directly moves the commander from the battlefield.
    Graveyard and exile replacement timing is implemented later.
    """

    permanent_id: int

    def __post_init__(self) -> None:
        if self.permanent_id <= 0:
            raise ValueError(
                "Permanent ID must be greater than zero."
            )