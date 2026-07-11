from krs.game.player import Player
from krs.game.zone import Zone
from krs.mana.mana_pool import ManaPool


def test_player_can_be_created() -> None:
    player = Player(player_id=0)

    assert player.player_id == 0
    assert player.name == "Player"


def test_player_starts_with_40_life() -> None:
    player = Player(player_id=0)

    assert player.life == 40


def test_player_has_all_zones() -> None:
    player = Player(player_id=0)

    assert isinstance(player.library, Zone)
    assert isinstance(player.hand, Zone)
    assert isinstance(player.battlefield, Zone)
    assert isinstance(player.graveyard, Zone)
    assert isinstance(player.exile, Zone)
    assert isinstance(player.command, Zone)


def test_player_has_mana_pool() -> None:
    player = Player(player_id=0)

    assert isinstance(player.mana_pool, ManaPool)


def test_player_starts_with_no_land_played() -> None:
    player = Player(player_id=0)

    assert player.land_played_this_turn == 0


def test_players_do_not_share_zones() -> None:
    first = Player(player_id=0)
    second = Player(player_id=1)

    first.hand.add("Sol Ring")

    assert len(first.hand) == 1
    assert len(second.hand) == 0


def test_players_do_not_share_mana_pool() -> None:
    from krs.mana.mana import Mana

    first = Player(player_id=0)
    second = Player(player_id=1)

    first.mana_pool.add(Mana.GREEN)

    assert first.mana_pool.total() == 1
    assert second.mana_pool.total() == 0


def test_player_name_can_be_changed() -> None:
    player = Player(
        player_id=0,
        name="Junpei",
    )

    assert player.name == "Junpei"