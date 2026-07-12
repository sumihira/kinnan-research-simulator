from dataclasses import dataclass

from krs.actions.action import Action


@dataclass(slots=True, frozen=True, kw_only=True)
class ActivateKinnanAction(Action):
    """
    Activate Kinnan's {5}{G}{U} ability.

    selected_card_id:
        ID of the non-Human creature selected from the top five.
        None means no card is selected.
    """

    source_permanent_id: int
    selected_card_id: str | None = None

    def __post_init__(self) -> None:
        if self.source_permanent_id <= 0:
            raise ValueError(
                "Source permanent ID must be greater than zero."
            )

        if (
            self.selected_card_id is not None
            and not self.selected_card_id.strip()
        ):
            raise ValueError(
                "Selected card ID must not be empty."
            )