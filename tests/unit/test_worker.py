
from __future__ import annotations

from unittest.mock import Mock

import pytest

from krs.cards.card import Card
from krs.decks.deck import Deck
from krs.simulation.runner import GoldfishRunResult
from krs.simulation.simulator import GoldfishSimulator
from krs.simulation.worker import SimulationWorker


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


def test_worker_executes_one_game() -> None:
    deck = create_deck()
    expected_result = create_result()

    simulator = Mock(
        spec=GoldfishSimulator,
    )
    simulator.simulate_game.return_value = expected_result

    worker = SimulationWorker(
        simulator=simulator,
    )

    result = worker.run_game(
        deck,
        game_id=4,
    )

    simulator.simulate_game.assert_called_once_with(
        deck,
        game_id=4,
        player_id=0,
        player_name="Player",
    )
    assert result is expected_result


def test_worker_passes_custom_player_values() -> None:
    deck = create_deck()

    simulator = Mock(
        spec=GoldfishSimulator,
    )
    simulator.simulate_game.return_value = create_result()

    worker = SimulationWorker(
        simulator=simulator,
    )

    worker.run_game(
        deck,
        game_id=8,
        player_id=7,
        player_name="Junpei",
    )

    simulator.simulate_game.assert_called_once_with(
        deck,
        game_id=8,
        player_id=7,
        player_name="Junpei",
    )


def test_worker_preserves_game_id() -> None:
    deck = create_deck()

    simulator = Mock(
        spec=GoldfishSimulator,
    )
    simulator.simulate_game.return_value = create_result()

    worker = SimulationWorker(
        simulator=simulator,
    )

    worker.run_game(
        deck,
        game_id=123,
    )

    assert (
        simulator.simulate_game.call_args.kwargs["game_id"]
        == 123
    )


@pytest.mark.parametrize(
    "game_id",
    [
        -1,
        -10,
        -100,
    ],
)
def test_worker_rejects_negative_game_id(
    game_id: int,
) -> None:
    deck = create_deck()

    simulator = Mock(
        spec=GoldfishSimulator,
    )

    worker = SimulationWorker(
        simulator=simulator,
    )

    with pytest.raises(
        ValueError,
        match="game_id must not be negative.",
    ):
        worker.run_game(
            deck,
            game_id=game_id,
        )

    simulator.simulate_game.assert_not_called()


def test_worker_returns_simulator_result_without_copying() -> None:
    deck = create_deck()
    expected_result = create_result()

    simulator = Mock(
        spec=GoldfishSimulator,
    )
    simulator.simulate_game.return_value = expected_result

    worker = SimulationWorker(
        simulator=simulator,
    )

    result = worker.run_game(
        deck,
        game_id=0,
    )

    assert result is expected_result