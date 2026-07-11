import pytest

from krs.mana.mana_cost import ManaCost


def test_empty_mana_cost_defaults_to_zero() -> None:
    cost = ManaCost()

    assert cost.generic == 0
    assert cost.white == 0
    assert cost.blue == 0
    assert cost.black == 0
    assert cost.red == 0
    assert cost.green == 0
    assert cost.colorless == 0
    assert cost.total == 0
    assert cost.colored_total == 0


def test_mana_cost_can_store_all_supported_symbols() -> None:
    cost = ManaCost(
        generic=3,
        white=1,
        blue=2,
        black=1,
        red=1,
        green=2,
        colorless=1,
    )

    assert cost.generic == 3
    assert cost.white == 1
    assert cost.blue == 2
    assert cost.black == 1
    assert cost.red == 1
    assert cost.green == 2
    assert cost.colorless == 1


def test_total_returns_all_mana_symbols() -> None:
    cost = ManaCost(
        generic=3,
        blue=1,
        green=1,
    )

    assert cost.total == 5


def test_colored_total_excludes_generic_and_colorless() -> None:
    cost = ManaCost(
        generic=3,
        white=1,
        blue=2,
        black=1,
        red=1,
        green=2,
        colorless=4,
    )

    assert cost.colored_total == 7


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("generic", {"generic": -1}),
        ("white", {"white": -1}),
        ("blue", {"blue": -1}),
        ("black", {"black": -1}),
        ("red", {"red": -1}),
        ("green", {"green": -1}),
        ("colorless", {"colorless": -1}),
    ],
)
def test_negative_values_are_rejected(
    field_name: str,
    kwargs: dict[str, int],
) -> None:
    with pytest.raises(
        ValueError,
        match="Mana cost values must not be negative",
    ):
        ManaCost(**kwargs)


def test_mana_cost_is_immutable() -> None:
    cost = ManaCost(generic=1)

    with pytest.raises(AttributeError):
        cost.generic = 2  # type: ignore[misc]


def test_equal_mana_costs_are_equal() -> None:
    first = ManaCost(generic=1, blue=1, green=1)
    second = ManaCost(generic=1, blue=1, green=1)

    assert first == second


def test_different_mana_costs_are_not_equal() -> None:
    first = ManaCost(generic=1, blue=1)
    second = ManaCost(generic=1, green=1)

    assert first != second