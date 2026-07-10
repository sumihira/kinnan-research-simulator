from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .player import Player
from .phase import Phase


@dataclass(slots=True)
class GameState:
    """
    現在のゲーム状態を保持するクラス。

    本クラスは状態のみ保持し、
    ゲームロジックは一切持たない。
    """

    # ---------- Players ----------

    player: Optional[Player] = None

    # ---------- Turn ----------

    turn_number: int = 1

    phase: Phase = Phase.UNTAP

    active_player_index: int = 0

    # ---------- Stack ----------

    stack_size: int = 0

    # ---------- Game ----------

    game_over: bool = False

    winner: Optional[str] = None

    # ---------- Statistics ----------

    action_count: int = 0

    mana_spent: int = 0

    mana_generated: int = 0

    # ---------- Replay ----------

    seed: int | None = None

    game_id: int = 0