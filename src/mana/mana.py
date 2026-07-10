from enum import Enum


class Mana(Enum):
    WHITE = "W"
    BLUE = "U"
    BLACK = "B"
    RED = "R"
    GREEN = "G"
    COLORLESS = "C"

    def __str__(self) -> str:
        return self.value