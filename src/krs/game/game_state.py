from __future__ import annotations

from dataclasses import dataclass, field

from krs.game.phase import Phase
from krs.game.player import Player


@dataclass(slots=True)
class GameState:
    players: list[Player] = field(default_factory=list)

    turn_number: int = 1
    phase: Phase = Phase.UNTAP
    active_player_index: int = 0

    started: bool = False

    stack_size: int = 0

    game_over: bool = False
    winner: str | None = None

    action_count: int = 0
    mana_spent: int = 0
    mana_generated: int = 0

    seed: int | None = None
    game_id: int = 0

    @property
    def active_player(self) -> Player | None:
        if not 0 <= self.active_player_index < len(self.players):
            return None

        return self.players[self.active_player_index]