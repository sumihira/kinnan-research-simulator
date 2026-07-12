import pytest

from krs.cards.card import Card
from krs.engine.game_engine import GameEngine
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player
from krs.mana.mana import Mana
from krs.abilities.static import StaticAbility

def create_card(
    card_id: str = "card-id",
    name: str = "Test Permanent",
    type_line: str = "Artifact",
    *,
    static_abilities: tuple[StaticAbility, ...] = (),
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line=type_line,
        static_abilities=static_abilities,
    )


def create_running_state(
    *,
    turn_number: int = 1,
    phase: Phase = Phase.UNTAP,
) -> GameState:
    player = Player(player_id=0)

    return GameState(
        players=[player],
        started=True,
        turn_number=turn_number,
        phase=phase,
    )


def test_start_turn_sets_phase_to_untap() -> None:
    state = create_running_state(
        phase=Phase.END,
    )

    GameEngine().start_turn(state)

    assert state.phase is Phase.UNTAP


def test_start_turn_resets_land_play_count() -> None:
    state = create_running_state()
    player = state.players[0]
    player.land_played_this_turn = 1

    GameEngine().start_turn(state)

    assert player.land_played_this_turn == 0


def test_start_turn_untaps_active_player_permanents() -> None:
    state = create_running_state()
    player = state.players[0]

    permanent = Permanent(
        permanent_id=1,
        card=create_card(),
        owner_id=0,
        controller_id=0,
        tapped=True,
        entered_turn=0,
    )
    player.battlefield.add(permanent)

    GameEngine().start_turn(state)

    assert permanent.tapped is False

def test_start_turn_does_not_untap_basalt_monolith() -> None:
    state = create_running_state()
    player = state.players[0]

    basalt_monolith = Permanent(
        permanent_id=1,
        card=create_card(
            card_id="basalt-monolith-id",
            name="Basalt Monolith",
            static_abilities=(
                StaticAbility(
                    ability_type="skip_normal_untap",
                    parameters={
                        "applies_during": "untap_step",
                    },
                ),
            ),
        ),
        owner_id=0,
        controller_id=0,
        tapped=True,
        entered_turn=0,
    )
    player.battlefield.add(basalt_monolith)

    GameEngine().start_turn(state)

    assert basalt_monolith.tapped is True


def test_start_turn_untaps_other_permanents_beside_basalt() -> None:
    state = create_running_state()
    player = state.players[0]

    basalt_monolith = Permanent(
        permanent_id=1,
        card=create_card(
            card_id="basalt-monolith-id",
            name="Basalt Monolith",
            static_abilities=(
                StaticAbility(
                    ability_type="skip_normal_untap",
                    parameters={
                        "applies_during": "untap_step",
                    },
                ),
            ),
        ),
        owner_id=0,
        controller_id=0,
        tapped=True,
        entered_turn=0,
    )
    sol_ring = Permanent(
        permanent_id=2,
        card=create_card(
            card_id="sol-ring-id",
            name="Sol Ring",
        ),
        owner_id=0,
        controller_id=0,
        tapped=True,
        entered_turn=0,
    )

    player.battlefield.add(basalt_monolith)
    player.battlefield.add(sol_ring)

    GameEngine().start_turn(state)

    assert basalt_monolith.tapped is True
    assert sol_ring.tapped is False


def test_start_turn_ignores_skip_untap_for_other_phase() -> None:
    state = create_running_state()
    player = state.players[0]

    permanent = Permanent(
        permanent_id=1,
        card=create_card(
            static_abilities=(
                StaticAbility(
                    ability_type="skip_normal_untap",
                    parameters={
                        "applies_during": "end_step",
                    },
                ),
            ),
        ),
        owner_id=0,
        controller_id=0,
        tapped=True,
        entered_turn=0,
    )
    player.battlefield.add(permanent)

    GameEngine().start_turn(state)

    assert permanent.tapped is False

def test_start_turn_removes_old_summoning_sickness() -> None:
    state = create_running_state(
        turn_number=2,
    )
    player = state.players[0]

    permanent = Permanent(
        permanent_id=1,
        card=create_card(
            type_line="Creature — Elf Druid",
        ),
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
        entered_turn=1,
    )
    player.battlefield.add(permanent)

    GameEngine().start_turn(state)

    assert permanent.summoning_sick is False


def test_start_turn_keeps_current_turn_summoning_sickness() -> None:
    state = create_running_state(
        turn_number=2,
    )
    player = state.players[0]

    permanent = Permanent(
        permanent_id=1,
        card=create_card(
            type_line="Creature — Elf Druid",
        ),
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
        entered_turn=2,
    )
    player.battlefield.add(permanent)

    GameEngine().start_turn(state)

    assert permanent.summoning_sick is True


def test_start_turn_clears_active_player_mana_pool() -> None:
    state = create_running_state()
    player = state.players[0]

    player.mana_pool.add(Mana.GREEN, 2)

    GameEngine().start_turn(state)

    assert player.mana_pool.total() == 0


@pytest.mark.parametrize(
    ("start_phase", "expected_phase"),
    [
        (Phase.UNTAP, Phase.UPKEEP),
        (Phase.UPKEEP, Phase.DRAW),
        (Phase.DRAW, Phase.MAIN),
        (Phase.MAIN, Phase.END),
    ],
)
def test_advance_phase(
    start_phase: Phase,
    expected_phase: Phase,
) -> None:
    state = create_running_state(
        phase=start_phase,
    )

    if start_phase is Phase.UPKEEP:
        state.active_player.library.cards.append(
            create_card(
                card_id="draw-card-id",
                name="Forest",
                type_line="Basic Land — Forest",
            )
        )

    GameEngine().advance_phase(state)

    assert state.phase is expected_phase


