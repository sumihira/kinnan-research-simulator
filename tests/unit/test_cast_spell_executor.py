import pytest

from krs.actions.cast_spell import CastSpellAction
from krs.cards.card import Card
from krs.engine.action_executor import ActionExecutor
from krs.game.game_state import GameState
from krs.game.phase import Phase
from krs.game.player import Player
from krs.mana.mana import Mana
from krs.mana.mana_cost import ManaCost
from krs.abilities.replacement import ReplacementAbility


def create_card(
    *,
    card_id: str,
    name: str,
    mana_cost: str,
    mana_value: int,
    type_line: str,
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost=mana_cost,
        mana_value=mana_value,
        oracle_text="",
        type_line=type_line,
    )


def create_running_state() -> GameState:
    return GameState(
        players=[Player(player_id=0)],
        started=True,
        phase=Phase.MAIN,
        turn_number=1,
    )


def test_cast_artifact_moves_card_to_battlefield() -> None:
    state = create_running_state()
    player = state.players[0]

    sol_ring = create_card(
        card_id="sol-ring-id",
        name="Sol Ring",
        mana_cost="{1}",
        mana_value=1,
        type_line="Artifact",
    )

    player.hand.add(sol_ring)
    player.mana_pool.add(Mana.COLORLESS)

    ActionExecutor().execute(
        state,
        CastSpellAction(
            player_id=0,
            turn_number=1,
            card=sol_ring,
            cost=ManaCost(generic=1),
        ),
    )

    assert len(player.hand) == 0
    assert len(player.battlefield) == 1

    permanent = player.battlefield.cards[0]

    assert permanent.card is sol_ring
    assert permanent.tapped is False
    assert permanent.summoning_sick is False
    assert permanent.entered_turn == 1


def test_cast_creature_enters_with_summoning_sickness() -> None:
    state = create_running_state()
    player = state.players[0]

    llanowar_elves = create_card(
        card_id="llanowar-elves-id",
        name="Llanowar Elves",
        mana_cost="{G}",
        mana_value=1,
        type_line="Creature — Elf Druid",
    )

    player.hand.add(llanowar_elves)
    player.mana_pool.add(Mana.GREEN)

    ActionExecutor().execute(
        state,
        CastSpellAction(
            player_id=0,
            turn_number=1,
            card=llanowar_elves,
            cost=ManaCost(green=1),
        ),
    )

    permanent = player.battlefield.cards[0]

    assert permanent.card is llanowar_elves
    assert permanent.summoning_sick is True
    assert permanent.entered_turn == 1


def test_cast_spell_pays_colored_and_generic_cost() -> None:
    state = create_running_state()
    player = state.players[0]

    kinnan = create_card(
        card_id="kinnan-id",
        name="Kinnan, Bonder Prodigy",
        mana_cost="{G}{U}",
        mana_value=2,
        type_line="Legendary Creature — Human Druid",
    )

    player.hand.add(kinnan)
    player.mana_pool.add(Mana.GREEN)
    player.mana_pool.add(Mana.BLUE)

    ActionExecutor().execute(
        state,
        CastSpellAction(
            player_id=0,
            turn_number=1,
            card=kinnan,
            cost=ManaCost(
                green=1,
                blue=1,
            ),
        ),
    )

    assert player.mana_pool.total() == 0
    assert state.mana_spent == 2
    assert state.action_count == 1


def test_cast_spell_assigns_permanent_id() -> None:
    state = create_running_state()
    player = state.players[0]

    sol_ring = create_card(
        card_id="sol-ring-id",
        name="Sol Ring",
        mana_cost="{1}",
        mana_value=1,
        type_line="Artifact",
    )

    player.hand.add(sol_ring)
    player.mana_pool.add(Mana.COLORLESS)

    ActionExecutor().execute(
        state,
        CastSpellAction(
            player_id=0,
            turn_number=1,
            card=sol_ring,
            cost=ManaCost(generic=1),
        ),
    )

    permanent = player.battlefield.cards[0]

    assert permanent.permanent_id == 1
    assert state.next_permanent_id == 2


