import pytest

from krs.statistics.kinnan_chain import (
    KinnanChainStatistics,
)


def test_new_statistics_are_zero() -> None:
    statistics = KinnanChainStatistics()

    assert statistics.activation_count == 0
    assert statistics.hit_count == 0
    assert statistics.miss_count == 0
    assert statistics.current_chain_length == 0
    assert statistics.longest_chain_length == 0
    assert statistics.hit_card_ids == []
    assert statistics.hit_rate == 0.0


def test_record_hit_updates_counts() -> None:
    statistics = KinnanChainStatistics()

    statistics.record_hit("great-whale-id")

    assert statistics.activation_count == 1
    assert statistics.hit_count == 1
    assert statistics.miss_count == 0
    assert statistics.current_chain_length == 1
    assert statistics.longest_chain_length == 1
    assert statistics.hit_card_ids == [
        "great-whale-id",
    ]


def test_consecutive_hits_increase_chain_length() -> None:
    statistics = KinnanChainStatistics()

    statistics.record_hit("card-1")
    statistics.record_hit("card-2")
    statistics.record_hit("card-3")

    assert statistics.activation_count == 3
    assert statistics.hit_count == 3
    assert statistics.current_chain_length == 3
    assert statistics.longest_chain_length == 3


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


def test_new_chain_after_miss_is_tracked() -> None:
    statistics = KinnanChainStatistics()

    statistics.record_hit("card-1")
    statistics.record_hit("card-2")
    statistics.record_miss()
    statistics.record_hit("card-3")

    assert statistics.current_chain_length == 1
    assert statistics.longest_chain_length == 2


def test_manual_reset_does_not_count_as_miss() -> None:
    statistics = KinnanChainStatistics()

    statistics.record_hit("card-1")
    statistics.reset_current_chain()

    assert statistics.activation_count == 1
    assert statistics.hit_count == 1
    assert statistics.miss_count == 0
    assert statistics.current_chain_length == 0
    assert statistics.longest_chain_length == 1


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