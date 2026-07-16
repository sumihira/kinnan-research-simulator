from __future__ import annotations

from unittest.mock import Mock

import pytest

from krs.engine.game_engine import GameEngine
from krs.game.game_state import GameState
from krs.game.phase import Phase
from krs.game.player import Player
from krs.simulation.runner import (
    GoldfishRunner,
    GoldfishRunResult,
)
from krs.statistics.kinnan_chain import (
    KinnanChainSnapshot,
    KinnanChainStatistics,
    KinnanChainSummary,
)


def test_snapshot_copies_statistics_immutably() -> None:
    statistics = KinnanChainStatistics()
    statistics.record_hit(
        "card-1",
        turn=2,
    )
    statistics.record_hit(
        "card-2",
        turn=2,
    )

    snapshot = statistics.snapshot()

    statistics.record_miss()

    assert snapshot == KinnanChainSnapshot(
        activation_count=2,
        hit_count=2,
        miss_count=0,
        current_chain_length=2,
        longest_chain_length=2,
        chain_activation_count=2,
        first_chain_turn=2,
        hit_card_ids=(
            "card-1",
            "card-2",
        ),
    )
    assert snapshot.has_activation is True
    assert snapshot.has_chain is True
    assert snapshot.hit_rate == 1.0


def test_snapshot_is_immutable() -> None:
    snapshot = KinnanChainSnapshot.empty()

    with pytest.raises(AttributeError):
        snapshot.activation_count = 1  # type: ignore[misc]


def test_summary_accepts_snapshots() -> None:
    first = KinnanChainStatistics()
    first.record_hit(
        "card-1",
        turn=2,
    )
    first.record_hit(
        "card-2",
        turn=2,
    )

    second = KinnanChainStatistics()
    second.record_miss()

    summary = KinnanChainSummary.from_games(
        (
            first.snapshot(),
            second.snapshot(),
        )
    )

    assert summary.games == 2
    assert summary.games_with_activation == 2
    assert summary.games_with_chain == 1
    assert summary.total_activations == 3
    assert summary.chain_activations == 2
    assert summary.first_chain_turns == (2,)


def test_result_defaults_to_empty_snapshot() -> None:
    result = GoldfishRunResult(
        turns_started=1,
        kinnan_activations=0,
        reached_turn_limit=True,
        game_over=False,
        winner=None,
    )

    assert (
        result.kinnan_chain
        == KinnanChainSnapshot.empty()
    )


def test_runner_retains_final_chain_snapshot() -> None:
    state = GameState(
        players=[
            Player(player_id=0),
        ],
        started=True,
        phase=Phase.MAIN,
        turn_number=3,
    )
    state.kinnan_chain.record_hit(
        "card-1",
        turn=3,
    )

    engine = Mock(
        spec=GameEngine,
    )

    def execute_kinnan(
        current_state: GameState,
        *,
        player_id: int,
    ) -> bool:
        assert player_id == 0

        current_state.kinnan_chain.record_hit(
            "card-2",
            turn=current_state.turn_number,
        )
        current_state.game_over = True
        current_state.winner = "Player"

        return True

    engine.execute_kinnan_activation_if_available.side_effect = (
        execute_kinnan
    )

    runner = GoldfishRunner(
        game_engine=engine,
        max_turns=3,
    )

    result = runner.run(state)

    state.kinnan_chain.record_miss()

    assert result.kinnan_chain.activation_count == 2
    assert result.kinnan_chain.longest_chain_length == 2
    assert result.kinnan_chain.chain_activation_count == 2
    assert result.kinnan_chain.first_chain_turn == 3
    assert result.kinnan_chain.hit_card_ids == (
        "card-1",
        "card-2",
    )