def test_cast_spell_fails_when_mana_is_insufficient() -> None:
    state = create_running_state()
    player = state.players[0]

    kinnan = create_card(
        card_id="kinnan-id",
        name="Kinnan, Bonder Prodigy",
        mana_cost="{G}{U}",
        mana_value=2,
        type_line="Legendary Creature — Human Druid",
    )

    player.hand.add(kinnan)
    player.mana_pool.add(Mana.GREEN)

    with pytest.raises(
        ValueError,
        match="Mana cost cannot be paid for: Kinnan",
    ):
        ActionExecutor().execute(
            state,
            CastSpellAction(
                player_id=0,
                turn_number=1,
                card=kinnan,
                cost=ManaCost(
                    green=1,
                    blue=1,
                ),
            ),
        )

    assert list(player.hand) == [kinnan]
    assert len(player.battlefield) == 0
    assert player.mana_pool.count(Mana.GREEN) == 1
    assert state.mana_spent == 0
    assert state.action_count == 0
    assert state.next_permanent_id == 1


def test_card_not_in_hand_cannot_be_cast() -> None:
    state = create_running_state()

    sol_ring = create_card(
        card_id="sol-ring-id",
        name="Sol Ring",
        mana_cost="{1}",
        mana_value=1,
        type_line="Artifact",
    )

    with pytest.raises(
        ValueError,
        match="Card not found in hand: sol-ring-id",
    ):
        ActionExecutor().execute(
            state,
            CastSpellAction(
                player_id=0,
                turn_number=1,
                card=sol_ring,
                cost=ManaCost(generic=1),
            ),
        )


def test_land_cannot_be_cast_as_spell() -> None:
    state = create_running_state()
    player = state.players[0]

    forest = create_card(
        card_id="forest-id",
        name="Forest",
        mana_cost="",
        mana_value=0,
        type_line="Basic Land — Forest",
    )

    player.hand.add(forest)

    with pytest.raises(
        ValueError,
        match="Land cards cannot be cast as spells: Forest",
    ):
        ActionExecutor().execute(
            state,
            CastSpellAction(
                player_id=0,
                turn_number=1,
                card=forest,
                cost=ManaCost(),
            ),
        )

    assert list(player.hand) == [forest]
    assert len(player.battlefield) == 0


def test_instant_is_not_supported_yet() -> None:
    state = create_running_state()
    player = state.players[0]

    tutor = create_card(
        card_id="worldly-tutor-id",
        name="Worldly Tutor",
        mana_cost="{G}",
        mana_value=1,
        type_line="Instant",
    )

    player.hand.add(tutor)
    player.mana_pool.add(Mana.GREEN)

    with pytest.raises(
        ValueError,
        match="Only permanent spells are supported: Worldly Tutor",
    ):
        ActionExecutor().execute(
            state,
            CastSpellAction(
                player_id=0,
                turn_number=1,
                card=tutor,
                cost=ManaCost(green=1),
            ),
        )

    assert list(player.hand) == [tutor]
    assert player.mana_pool.count(Mana.GREEN) == 1


def test_permanent_spell_can_only_be_cast_in_main_phase() -> None:
    state = create_running_state()
    state.phase = Phase.DRAW

    player = state.players[0]

    sol_ring = create_card(
        card_id="sol-ring-id",
        name="Sol Ring",
        mana_cost="{1}",
        mana_value=1,
        type_line="Artifact",
    )

    player.hand.add(sol_ring)
    player.mana_pool.add(Mana.COLORLESS)

    with pytest.raises(
        ValueError,
        match="Permanent spells can only be cast during the main phase",
    ):
        ActionExecutor().execute(
            state,
            CastSpellAction(
                player_id=0,
                turn_number=1,
                card=sol_ring,
                cost=ManaCost(generic=1),
            ),
        )

    assert list(player.hand) == [sol_ring]
    assert player.mana_pool.total() == 1


