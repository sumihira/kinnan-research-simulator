from krs.actions.action import Action
from krs.cards.card import Card
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player
from krs.game.zone import Zone
from krs.mana.mana import Mana
from krs.mana.mana_pool import ManaPool


def test_core_modules_can_be_imported() -> None:
    assert Action is not None
    assert Card is not None
    assert GameState is not None
    assert Permanent is not None
    assert Phase is not None
    assert Player is not None
    assert Zone is not None
    assert Mana is not None
    assert ManaPool is not None