import pytest

from krs.actions.activate_kinnan import ActivateKinnanAction
from krs.cards.card import Card
from krs.engine.action_executor import ActionExecutor
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player
from krs.mana.mana import Mana


def create_card(
    *,
    card_id: str,
    name: str,
    type_line: str,
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line=type_line,
    )


def create_kinnan() -> Permanent:
    card = create_card(
        card_id="kinnan-id",
        name="Kinnan, Bonder Prodigy",
        type_line="Legendary Creature — Human Druid",
    )

    return Permanent(
        permanent_id=1,
        card=card,
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
        entered_turn=1,
    )


def create_running_state() -> GameState:
    player = Player(player_id=0)
    player.battlefield.add(create_kinnan())

    return GameState(
        players=[player],
        started=True,
        phase=Phase.MAIN,
        turn_number=3,
        next_permanent_id=2,
    )


def add_activation_mana(player: Player) -> None:
    player.mana_pool.add(
        Mana.COLORLESS,
        5,
    )
    player.mana_pool.add(
        Mana.GREEN,
    )
    player.mana_pool.add(
        Mana.BLUE,
    )


def test_kinnan_activation_puts_selected_creature_onto_battlefield() -> None:
    state = create_running_state()
    player = state.players[0]

    selected = create_card(
        card_id="great-whale-id",
        name="Great Whale",
        type_line="Creature — Whale",
    )

    player.library.cards.extend(
        [
            create_card(
                card_id="forest-id",
                name="Forest",
                type_line="Basic Land — Forest",
            ),
            selected,
            create_card(
                card_id="sol-ring-id",
                name="Sol Ring",
                type_line="Artifact",
            ),
            create_card(
                card_id="instant-id",
                name="Test Instant",
                type_line="Instant",
            ),
            create_card(
                card_id="island-id",
                name="Island",
                type_line="Basic Land — Island",
            ),
            create_card(
                card_id="remaining-id",
                name="Remaining Card",
                type_line="Artifact",
            ),
        ]
    )

    add_activation_mana(player)

    ActionExecutor().execute(
        state,
        ActivateKinnanAction(
            player_id=0,
            turn_number=3,
            source_permanent_id=1,
            selected_card_id=selected.id,
        ),
    )

    assert len(player.battlefield) == 2

    hit = player.battlefield.cards[1]

    assert hit.card is selected
    assert hit.permanent_id == 2
    assert hit.summoning_sick is True
    assert hit.entered_turn == 3

    assert state.next_permanent_id == 3
    assert state.mana_spent == 7
    assert state.action_count == 1
    assert player.mana_pool.total() == 0
    assert state.kinnan_chain.activation_count == 1
    assert state.kinnan_chain.hit_count == 1
    assert state.kinnan_chain.miss_count == 0
    assert state.kinnan_chain.current_chain_length == 1
    assert state.kinnan_chain.longest_chain_length == 1
    assert state.kinnan_chain.hit_card_ids == [
        selected.id,
    ]

def test_kinnan_activation_puts_remaining_reveals_on_bottom() -> None:
    state = create_running_state()
    player = state.players[0]

    first = create_card(
        card_id="first-id",
        name="First",
        type_line="Artifact",
    )
    selected = create_card(
        card_id="selected-id",
        name="Selected Creature",
        type_line="Creature — Beast",
    )
    third = create_card(
        card_id="third-id",
        name="Third",
        type_line="Land",
    )
    fourth = create_card(
        card_id="fourth-id",
        name="Fourth",
        type_line="Instant",
    )
    fifth = create_card(
        card_id="fifth-id",
        name="Fifth",
        type_line="Sorcery",
    )
    remaining = create_card(
        card_id="sixth-id",
        name="Sixth",
        type_line="Artifact",
    )

    player.library.cards.extend(
        [
            first,
            selected,
            third,
            fourth,
            fifth,
            remaining,
        ]
    )

    add_activation_mana(player)

    ActionExecutor().execute(
        state,
        ActivateKinnanAction(
            player_id=0,
            turn_number=3,
            source_permanent_id=1,
            selected_card_id=selected.id,
        ),
    )

    library_cards = list(player.library)

    assert len(library_cards) == 5

    # 公開範囲外だった6枚目はライブラリー先頭に残る。
    assert library_cards[0] is remaining

    # 公開した残り4枚は無作為順でライブラリー下へ置かれる。
    bottom_card_ids = {
        card.id
        for card in library_cards[1:]
    }

    assert bottom_card_ids == {
        first.id,
        third.id,
        fourth.id,
        fifth.id,
    }

    assert selected not in player.library

