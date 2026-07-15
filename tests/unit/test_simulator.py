from __future__ import annotations

from unittest.mock import Mock, patch

from krs.cards.card import Card
from krs.decks.deck import Deck
from krs.engine.game_engine import GameEngine
from krs.game.game_state import GameState
from krs.simulation.game_state_factory import GameStateFactory
from krs.simulation.runner import GoldfishRunResult
from krs.simulation.simulation_config import SimulationConfig
from krs.simulation.simulator import GoldfishSimulator


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


def create_deck() -> Deck:
    commander = create_card(
        card_id="kinnan-id",
        name="Kinnan, Bonder Prodigy",
        type_line="Legendary Creature — Human Druid",
    )

    cards = [
        create_card(
            card_id=f"forest-{index}",
            name="Forest",
            type_line="Basic Land — Forest",
        )
        for index in range(10)
    ]

    return Deck(
        name="Kinnan Test",
        commander=commander,
        cards=cards,
    )


def create_result() -> GoldfishRunResult:
    return GoldfishRunResult(
        turns_started=3,
        kinnan_activations=2,
        reached_turn_limit=False,
        game_over=True,
        winner="Player",
    )


def test_simulate_game_creates_state_with_derived_seed() -> None:
    deck = create_deck()
    config = SimulationConfig(
        max_turns=6,
        seed=1000,
    )

    state = GameState(
        game_id=4,
        seed=1004,
    )

    state_factory = Mock(
        spec=GameStateFactory,
    )
    state_factory.create_goldfish_state.return_value = state

    game_engine = Mock(
        spec=GameEngine,
    )

    expected_result = create_result()

    with patch(
        "krs.simulation.simulator.GoldfishRunner",
    ) as runner_class:
        runner = runner_class.return_value
        runner.run.return_value = expected_result

        simulator = GoldfishSimulator(
            config=config,
            game_engine=game_engine,
            state_factory=state_factory,
        )

        result = simulator.simulate_game(
            deck,
            game_id=4,
        )

    state_factory.create_goldfish_state.assert_called_once_with(
        deck,
        game_id=4,
        seed=1004,
        player_id=0,
        player_name="Player",
    )
    assert result is expected_result


def test_simulate_game_uses_none_seed_without_base_seed() -> None:
    deck = create_deck()
    config = SimulationConfig(
        max_turns=6,
        seed=None,
    )

    state = GameState(
        game_id=2,
        seed=None,
    )

    state_factory = Mock(
        spec=GameStateFactory,
    )
    state_factory.create_goldfish_state.return_value = state

    game_engine = Mock(
        spec=GameEngine,
    )

    with patch(
        "krs.simulation.simulator.GoldfishRunner",
    ) as runner_class:
        runner_class.return_value.run.return_value = create_result()

        simulator = GoldfishSimulator(
            config=config,
            game_engine=game_engine,
            state_factory=state_factory,
        )

        simulator.simulate_game(
            deck,
            game_id=2,
        )

    state_factory.create_goldfish_state.assert_called_once_with(
        deck,
        game_id=2,
        seed=None,
        player_id=0,
        player_name="Player",
    )


def test_simulate_game_passes_custom_player_values() -> None:
    deck = create_deck()
    config = SimulationConfig()

    state = GameState(
        game_id=0,
    )

    state_factory = Mock(
        spec=GameStateFactory,
    )
    state_factory.create_goldfish_state.return_value = state

    game_engine = Mock(
        spec=GameEngine,
    )

    with patch(
        "krs.simulation.simulator.GoldfishRunner",
    ) as runner_class:
        runner_class.return_value.run.return_value = create_result()

        simulator = GoldfishSimulator(
            config=config,
            game_engine=game_engine,
            state_factory=state_factory,
        )

        simulator.simulate_game(
            deck,
            player_id=7,
            player_name="Junpei",
        )

    state_factory.create_goldfish_state.assert_called_once_with(
        deck,
        game_id=0,
        seed=None,
        player_id=7,
        player_name="Junpei",
    )


def test_simulate_game_creates_runner_from_config() -> None:
    deck = create_deck()
    config = SimulationConfig(
        max_turns=9,
    )

    state = GameState()
    state_factory = Mock(
        spec=GameStateFactory,
    )
    state_factory.create_goldfish_state.return_value = state

    game_engine = Mock(
        spec=GameEngine,
    )

    with patch(
        "krs.simulation.simulator.GoldfishRunner",
    ) as runner_class:
        runner = runner_class.return_value
        runner.run.return_value = create_result()

        simulator = GoldfishSimulator(
            config=config,
            game_engine=game_engine,
            state_factory=state_factory,
        )

        simulator.simulate_game(deck)

    runner_class.assert_called_once_with(
        game_engine=game_engine,
        max_turns=9,
    )
    runner.run.assert_called_once_with(state)


def test_simulate_game_returns_runner_result() -> None:
    deck = create_deck()
    config = SimulationConfig()

    state_factory = Mock(
        spec=GameStateFactory,
    )
    state_factory.create_goldfish_state.return_value = GameState()

    game_engine = Mock(
        spec=GameEngine,
    )

    expected_result = create_result()

    with patch(
        "krs.simulation.simulator.GoldfishRunner",
    ) as runner_class:
        runner_class.return_value.run.return_value = expected_result

        simulator = GoldfishSimulator(
            config=config,
            game_engine=game_engine,
            state_factory=state_factory,
        )

        result = simulator.simulate_game(deck)

    assert result is expected_result


def test_simulate_game_creates_fresh_state_for_each_call() -> None:
    deck = create_deck()
    config = SimulationConfig(
        seed=200,
    )

    first_state = GameState(
        game_id=0,
        seed=200,
    )
    second_state = GameState(
        game_id=1,
        seed=201,
    )

    state_factory = Mock(
        spec=GameStateFactory,
    )
    state_factory.create_goldfish_state.side_effect = [
        first_state,
        second_state,
    ]

    game_engine = Mock(
        spec=GameEngine,
    )

    with patch(
        "krs.simulation.simulator.GoldfishRunner",
    ) as runner_class:
        runner_class.return_value.run.return_value = create_result()

        simulator = GoldfishSimulator(
            config=config,
            game_engine=game_engine,
            state_factory=state_factory,
        )

        simulator.simulate_game(
            deck,
            game_id=0,
        )
        simulator.simulate_game(
            deck,
            game_id=1,
        )

    assert state_factory.create_goldfish_state.call_count == 2

    runner = runner_class.return_value
    assert runner.run.call_count == 2
    assert runner.run.call_args_list[0].args == (
        first_state,
    )
    assert runner.run.call_args_list[1].args == (
        second_state,
    )