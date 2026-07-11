from dataclasses import dataclass

from krs.actions.action import Action


@dataclass(slots=True, frozen=True, kw_only=True)
class BottomCardsAction(Action):
    """Put selected cards from hand on the bottom of the library."""

    card_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.card_ids:
            raise ValueError(
                "At least one card must be selected for bottoming."
            )

        if len(set(self.card_ids)) != len(self.card_ids):
            raise ValueError(
                "Bottom card IDs must not contain duplicates."
            )