def test_kinnan_activation_allows_no_selection() -> None:
    state = create_running_state()
    player = state.players[0]

    revealed = [
        create_card(
            card_id=f"card-{index}",
            name=f"Card {index}",
            type_line="Artifact",
        )
        for index in range(5)
    ]

    player.library.cards.extend(revealed)
    add_activation_mana(player)

    ActionExecutor().execute(
        state,
        ActivateKinnanAction(
            player_id=0,
            turn_number=3,
            source_permanent_id=1,
            selected_card_id=None,
        ),
    )

    library_cards = list(player.library)

    assert len(player.battlefield) == 1
    assert len(library_cards) == 5

    assert {
        card.id
        for card in library_cards
    } == {
        card.id
        for card in revealed
    }

    assert state.mana_spent == 7
    assert state.action_count == 1

def test_kinnan_activation_rejects_human_creature() -> None:
    state = create_running_state()
    player = state.players[0]

    human = create_card(
        card_id="human-id",
        name="Human Creature",
        type_line="Creature — Human Wizard",
    )

    player.library.cards.extend(
        [
            human,
            create_card(
                card_id="card-2",
                name="Card 2",
                type_line="Artifact",
            ),
            create_card(
                card_id="card-3",
                name="Card 3",
                type_line="Artifact",
            ),
            create_card(
                card_id="card-4",
                name="Card 4",
                type_line="Artifact",
            ),
            create_card(
                card_id="card-5",
                name="Card 5",
                type_line="Artifact",
            ),
        ]
    )

    original_library = list(player.library)
    add_activation_mana(player)

    with pytest.raises(
        ValueError,
        match="not a valid Kinnan hit",
    ):
        ActionExecutor().execute(
            state,
            ActivateKinnanAction(
                player_id=0,
                turn_number=3,
                source_permanent_id=1,
                selected_card_id=human.id,
            ),
        )

    assert list(player.library) == original_library
    assert player.mana_pool.total() == 7
    assert state.mana_spent == 0
    assert state.action_count == 0
    assert state.kinnan_chain.activation_count == 0
    assert state.kinnan_chain.hit_count == 0
    assert state.kinnan_chain.miss_count == 0

def test_kinnan_activation_rejects_noncreature() -> None:
    state = create_running_state()
    player = state.players[0]

    artifact = create_card(
        card_id="artifact-id",
        name="Test Artifact",
        type_line="Artifact",
    )

    player.library.cards.extend(
        [
            artifact,
            create_card(
                card_id="card-2",
                name="Card 2",
                type_line="Land",
            ),
            create_card(
                card_id="card-3",
                name="Card 3",
                type_line="Instant",
            ),
            create_card(
                card_id="card-4",
                name="Card 4",
                type_line="Sorcery",
            ),
            create_card(
                card_id="card-5",
                name="Card 5",
                type_line="Enchantment",
            ),
        ]
    )

    add_activation_mana(player)

    with pytest.raises(
        ValueError,
        match="not a valid Kinnan hit",
    ):
        ActionExecutor().execute(
            state,
            ActivateKinnanAction(
                player_id=0,
                turn_number=3,
                source_permanent_id=1,
                selected_card_id=artifact.id,
            ),
        )

    assert player.mana_pool.total() == 7
    assert state.action_count == 0

def test_kinnan_activation_rejects_card_outside_top_five() -> None:
    state = create_running_state()
    player = state.players[0]

    top_five = [
        create_card(
            card_id=f"card-{index}",
            name=f"Card {index}",
            type_line="Artifact",
        )
        for index in range(5)
    ]

    sixth = create_card(
        card_id="sixth-creature",
        name="Sixth Creature",
        type_line="Creature — Beast",
    )

    player.library.cards.extend(
        [
            *top_five,
            sixth,
        ]
    )

    add_activation_mana(player)

    with pytest.raises(
        ValueError,
        match="was not found among Kinnan reveals",
    ):
        ActionExecutor().execute(
            state,
            ActivateKinnanAction(
                player_id=0,
                turn_number=3,
                source_permanent_id=1,
                selected_card_id=sixth.id,
            ),
        )

    assert player.mana_pool.total() == 7
    assert len(player.library) == 6
    assert state.action_count == 0

def test_kinnan_activation_rejects_insufficient_mana() -> None:
    state = create_running_state()
    player = state.players[0]

    player.mana_pool.add(
        Mana.COLORLESS,
        5,
    )
    player.mana_pool.add(
        Mana.GREEN,
    )

    with pytest.raises(
        ValueError,
        match="Kinnan activation cost cannot be paid",
    ):
        ActionExecutor().execute(
            state,
            ActivateKinnanAction(
                player_id=0,
                turn_number=3,
                source_permanent_id=1,
            ),
        )

    assert player.mana_pool.total() == 6
    assert state.mana_spent == 0
    assert state.action_count == 0

