from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class ManaCost:
    """
    Represents a mana cost.

    Version 1 supports generic, colored, and colorless mana.
    Hybrid, Phyrexian, snow, and X costs will be added later.
    """

    generic: int = 0
    white: int = 0
    blue: int = 0
    black: int = 0
    red: int = 0
    green: int = 0
    colorless: int = 0

    def __post_init__(self) -> None:
        values = (
            self.generic,
            self.white,
            self.blue,
            self.black,
            self.red,
            self.green,
            self.colorless,
        )

        if any(value < 0 for value in values):
            raise ValueError("Mana cost values must not be negative.")

    @property
    def total(self) -> int:
        return (
            self.generic
            + self.white
            + self.blue
            + self.black
            + self.red
            + self.green
            + self.colorless
        )

    @property
    def colored_total(self) -> int:
        return (
            self.white
            + self.blue
            + self.black
            + self.red
            + self.green
        )