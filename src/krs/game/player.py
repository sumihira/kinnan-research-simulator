from __future__ import annotations

from dataclasses import dataclass, field

from krs.cards.card import Card
from krs.game.library import Library
from krs.game.permanent import Permanent
from krs.game.zone import Zone
from krs.mana.mana_pool import ManaPool


@dataclass(slots=True)
class Player:
    """Stores player state. Game logic belongs to GameEngine."""

    player_id: int
    name: str = "Player"
    life: int = 40

    library: Library[Card] = field(default_factory=Library)
    hand: Zone[Card] = field(default_factory=Zone)
    battlefield: Zone[Permanent] = field(default_factory=Zone)
    graveyard: Zone[Card] = field(default_factory=Zone)
    exile: Zone[Card] = field(default_factory=Zone)
    command: Zone[Card] = field(default_factory=Zone)

    mana_pool: ManaPool = field(default_factory=ManaPool)

    land_played_this_turn: int = 0
    mulligan_count: int = 0
    commander_cast_count: int = 0