def test_non_kinnan_source_cannot_activate_kinnan_ability() -> None:
    state = create_running_state()
    player = state.players[0]

    player.battlefield.clear()

    sol_ring = Permanent(
        permanent_id=1,
        card=create_card(
            card_id="sol-ring-id",
            name="Sol Ring",
            type_line="Artifact",
        ),
        owner_id=0,
        controller_id=0,
        summoning_sick=False,
    )

    player.battlefield.add(sol_ring)
    add_activation_mana(player)

    with pytest.raises(
        ValueError,
        match="Source permanent is not Kinnan",
    ):
        ActionExecutor().execute(
            state,
            ActivateKinnanAction(
                player_id=0,
                turn_number=3,
                source_permanent_id=1,
            ),
        )

    assert player.mana_pool.total() == 7

def test_kinnan_activation_looks_at_remaining_library_when_below_five() -> None:
    state = create_running_state()
    player = state.players[0]

    creature = create_card(
        card_id="creature-id",
        name="Creature",
        type_line="Creature — Beast",
    )

    player.library.cards.extend(
        [
            creature,
            create_card(
                card_id="artifact-id",
                name="Artifact",
                type_line="Artifact",
            ),
        ]
    )

    add_activation_mana(player)

    ActionExecutor().execute(
        state,
        ActivateKinnanAction(
            player_id=0,
            turn_number=3,
            source_permanent_id=1,
            selected_card_id=creature.id,
        ),
    )

    assert len(player.battlefield) == 2
    assert len(player.library) == 1

def test_consecutive_kinnan_hits_build_chain() -> None:
    state = create_running_state()
    player = state.players[0]

    first_hit = create_card(
        card_id="first-hit-id",
        name="First Hit",
        type_line="Creature — Beast",
    )
    second_hit = create_card(
        card_id="second-hit-id",
        name="Second Hit",
        type_line="Creature — Beast",
    )

    filler_cards = [
        create_card(
            card_id=f"filler-{index}",
            name=f"Filler {index}",
            type_line="Artifact",
        )
        for index in range(8)
    ]

    player.library.cards.extend(
        [
            first_hit,
            *filler_cards[:4],
            second_hit,
            *filler_cards[4:],
        ]
    )

    add_activation_mana(player)

    executor = ActionExecutor()

    executor.execute(
        state,
        ActivateKinnanAction(
            player_id=0,
            turn_number=3,
            source_permanent_id=1,
            selected_card_id=first_hit.id,
        ),
    )

    add_activation_mana(player)

    executor.execute(
        state,
        ActivateKinnanAction(
            player_id=0,
            turn_number=3,
            source_permanent_id=1,
            selected_card_id=second_hit.id,
        ),
    )

    assert state.kinnan_chain.activation_count == 2
    assert state.kinnan_chain.hit_count == 2
    assert state.kinnan_chain.miss_count == 0
    assert state.kinnan_chain.current_chain_length == 2
    assert state.kinnan_chain.longest_chain_length == 2
    assert state.kinnan_chain.hit_card_ids == [
        first_hit.id,
        second_hit.id,
    ]

def test_kinnan_miss_ends_current_chain() -> None:
    state = create_running_state()
    player = state.players[0]

    hit = create_card(
        card_id="hit-id",
        name="Valid Hit",
        type_line="Creature — Beast",
    )

    first_filler = [
        create_card(
            card_id=f"first-filler-{index}",
            name=f"First Filler {index}",
            type_line="Artifact",
        )
        for index in range(4)
    ]

    second_filler = [
        create_card(
            card_id=f"second-filler-{index}",
            name=f"Second Filler {index}",
            type_line="Artifact",
        )
        for index in range(5)
    ]

    player.library.cards.extend(
        [
            hit,
            *first_filler,
            *second_filler,
        ]
    )

    executor = ActionExecutor()

    add_activation_mana(player)

    executor.execute(
        state,
        ActivateKinnanAction(
            player_id=0,
            turn_number=3,
            source_permanent_id=1,
            selected_card_id=hit.id,
        ),
    )

    add_activation_mana(player)

    executor.execute(
        state,
        ActivateKinnanAction(
            player_id=0,
            turn_number=3,
            source_permanent_id=1,
            selected_card_id=None,
        ),
    )

    assert state.kinnan_chain.activation_count == 2
    assert state.kinnan_chain.hit_count == 1
    assert state.kinnan_chain.miss_count == 1
    assert state.kinnan_chain.current_chain_length == 0
    assert state.kinnan_chain.longest_chain_length == 1