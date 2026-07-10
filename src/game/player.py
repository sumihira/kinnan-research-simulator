from __future__ import annotations

from dataclasses import dataclass, field

from cards.card import Card
from game.permanent import Permanent
from game.zone import Zone
from mana.mana_pool import ManaPool


@dataclass(slots=True)
class Player:
    """
    Represents a player.

    This class stores only player state.
    Game logic belongs to GameEngine.
    """

    player_id: int

    name: str = "Player"

    life: int = 40

    library: Zone[Card] = field(default_factory=Zone)

    hand: Zone[Card] = field(default_factory=Zone)

    battlefield: Zone[Permanent] = field(default_factory=Zone)

    graveyard: Zone[Card] = field(default_factory=Zone)

    exile: Zone[Card] = field(default_factory=Zone)

    command: Zone[Card] = field(default_factory=Zone)

    land_played_this_turn: int = 0

    mana_pool: ManaPool = field(default_factory=ManaPool)