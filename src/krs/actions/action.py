from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(slots=True, frozen=True, kw_only=True)
class Action(ABC):
    """
    Immutable description of a game action.

    GameEngine is responsible for applying the action to GameState.
    """

    player_id: int
    turn_number: int
    action_id: UUID = field(default_factory=uuid4)