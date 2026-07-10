from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from cards.card import Card


@dataclass(slots=True)
class Permanent:
    """
    Runtime representation of a permanent on the battlefield.

    Permanent stores mutable game state.
    Card itself is immutable.
    """

    card: Card

    # Ownership

    owner_id: int

    controller_id: int

    # State

    tapped: bool = False

    summoning_sick: bool = True

    is_token: bool = False

    # Copy

    copied_from: Optional[Card] = None

    # Turn Information

    entered_turn: int = 0

    # Counters

    counters: dict[str, int] = field(default_factory=dict)

    permanent_id: int