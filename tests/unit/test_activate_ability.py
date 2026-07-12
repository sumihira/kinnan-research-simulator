from __future__ import annotations

import pytest

from krs.abilities.activated import ActivatedAbility
from krs.actions.activate_ability import ActivateAbilityAction
from krs.cards.card import Card
from krs.engine.action_executor import ActionExecutor
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player
from krs.mana.mana import Mana


def create_running_state(
    permanent: Permanent,
    *,
    colorless_mana: int = 3,
) -> GameState:
    state = GameState(
        players=[Player(player_id=0)],
        started=True,
        phase=Phase.MAIN,
        turn_number=1,
    )
    player = state.players[0]
    player.battlefield.add(permanent)

    if colorless_mana > 0:
        player.mana_pool.add(
            Mana.COLORLESS,
            colorless_mana,
        )

    return state


def create_basalt_monolith(
    *,
    permanent_id: int = 1,
    tapped: bool = True,
    controller_id: int = 0,
) -> Permanent:
    card = Card(
        id="basalt-monolith-id",
        name="Basalt Monolith",
        mana_cost="{3}",
        mana_value=3,
        oracle_text=(
            "Basalt Monolith doesn't untap during your untap step.\n"
            "{T}: Add {C}{C}{C}.\n"
            "{3}: Untap Basalt Monolith."
        ),
        type_line="Artifact",
        activated_abilities=(
            ActivatedAbility(
                ability_type="untap_self",
                mana_cost="{3}",
                requires_tap=False,
                parameters={},
            ),
        ),
    )

    return Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=0,
        controller_id=controller_id,
        tapped=tapped,
        summoning_sick=False,
        entered_turn=1,
    )


def create_action(
    permanent: Permanent,
    *,
    ability_index: int = 0,
) -> ActivateAbilityAction:
    return ActivateAbilityAction(
        player_id=0,
        turn_number=1,
        source=permanent,
        ability_index=ability_index,
    )


def test_activates_basalt_monolith_untap_ability() -> None:
    permanent = create_basalt_monolith()
    state = create_running_state(permanent)
    player = state.players[0]

    ActionExecutor().execute(
        state,
        create_action(permanent),
    )

    assert permanent.tapped is False
    assert player.mana_pool.total() == 0
    assert state.mana_spent == 3
    assert state.action_count == 1


def test_rejects_untap_ability_when_mana_is_insufficient() -> None:
    permanent = create_basalt_monolith()
    state = create_running_state(
        permanent,
        colorless_mana=2,
    )
    player = state.players[0]

    with pytest.raises(
        ValueError,
        match="Activated ability cost cannot be paid",
    ):
        ActionExecutor().execute(
            state,
            create_action(permanent),
        )

    assert permanent.tapped is True
    assert player.mana_pool.total() == 2
    assert state.mana_spent == 0
    assert state.action_count == 0


def test_rejects_untap_ability_when_source_is_untapped() -> None:
    permanent = create_basalt_monolith(
        tapped=False,
    )
    state = create_running_state(permanent)
    player = state.players[0]

    with pytest.raises(
        ValueError,
        match="Permanent is already untapped",
    ):
        ActionExecutor().execute(
            state,
            create_action(permanent),
        )

    assert permanent.tapped is False
    assert player.mana_pool.total() == 3
    assert state.mana_spent == 0
    assert state.action_count == 0


def test_rejects_invalid_activated_ability_index() -> None:
    permanent = create_basalt_monolith()
    state = create_running_state(permanent)
    player = state.players[0]

    with pytest.raises(
        ValueError,
        match="Activated ability not found at index 1",
    ):
        ActionExecutor().execute(
            state,
            create_action(
                permanent,
                ability_index=1,
            ),
        )

    assert permanent.tapped is True
    assert player.mana_pool.total() == 3
    assert state.mana_spent == 0
    assert state.action_count == 0


def test_rejects_ability_source_not_controlled_by_player() -> None:
    permanent = create_basalt_monolith(
        controller_id=1,
    )
    state = create_running_state(permanent)
    player = state.players[0]

    with pytest.raises(
        ValueError,
        match="Player does not control the ability source",
    ):
        ActionExecutor().execute(
            state,
            create_action(permanent),
        )

    assert permanent.tapped is True
    assert player.mana_pool.total() == 3
    assert state.mana_spent == 0
    assert state.action_count == 0


def test_rejects_unsupported_activated_ability_type() -> None:
    card = Card(
        id="unsupported-card-id",
        name="Unsupported Card",
        mana_cost="{1}",
        mana_value=1,
        oracle_text="{1}: Unsupported effect.",
        type_line="Artifact",
        activated_abilities=(
            ActivatedAbility(
                ability_type="unsupported_effect",
                mana_cost="{1}",
                requires_tap=False,
                parameters={},
            ),
        ),
    )
    permanent = Permanent(
        permanent_id=1,
        card=card,
        owner_id=0,
        controller_id=0,
        tapped=False,
        summoning_sick=False,
        entered_turn=1,
    )
    state = create_running_state(
        permanent,
        colorless_mana=1,
    )
    player = state.players[0]

    with pytest.raises(
        NotImplementedError,
        match="Unsupported activated ability type",
    ):
        ActionExecutor().execute(
            state,
            create_action(permanent),
        )

    assert permanent.tapped is False
    assert player.mana_pool.total() == 1
    assert state.mana_spent == 0
    assert state.action_count == 0


def test_rejects_activation_before_game_starts() -> None:
    permanent = create_basalt_monolith()
    state = create_running_state(permanent)
    player = state.players[0]
    state.started = False

    with pytest.raises(
        ValueError,
        match="Cannot activate an ability before the game starts",
    ):
        ActionExecutor().execute(
            state,
            create_action(permanent),
        )

    assert permanent.tapped is True
    assert player.mana_pool.total() == 3
    assert state.mana_spent == 0
    assert state.action_count == 0


def test_rejects_activation_after_game_finishes() -> None:
    permanent = create_basalt_monolith()
    state = create_running_state(permanent)
    player = state.players[0]
    state.game_over = True

    with pytest.raises(
        ValueError,
        match="Cannot activate an ability in a finished game",
    ):
        ActionExecutor().execute(
            state,
            create_action(permanent),
        )

    assert permanent.tapped is True
    assert player.mana_pool.total() == 3
    assert state.mana_spent == 0
    assert state.action_count == 0