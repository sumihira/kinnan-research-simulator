import pytest

from krs.game.zone import Zone


def test_new_zone_is_empty() -> None:
    zone: Zone[str] = Zone()

    assert len(zone) == 0
    assert list(zone) == []


def test_add_item() -> None:
    zone: Zone[str] = Zone()

    zone.add("Sol Ring")

    assert len(zone) == 1
    assert "Sol Ring" in zone


def test_add_multiple_items_preserves_order() -> None:
    zone: Zone[str] = Zone()

    zone.add("Forest")
    zone.add("Island")
    zone.add("Sol Ring")

    assert list(zone) == [
        "Forest",
        "Island",
        "Sol Ring",
    ]


def test_remove_existing_item() -> None:
    zone: Zone[str] = Zone()
    zone.add("Kinnan")
    zone.add("Sol Ring")

    zone.remove("Kinnan")

    assert len(zone) == 1
    assert "Kinnan" not in zone
    assert "Sol Ring" in zone


def test_remove_missing_item_raises_value_error() -> None:
    zone: Zone[str] = Zone()

    with pytest.raises(ValueError):
        zone.remove("Kinnan")


def test_contains_returns_true_for_existing_item() -> None:
    zone: Zone[str] = Zone()
    zone.add("Basalt Monolith")

    assert "Basalt Monolith" in zone


def test_contains_returns_false_for_missing_item() -> None:
    zone: Zone[str] = Zone()

    assert "Basalt Monolith" not in zone


def test_iterates_over_all_items() -> None:
    zone: Zone[str] = Zone()
    zone.add("Forest")
    zone.add("Island")

    items = [item for item in zone]

    assert items == ["Forest", "Island"]


def test_clear_removes_all_items() -> None:
    zone: Zone[str] = Zone()
    zone.add("Forest")
    zone.add("Island")
    zone.add("Sol Ring")

    zone.clear()

    assert len(zone) == 0
    assert list(zone) == []


def test_duplicate_items_are_allowed() -> None:
    zone: Zone[str] = Zone()

    zone.add("Island")
    zone.add("Island")

    assert len(zone) == 2
    assert list(zone) == ["Island", "Island"]


def test_remove_only_first_matching_item() -> None:
    zone: Zone[str] = Zone()
    zone.add("Island")
    zone.add("Island")

    zone.remove("Island")

    assert len(zone) == 1
    assert list(zone) == ["Island"]