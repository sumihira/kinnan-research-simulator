import pytest

from krs.statistics.kinnan_chain import (
    KinnanChainStatistics,
    KinnanChainSummary,
)


def test_new_statistics_are_zero() -> None:
    statistics = KinnanChainStatistics()

    assert statistics.activation_count == 0
    assert statistics.hit_count == 0
    assert statistics.miss_count == 0
    assert statistics.current_chain_length == 0
    assert statistics.longest_chain_length == 0
    assert statistics.chain_activation_count == 0
    assert statistics.first_chain_turn is None
    assert statistics.hit_card_ids == []
    assert statistics.hit_rate == 0.0
    assert statistics.has_activation is False
    assert statistics.has_chain is False


def test_record_hit_updates_counts() -> None:
    statistics = KinnanChainStatistics()

    statistics.record_hit("great-whale-id")

    assert statistics.activation_count == 1
    assert statistics.hit_count == 1
    assert statistics.miss_count == 0
    assert statistics.current_chain_length == 1
    assert statistics.longest_chain_length == 1
    assert statistics.chain_activation_count == 0
    assert statistics.hit_card_ids == [
        "great-whale-id",
    ]
    assert statistics.has_activation is True
    assert statistics.has_chain is False


def test_consecutive_hits_increase_chain_length() -> None:
    statistics = KinnanChainStatistics()

    statistics.record_hit("card-1", turn=3)
    statistics.record_hit("card-2", turn=3)
    statistics.record_hit("card-3", turn=4)

    assert statistics.activation_count == 3
    assert statistics.hit_count == 3
    assert statistics.current_chain_length == 3
    assert statistics.longest_chain_length == 3
    assert statistics.chain_activation_count == 3
    assert statistics.first_chain_turn == 3
    assert statistics.has_chain is True


def test_miss_resets_current_chain() -> None:
    statistics = KinnanChainStatistics()

    statistics.record_hit("card-1")
    statistics.record_hit("card-2")
    statistics.record_miss()

    assert statistics.activation_count == 3
    assert statistics.hit_count == 2
    assert statistics.miss_count == 1
    assert statistics.current_chain_length == 0
    assert statistics.longest_chain_length == 2
    assert statistics.chain_activation_count == 2


def test_new_chain_after_miss_is_tracked() -> None:
    statistics = KinnanChainStatistics()

    statistics.record_hit("card-1")
    statistics.record_hit("card-2")
    statistics.record_miss()
    statistics.record_hit("card-3")
    statistics.record_hit("card-4")

    assert statistics.current_chain_length == 2
    assert statistics.longest_chain_length == 2
    assert statistics.chain_activation_count == 4


def test_manual_reset_does_not_count_as_miss() -> None:
    statistics = KinnanChainStatistics()

    statistics.record_hit("card-1")
    statistics.reset_current_chain()

    assert statistics.activation_count == 1
    assert statistics.hit_count == 1
    assert statistics.miss_count == 0
    assert statistics.current_chain_length == 0
    assert statistics.longest_chain_length == 1
    assert statistics.chain_activation_count == 0


def test_first_chain_turn_is_not_replaced() -> None:
    statistics = KinnanChainStatistics()

    statistics.record_hit("card-1", turn=2)
    statistics.record_hit("card-2", turn=2)
    statistics.record_miss()
    statistics.record_hit("card-3", turn=4)
    statistics.record_hit("card-4", turn=4)

    assert statistics.first_chain_turn == 2


def test_hit_rate_is_calculated() -> None:
    statistics = KinnanChainStatistics()

    statistics.record_hit("card-1")
    statistics.record_hit("card-2")
    statistics.record_miss()
    statistics.record_miss()

    assert statistics.hit_rate == 0.5


def test_record_hit_rejects_empty_card_id() -> None:
    statistics = KinnanChainStatistics()

    with pytest.raises(
        ValueError,
        match="Hit card ID must not be empty",
    ):
        statistics.record_hit("")


def test_record_hit_rejects_invalid_turn() -> None:
    statistics = KinnanChainStatistics()

    with pytest.raises(
        ValueError,
        match="Turn must be at least 1",
    ):
        statistics.record_hit("card-1", turn=0)


