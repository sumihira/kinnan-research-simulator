from __future__ import annotations

from dataclasses import dataclass

import pytest

from krs.actions.action import Action
from krs.actions.draw import DrawAction
from krs.cards.card import Card
from krs.engine.action_executor import ActionExecutor
from krs.game.game_state import GameState
from krs.game.library import Library
from krs.game.phase import Phase
from krs.game.player import Player
from krs.replay.replay import Replay


def create_card(
    card_id: str,
) -> Card:
    return Card(
        id=card_id,
        name=f"Card {card_id}",
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line="Creature",
        power="1",
        toughness="1",
    )


def create_state() -> GameState:
    player = Player(
        player_id=0,
        library=Library(
            cards=[
                create_card("card_1"),
                create_card("card_2"),
                create_card("card_3"),
            ],
        ),
    )

    return GameState(
        game_id=1,
        players=[player],
        started=True,
        turn_number=2,
        phase=Phase.DRAW,
    )


def test_executor_creates_empty_replay_by_default() -> None:
    executor = ActionExecutor()

    assert isinstance(
        executor.replay,
        Replay,
    )
    assert executor.replay.is_empty is True


def test_executor_uses_supplied_replay() -> None:
    replay = Replay()

    executor = ActionExecutor(
        replay=replay,
    )

    assert executor.replay is replay


def test_successful_draw_is_recorded() -> None:
    state = create_state()
    replay = Replay()

    executor = ActionExecutor(
        replay=replay,
    )

    executor.execute(
        state,
        DrawAction(
            player_id=0,
            turn_number=2,
            amount=1,
        ),
    )

    assert replay.event_count == 1

    event = replay.events[0]

    assert event.turn == 2
    assert event.phase == "draw"
    assert event.action == "draw"
    assert event.description == (
        "Player 0 executed draw."
    )


def test_successful_action_updates_state_and_replay() -> None:
    state = create_state()
    replay = Replay()

    executor = ActionExecutor(
        replay=replay,
    )

    executor.execute(
        state,
        DrawAction(
            player_id=0,
            turn_number=2,
            amount=1,
        ),
    )

    assert state.action_count == 1
    assert len(state.players[0].hand) == 1
    assert replay.event_count == 1


def test_multiple_actions_preserve_order() -> None:
    state = create_state()
    replay = Replay()

    executor = ActionExecutor(
        replay=replay,
    )

    executor.execute(
        state,
        DrawAction(
            player_id=0,
            turn_number=2,
            amount=1,
        ),
    )
    executor.execute(
        state,
        DrawAction(
            player_id=0,
            turn_number=2,
            amount=2,
        ),
    )

    assert tuple(
        event.action
        for event in replay.events
    ) == (
        "draw",
        "draw",
    )

    assert tuple(
        event.description
        for event in replay.events
    ) == (
        "Player 0 executed draw.",
        "Player 0 executed draw.",
    )


def test_failed_action_is_not_recorded() -> None:
    state = create_state()
    replay = Replay()

    executor = ActionExecutor(
        replay=replay,
    )

    with pytest.raises(IndexError):
        executor.execute(
            state,
            DrawAction(
                player_id=0,
                turn_number=2,
                amount=10,
            ),
        )

    assert replay.is_empty is True
    assert state.action_count == 0


def test_replay_events_are_returned_as_tuple() -> None:
    state = create_state()
    executor = ActionExecutor()

    executor.execute(
        state,
        DrawAction(
            player_id=0,
            turn_number=2,
            amount=1,
        ),
    )

    events = executor.replay.events

    assert isinstance(events, tuple)

    with pytest.raises(AttributeError):
        events.append(  # type: ignore[attr-defined]
            events[0]
        )


@dataclass(frozen=True, slots=True)
class UnsupportedAction(Action):
    pass


def test_unsupported_action_is_not_recorded() -> None:
    state = create_state()
    replay = Replay()

    executor = ActionExecutor(
        replay=replay,
    )

    with pytest.raises(
        NotImplementedError,
        match="Unsupported action type",
    ):
        executor.execute(
            state,
            UnsupportedAction(
                player_id=0,
                turn_number=2,
            ),
        )

    assert replay.is_empty is True
    assert state.action_count == 0


@pytest.mark.parametrize(
    (
        "class_name",
        "expected",
    ),
    (
        (
            "DrawAction",
            "draw",
        ),
        (
            "CastSpellAction",
            "cast_spell",
        ),
        (
            "ActivateAbilityAction",
            "activate_ability",
        ),
        (
            "ActivateKinnanAction",
            "activate_kinnan",
        ),
        (
            "ReturnCommanderAction",
            "return_commander",
        ),
    ),
)
def test_action_name_converts_class_name_to_snake_case(
    class_name: str,
    expected: str,
) -> None:
    action_type = type(
        class_name,
        (UnsupportedAction,),
        {},
    )

    action = action_type(
        player_id=0,
        turn_number=1,
    )

    assert (
        ActionExecutor._action_name(action)
        == expected
    )


def test_action_description_uses_common_action_fields() -> None:
    action = DrawAction(
        player_id=3,
        turn_number=4,
        amount=1,
    )

    description = (
        ActionExecutor._action_description(
            action
        )
    )

    assert description == (
        "Player 3 executed draw."
    )


def test_replay_is_not_shared_between_default_executors() -> None:
    first = ActionExecutor()
    second = ActionExecutor()

    assert first.replay is not second.replay