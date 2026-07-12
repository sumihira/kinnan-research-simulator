from __future__ import annotations

import pytest

from krs.abilities.etb import EtbAbility
from krs.cards.card import Card
from krs.engine.etb_ability_engine import EtbAbilityEngine
from krs.game.permanent import Permanent
from krs.game.player import Player


def create_card(
    *,
    card_id: str,
    name: str,
    etb_abilities: tuple[EtbAbility, ...] = (),
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="{2}",
        mana_value=2,
        oracle_text="",
        type_line="Creature — Beast",
        power="2",
        toughness="2",
        etb_abilities=etb_abilities,
    )


def create_permanent(
    *,
    etb_abilities: tuple[EtbAbility, ...] = (),
) -> Permanent:
    return Permanent(
        permanent_id=1,
        card=create_card(
            card_id="etb-source-id",
            name="ETB Source",
            etb_abilities=etb_abilities,
        ),
        owner_id=0,
        controller_id=0,
        summoning_sick=True,
        entered_turn=1,
    )


def test_etb_engine_does_nothing_without_abilities() -> None:
    player = Player(player_id=0)
    permanent = create_permanent()

    EtbAbilityEngine().validate(
        permanent=permanent,
        controller=player,
    )
    EtbAbilityEngine().execute(
        permanent=permanent,
        controller=player,
    )

    assert len(player.hand) == 0
    assert len(player.library) == 0


def test_draw_card_etb_draws_configured_amount() -> None:
    player = Player(player_id=0)
    permanent = create_permanent(
        etb_abilities=(
            EtbAbility(
                ability_type="draw_card",
                parameters={
                    "amount": 2,
                },
            ),
        ),
    )

    first_card = create_card(
        card_id="first-card-id",
        name="First Card",
    )
    second_card = create_card(
        card_id="second-card-id",
        name="Second Card",
    )

    player.library.cards.extend(
        [
            first_card,
            second_card,
        ]
    )

    engine = EtbAbilityEngine()

    engine.validate(
        permanent=permanent,
        controller=player,
    )
    engine.execute(
        permanent=permanent,
        controller=player,
    )

    assert len(player.library) == 0
    assert len(player.hand) == 2
    assert first_card in player.hand
    assert second_card in player.hand


def test_draw_card_etb_defaults_to_one_card() -> None:
    player = Player(player_id=0)
    permanent = create_permanent(
        etb_abilities=(
            EtbAbility(
                ability_type="draw_card",
                parameters={},
            ),
        ),
    )
    drawn_card = create_card(
        card_id="drawn-card-id",
        name="Drawn Card",
    )
    player.library.cards.append(drawn_card)

    engine = EtbAbilityEngine()

    engine.validate(
        permanent=permanent,
        controller=player,
    )
    engine.execute(
        permanent=permanent,
        controller=player,
    )

    assert list(player.hand) == [drawn_card]
    assert len(player.library) == 0


@pytest.mark.parametrize(
    "amount",
    [
        True,
        1.5,
        "1",
        None,
    ],
)
def test_draw_card_etb_rejects_non_integer_amount(
    amount: object,
) -> None:
    player = Player(player_id=0)
    permanent = create_permanent(
        etb_abilities=(
            EtbAbility(
                ability_type="draw_card",
                parameters={
                    "amount": amount,
                },
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="ETB draw amount must be an integer",
    ):
        EtbAbilityEngine().validate(
            permanent=permanent,
            controller=player,
        )

    assert len(player.hand) == 0


@pytest.mark.parametrize(
    "amount",
    [
        0,
        -1,
        -10,
    ],
)
def test_draw_card_etb_rejects_non_positive_amount(
    amount: int,
) -> None:
    player = Player(player_id=0)
    permanent = create_permanent(
        etb_abilities=(
            EtbAbility(
                ability_type="draw_card",
                parameters={
                    "amount": amount,
                },
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="ETB draw amount must be greater than zero",
    ):
        EtbAbilityEngine().validate(
            permanent=permanent,
            controller=player,
        )


def test_draw_card_etb_rejects_insufficient_library() -> None:
    player = Player(player_id=0)
    permanent = create_permanent(
        etb_abilities=(
            EtbAbility(
                ability_type="draw_card",
                parameters={
                    "amount": 2,
                },
            ),
        ),
    )
    player.library.cards.append(
        create_card(
            card_id="only-card-id",
            name="Only Card",
        )
    )

    with pytest.raises(
        IndexError,
        match="Not enough cards in library for ETB draw",
    ):
        EtbAbilityEngine().validate(
            permanent=permanent,
            controller=player,
        )

    assert len(player.library) == 1
    assert len(player.hand) == 0


def test_rejects_unsupported_etb_ability() -> None:
    player = Player(player_id=0)
    permanent = create_permanent(
        etb_abilities=(
            EtbAbility(
                ability_type="unsupported_etb",
                parameters={},
            ),
        ),
    )

    with pytest.raises(
        NotImplementedError,
        match="Unsupported ETB ability type",
    ):
        EtbAbilityEngine().validate(
            permanent=permanent,
            controller=player,
        )