def test_advance_phase_rejects_end_phase() -> None:
    state = create_running_state(
        phase=Phase.END,
    )

    with pytest.raises(
        ValueError,
        match="Cannot advance beyond END phase",
    ):
        GameEngine().advance_phase(state)


def test_end_turn_increments_turn_number() -> None:
    state = create_running_state(
        turn_number=1,
        phase=Phase.END,
    )

    GameEngine().end_turn(state)

    assert state.turn_number == 2
    assert state.phase is Phase.UNTAP


def test_end_turn_resets_land_play_count() -> None:
    state = create_running_state(
        phase=Phase.END,
    )
    player = state.players[0]
    player.land_played_this_turn = 1

    GameEngine().end_turn(state)

    assert player.land_played_this_turn == 0


def test_end_turn_clears_all_mana_pools() -> None:
    first = Player(player_id=0)
    second = Player(player_id=1)

    first.mana_pool.add(Mana.GREEN)
    second.mana_pool.add(Mana.BLUE)

    state = GameState(
        players=[first, second],
        started=True,
        phase=Phase.END,
    )

    GameEngine().end_turn(state)

    assert first.mana_pool.total() == 0
    assert second.mana_pool.total() == 0


def test_end_turn_advances_active_player() -> None:
    first = Player(player_id=0)
    second = Player(player_id=1)

    state = GameState(
        players=[first, second],
        started=True,
        phase=Phase.END,
        active_player_index=0,
    )

    GameEngine().end_turn(state)

    assert state.active_player_index == 1
    assert state.active_player is second


def test_end_turn_wraps_active_player_index() -> None:
    first = Player(player_id=0)
    second = Player(player_id=1)

    state = GameState(
        players=[first, second],
        started=True,
        phase=Phase.END,
        active_player_index=1,
    )

    GameEngine().end_turn(state)

    assert state.active_player_index == 0
    assert state.active_player is first


def test_end_turn_requires_end_phase() -> None:
    state = create_running_state(
        phase=Phase.MAIN,
    )

    with pytest.raises(
        ValueError,
        match="only end during the END phase",
    ):
        GameEngine().end_turn(state)


def test_turn_operations_reject_unstarted_game() -> None:
    state = GameState(
        players=[Player(player_id=0)],
        started=False,
    )

    with pytest.raises(
        ValueError,
        match="Game has not started",
    ):
        GameEngine().start_turn(state)


def test_turn_operations_reject_finished_game() -> None:
    state = GameState(
        players=[Player(player_id=0)],
        started=True,
        game_over=True,
    )

    with pytest.raises(
        ValueError,
        match="Game has already finished",
    ):
        GameEngine().start_turn(state)

def test_entering_draw_phase_draws_one_card() -> None:
    state = create_running_state(
        phase=Phase.UPKEEP,
   )
    player = state.players[0]

    top_card = create_card(
        card_id="forest-id",
        name="Forest",
    type_line="Basic Land — Forest",
    )
    second_card = create_card(
        card_id="island-id",
        name="Island",
        type_line="Basic Land — Island",
    )

    player.library.cards.extend(
        [
            top_card,
            second_card,
        ]
    )

    GameEngine().advance_phase(state)

    assert state.phase is Phase.DRAW
    assert list(player.hand) == [top_card]
    assert list(player.library) == [second_card]

def test_draw_step_increments_action_count() -> None:
    state = create_running_state(
        phase=Phase.UPKEEP,
    )
    player = state.players[0]

    player.library.cards.append(
        create_card(
            card_id="forest-id",
            name="Forest",
            type_line="Basic Land — Forest",
        )
    )

    GameEngine().advance_phase(state)

    assert state.action_count == 1

def test_draw_step_draws_for_active_player_only() -> None:
    first = Player(player_id=0)
    second = Player(player_id=1)

    first.library.cards.append(
        create_card(
            card_id="forest-id",
            name="Forest",
            type_line="Basic Land — Forest",
        )
    )
    second.library.cards.append(
        create_card(
            card_id="island-id",
            name="Island",
            type_line="Basic Land — Island",
        )
    )

    state = GameState(
        players=[first, second],
        started=True,
        phase=Phase.UPKEEP,
        active_player_index=1,
    )

    GameEngine().advance_phase(state)

    assert len(first.hand) == 0
    assert [card.name for card in second.hand] == ["Island"]
    assert len(first.library) == 1
    assert len(second.library) == 0

def test_entering_non_draw_phase_does_not_draw() -> None:
    state = create_running_state(
        phase=Phase.UNTAP,
    )
    player = state.players[0]

    player.library.cards.append(
        create_card(
            card_id="forest-id",
            name="Forest",
            type_line="Basic Land — Forest",
        )
    )

    GameEngine().advance_phase(state)

    assert state.phase is Phase.UPKEEP
    assert len(player.hand) == 0
    assert len(player.library) == 1
    assert state.action_count == 0

def test_draw_step_from_empty_library_raises_error() -> None:
    state = create_running_state(
        phase=Phase.UPKEEP,
    )

    with pytest.raises(
        IndexError,
        match=r"Not enough cards in library\.",
    ):
        GameEngine().advance_phase(state)

    assert state.phase is Phase.DRAW
    assert state.action_count == 0
    assert len(state.players[0].hand) == 0

def test_first_turn_draw_step_draws_one_card() -> None:
    state = create_running_state(
        turn_number=1,
        phase=Phase.UPKEEP,
    )
    player = state.players[0]

    player.library.cards.append(
        create_card(
            card_id="forest-id",
            name="Forest",
            type_line="Basic Land — Forest",
        )
    )

    GameEngine().advance_phase(state)

    assert state.turn_number == 1
    assert state.phase is Phase.DRAW
    assert len(player.hand) == 1