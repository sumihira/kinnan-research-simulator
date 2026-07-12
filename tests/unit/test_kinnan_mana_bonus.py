from krs.abilities.mana_ability import ManaAbility
from krs.actions.tap_permanent import TapPermanentAction
from krs.cards.card import Card
from krs.engine.action_executor import ActionExecutor
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player
from krs.mana.mana import Mana


def create_running_state() -> GameState:
    return GameState(
        players=[Player(player_id=0)],
        started=True,
        phase=Phase.MAIN,
        turn_number=1,
    )


def create_kinnan(
    permanent_id: int = 1,
) -> Permanent:
    card = Card(
        id="kinnan-id",
        name="Kinnan, Bonder Prodigy",
        mana_cost="{G}{U}",
        mana_value=2,
        oracle_text="",
        type_line="Legendary Creature — Human Druid",
        power="2",
        toughness="2",
    )

    return Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
        entered_turn=1,
    )


def create_sol_ring(
    permanent_id: int = 2,
) -> Permanent:
    card = Card(
        id="sol-ring-id",
        name="Sol Ring",
        mana_cost="{1}",
        mana_value=1,
        oracle_text="{T}: Add {C}{C}.",
        type_line="Artifact",
        mana_abilities=(
            ManaAbility(
                produced_mana={
                    Mana.COLORLESS: 2,
                }
            ),
        ),
    )

    return Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=0,
        controller_id=0,
        summoning_sick=False,
        entered_turn=1,
    )


def create_basalt_monolith(
    permanent_id: int = 2,
) -> Permanent:
    card = Card(
        id="basalt-id",
        name="Basalt Monolith",
        mana_cost="{3}",
        mana_value=3,
        oracle_text="{T}: Add {C}{C}{C}.",
        type_line="Artifact",
        mana_abilities=(
            ManaAbility(
                produced_mana={
                    Mana.COLORLESS: 3,
                }
            ),
        ),
    )

    return Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=0,
        controller_id=0,
        summoning_sick=False,
        entered_turn=1,
    )


def create_forest(
    permanent_id: int = 2,
) -> Permanent:
    card = Card(
        id="forest-id",
        name="Forest",
        mana_cost="",
        mana_value=0,
        oracle_text="{T}: Add {G}.",
        type_line="Basic Land — Forest",
    )

    return Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=0,
        controller_id=0,
        summoning_sick=False,
        entered_turn=1,
    )
def create_roaming_throne(
    *,
    permanent_id: int = 3,
    chosen_type: str = "Human",
) -> Permanent:
    card = Card(
        id=f"roaming-throne-{permanent_id}",
        name="Roaming Throne",
        mana_cost="{4}",
        mana_value=4,
        oracle_text="",
        type_line="Artifact Creature — Golem",
        power="4",
        toughness="4",
    )

    return Permanent(
        permanent_id=permanent_id,
        card=card,
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
        entered_turn=1,
        chosen_values={
            "creature_type": chosen_type,
        },
    )
def create_kinnan_copy(
    permanent_id: int = 4,
) -> Permanent:
    kinnan_card = Card(
        id="kinnan-id",
        name="Kinnan, Bonder Prodigy",
        mana_cost="{G}{U}",
        mana_value=2,
        oracle_text="",
        type_line="Legendary Creature — Human Druid",
        power="2",
        toughness="2",
    )

    spark_double_card = Card(
        id="spark-double-id",
        name="Spark Double",
        mana_cost="{3}{U}",
        mana_value=4,
        oracle_text="",
        type_line="Creature — Illusion",
        power="0",
        toughness="0",
    )

    return Permanent(
        permanent_id=permanent_id,
        card=spark_double_card,
        copied_from=kinnan_card,
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
        entered_turn=1,
    )

def test_sol_ring_produces_one_additional_mana_with_kinnan() -> None:
    state = create_running_state()
    player = state.players[0]

    kinnan = create_kinnan()
    sol_ring = create_sol_ring()

    player.battlefield.add(kinnan)
    player.battlefield.add(sol_ring)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=sol_ring,
            mana=Mana.COLORLESS,
        ),
    )

    assert player.mana_pool.count(Mana.COLORLESS) == 3
    assert state.mana_generated == 3


def test_basalt_produces_four_mana_with_kinnan() -> None:
    state = create_running_state()
    player = state.players[0]

    player.battlefield.add(create_kinnan())
    basalt = create_basalt_monolith()
    player.battlefield.add(basalt)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=basalt,
            mana=Mana.COLORLESS,
        ),
    )

    assert player.mana_pool.count(Mana.COLORLESS) == 4
    assert state.mana_generated == 4


def test_nonland_produces_no_bonus_without_kinnan() -> None:
    state = create_running_state()
    player = state.players[0]

    sol_ring = create_sol_ring()
    player.battlefield.add(sol_ring)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=sol_ring,
            mana=Mana.COLORLESS,
        ),
    )

    assert player.mana_pool.count(Mana.COLORLESS) == 2
    assert state.mana_generated == 2


