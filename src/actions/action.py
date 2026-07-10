from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(slots=True, frozen=True)
class Action(ABC):
    """
    Base class for all game actions.

    Action objects are immutable.
    They describe what a player intends to do.
    GameEngine is responsible for executing them.
    """

    player_id: int
    turn_number: int
    action_id: UUID = field(default_factory=uuid4)