def test_spell_cannot_be_cast_before_game_start() -> None:
    player = Player(player_id=0)

    sol_ring = create_card(
        card_id="sol-ring-id",
        name="Sol Ring",
        mana_cost="{1}",
        mana_value=1,
        type_line="Artifact",
    )

    player.hand.add(sol_ring)
    player.mana_pool.add(Mana.COLORLESS)

    state = GameState(
        players=[player],
        started=False,
        phase=Phase.MAIN,
    )

    with pytest.raises(
        ValueError,
        match="Cannot cast a spell before the game starts",
    ):
        ActionExecutor().execute(
            state,
            CastSpellAction(
                player_id=0,
                turn_number=1,
                card=sol_ring,
                cost=ManaCost(generic=1),
            ),
        )


def test_spell_cannot_be_cast_after_game_end() -> None:
    state = create_running_state()
    state.game_over = True

    player = state.players[0]

    sol_ring = create_card(
        card_id="sol-ring-id",
        name="Sol Ring",
        mana_cost="{1}",
        mana_value=1,
        type_line="Artifact",
    )

    player.hand.add(sol_ring)
    player.mana_pool.add(Mana.COLORLESS)

    with pytest.raises(
        ValueError,
        match="Cannot cast a spell in a finished game",
    ):
        ActionExecutor().execute(
            state,
            CastSpellAction(
                player_id=0,
                turn_number=1,
                card=sol_ring,
                cost=ManaCost(generic=1),
            ),
        )

def test_cast_roaming_throne_stores_chosen_creature_type() -> None:
    state = create_running_state()
    player = state.players[0]

    roaming_throne = Card(
        id="roaming-throne-id",
        name="Roaming Throne",
        mana_cost="{4}",
        mana_value=4,
        oracle_text=(
            "As Roaming Throne enters, choose a creature type."
        ),
        type_line="Artifact Creature — Golem",
        power="4",
        toughness="4",
        replacement_abilities=(
            ReplacementAbility(
                ability_type="choose_creature_type",
                event="enters_battlefield",
                parameters={
                    "choice_type": "creature_type",
                },
            ),
        ),
    )
    player.hand.add(roaming_throne)
    player.mana_pool.add(Mana.COLORLESS, 4)

    ActionExecutor().execute(
        state,
        CastSpellAction(
            player_id=0,
            turn_number=1,
            card=roaming_throne,
            cost=ManaCost(generic=4),
            chosen_values={
                "creature_type": "Druid",
            },
        ),
    )

    permanent = next(iter(player.battlefield))

    assert permanent.effective_card is roaming_throne
    assert permanent.chosen_values == {
        "creature_type": "Druid",
    }
    assert player.mana_pool.total() == 0
    assert len(player.hand) == 0
    assert state.mana_spent == 4
    assert state.action_count == 1


def test_cast_roaming_throne_requires_creature_type_choice() -> None:
    state = create_running_state()
    player = state.players[0]

    roaming_throne = Card(
        id="roaming-throne-id",
        name="Roaming Throne",
        mana_cost="{4}",
        mana_value=4,
        oracle_text="",
        type_line="Artifact Creature — Golem",
        power="4",
        toughness="4",
        replacement_abilities=(
            ReplacementAbility(
                ability_type="choose_creature_type",
                event="enters_battlefield",
                parameters={
                    "choice_type": "creature_type",
                },
            ),
        ),
    )
    player.hand.add(roaming_throne)
    player.mana_pool.add(Mana.COLORLESS, 4)

    with pytest.raises(
        ValueError,
        match="Required chosen value was not provided",
    ):
        ActionExecutor().execute(
            state,
            CastSpellAction(
                player_id=0,
                turn_number=1,
                card=roaming_throne,
                cost=ManaCost(generic=4),
            ),
        )

    assert player.mana_pool.total() == 4
    assert list(player.hand) == [roaming_throne]
    assert len(player.battlefield) == 0
    assert state.mana_spent == 0
    assert state.action_count == 0