def test_land_receives_no_kinnan_bonus() -> None:
    state = create_running_state()
    player = state.players[0]

    player.battlefield.add(create_kinnan())
    forest = create_forest()
    player.battlefield.add(forest)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=forest,
            mana=Mana.GREEN,
        ),
    )

    assert player.mana_pool.count(Mana.GREEN) == 1
    assert state.mana_generated == 1


def test_tapped_kinnan_still_provides_bonus() -> None:
    state = create_running_state()
    player = state.players[0]

    kinnan = create_kinnan()
    kinnan.tapped = True

    sol_ring = create_sol_ring()

    player.battlefield.add(kinnan)
    player.battlefield.add(sol_ring)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=sol_ring,
            mana=Mana.COLORLESS,
        ),
    )

    assert player.mana_pool.count(Mana.COLORLESS) == 3


def test_summoning_sick_kinnan_still_provides_bonus() -> None:
    state = create_running_state()
    player = state.players[0]

    kinnan = create_kinnan()
    assert kinnan.summoning_sick is True

    sol_ring = create_sol_ring()

    player.battlefield.add(kinnan)
    player.battlefield.add(sol_ring)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=sol_ring,
            mana=Mana.COLORLESS,
        ),
    )

    assert player.mana_pool.count(Mana.COLORLESS) == 3

def test_one_kinnan_and_one_throne_add_two_bonus_mana() -> None:
    state = create_running_state()
    player = state.players[0]

    player.battlefield.add(create_kinnan())
    player.battlefield.add(
        create_roaming_throne(
            chosen_type="Human",
        )
    )

    sol_ring = create_sol_ring()
    player.battlefield.add(sol_ring)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=sol_ring,
            mana=Mana.COLORLESS,
        ),
    )

    # Sol Ring 2 + Kinnan trigger twice
    assert player.mana_pool.count(Mana.COLORLESS) == 4
    assert state.mana_generated == 4


def test_throne_with_unrelated_type_does_not_add_trigger() -> None:
    state = create_running_state()
    player = state.players[0]

    player.battlefield.add(create_kinnan())
    player.battlefield.add(
        create_roaming_throne(
            chosen_type="Golem",
        )
    )

    sol_ring = create_sol_ring()
    player.battlefield.add(sol_ring)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=sol_ring,
            mana=Mana.COLORLESS,
        ),
    )

    assert player.mana_pool.count(Mana.COLORLESS) == 3
    assert state.mana_generated == 3


def test_two_kinnans_without_throne_add_two_bonus_mana() -> None:
    state = create_running_state()
    player = state.players[0]

    player.battlefield.add(create_kinnan())
    player.battlefield.add(create_kinnan_copy())

    sol_ring = create_sol_ring()
    player.battlefield.add(sol_ring)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=sol_ring,
            mana=Mana.COLORLESS,
        ),
    )

    # Sol Ring 2 + two Kinnan triggers
    assert player.mana_pool.count(Mana.COLORLESS) == 4
    assert state.mana_generated == 4


def test_two_kinnans_and_one_throne_add_four_bonus_mana() -> None:
    state = create_running_state()
    player = state.players[0]

    player.battlefield.add(create_kinnan())
    player.battlefield.add(create_kinnan_copy())
    player.battlefield.add(
        create_roaming_throne(
            chosen_type="Druid",
        )
    )

    sol_ring = create_sol_ring()
    player.battlefield.add(sol_ring)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=sol_ring,
            mana=Mana.COLORLESS,
        ),
    )

    # Sol Ring 2 + (Kinnan 2体 × 各2回)
    assert player.mana_pool.count(Mana.COLORLESS) == 6
    assert state.mana_generated == 6


def test_two_kinnans_and_two_thrones_add_six_bonus_mana() -> None:
    state = create_running_state()
    player = state.players[0]

    player.battlefield.add(create_kinnan())
    player.battlefield.add(create_kinnan_copy())

    player.battlefield.add(
        create_roaming_throne(
            permanent_id=3,
            chosen_type="Human",
        )
    )
    player.battlefield.add(
        create_roaming_throne(
            permanent_id=4,
            chosen_type="Druid",
        )
    )

    sol_ring = create_sol_ring(
        permanent_id=5,
    )
    player.battlefield.add(sol_ring)

    ActionExecutor().execute(
        state,
        TapPermanentAction(
            player_id=0,
            turn_number=1,
            permanent=sol_ring,
            mana=Mana.COLORLESS,
        ),
    )

    # Sol Ring 2 + (Kinnan 2体 × 各3回)
    assert player.mana_pool.count(Mana.COLORLESS) == 8
    assert state.mana_generated == 8