def test_empty_summary_is_zero() -> None:
    summary = KinnanChainSummary.from_games(())

    assert summary == KinnanChainSummary.empty()
    assert summary.games == 0
    assert summary.overall_chain_rate == 0.0
    assert summary.activation_game_chain_rate == 0.0
    assert summary.activation_chain_rate == 0.0
    assert summary.chain_count_through_turn(3) == 0
    assert summary.chain_rate_through_turn(3) == 0.0


def test_summary_aggregates_multiple_games() -> None:
    no_activation = KinnanChainStatistics()

    one_hit = KinnanChainStatistics()
    one_hit.record_hit("card-1", turn=2)

    two_hit_chain = KinnanChainStatistics()
    two_hit_chain.record_hit("card-2", turn=3)
    two_hit_chain.record_hit("card-3", turn=3)

    split_chains = KinnanChainStatistics()
    split_chains.record_hit("card-4", turn=2)
    split_chains.record_hit("card-5", turn=2)
    split_chains.record_miss()
    split_chains.record_hit("card-6", turn=4)
    split_chains.record_hit("card-7", turn=4)
    split_chains.record_hit("card-8", turn=5)

    summary = KinnanChainSummary.from_games(
        (
            no_activation,
            one_hit,
            two_hit_chain,
            split_chains,
        )
    )

    assert summary.games == 4
    assert summary.games_with_activation == 3
    assert summary.games_with_chain == 2
    assert summary.total_activations == 9
    assert summary.chain_activations == 7
    assert summary.average_longest_chain == pytest.approx(
        1.5
    )
    assert summary.max_chain == 3
    assert summary.max_chain_distribution == (
        (0, 1),
        (1, 1),
        (2, 1),
        (3, 1),
    )
    assert summary.first_chain_turns == (3, 2)
    assert summary.turn_chain_counts == (
        (2, 1),
        (3, 1),
    )


def test_summary_rates_are_calculated() -> None:
    first = KinnanChainStatistics()
    first.record_hit("card-1", turn=2)
    first.record_hit("card-2", turn=2)

    second = KinnanChainStatistics()
    second.record_miss()

    summary = KinnanChainSummary.from_games(
        (first, second)
    )

    assert summary.overall_chain_rate == pytest.approx(0.5)
    assert summary.activation_game_chain_rate == pytest.approx(
        0.5
    )
    assert summary.activation_chain_rate == pytest.approx(
        2 / 3
    )


def test_turn_chain_rate_is_cumulative() -> None:
    turn_two = KinnanChainStatistics()
    turn_two.record_hit("card-1", turn=2)
    turn_two.record_hit("card-2", turn=2)

    turn_four = KinnanChainStatistics()
    turn_four.record_hit("card-3", turn=4)
    turn_four.record_hit("card-4", turn=4)

    no_chain = KinnanChainStatistics()
    no_chain.record_miss()

    summary = KinnanChainSummary.from_games(
        (turn_two, turn_four, no_chain)
    )

    assert summary.chain_count_through_turn(1) == 0
    assert summary.chain_count_through_turn(2) == 1
    assert summary.chain_count_through_turn(3) == 1
    assert summary.chain_count_through_turn(4) == 2
    assert summary.chain_rate_through_turn(2) == pytest.approx(
        1 / 3
    )
    assert summary.chain_rate_through_turn(4) == pytest.approx(
        2 / 3
    )


def test_summary_supports_chain_without_turn_data() -> None:
    statistics = KinnanChainStatistics()
    statistics.record_hit("card-1")
    statistics.record_hit("card-2")

    summary = KinnanChainSummary.from_games((statistics,))

    assert summary.games_with_chain == 1
    assert summary.first_chain_turns == ()
    assert summary.turn_chain_counts == ()


def test_summary_is_immutable() -> None:
    summary = KinnanChainSummary.empty()

    with pytest.raises(AttributeError):
        summary.games = 1  # type: ignore[misc]


def test_summary_rejects_inconsistent_game_counts() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "games_with_chain must not exceed "
            "games_with_activation"
        ),
    ):
        KinnanChainSummary(
            games=1,
            games_with_activation=0,
            games_with_chain=1,
            total_activations=0,
            chain_activations=0,
            average_longest_chain=0.0,
            max_chain=0,
            max_chain_distribution=((0, 1),),
            first_chain_turns=(),
            turn_chain_counts=(),
        )


def test_turn_queries_reject_invalid_turn() -> None:
    summary = KinnanChainSummary.empty()

    with pytest.raises(
        ValueError,
        match="Turn must be at least 1",
    ):
        summary.chain_count_through_turn(0)