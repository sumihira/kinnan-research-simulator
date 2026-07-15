from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from collections.abc import Iterable

from krs.replay.replay_event import ReplayEvent


@dataclass(slots=True)
class Replay:
    """
    Stores ReplayEvent instances in recording order.

    Replay is mutable because events are appended while a game is running.
    The public events property returns an immutable tuple so callers cannot
    modify the internal event collection directly.
    """

    _events: list[ReplayEvent] = field(
        default_factory=list,
        init=False,
        repr=False,
    )

    @property
    def events(self) -> tuple[ReplayEvent, ...]:
        """
        Return all recorded events in insertion order.

        A tuple is returned to prevent callers from mutating the internal
        Replay collection.
        """
        return tuple(self._events)

    @property
    def event_count(self) -> int:
        """
        Return the number of recorded events.
        """
        return len(self._events)

    @property
    def is_empty(self) -> bool:
        """
        Return whether the Replay contains no events.
        """
        return not self._events

    def add(
        self,
        event: ReplayEvent,
    ) -> None:
        """
        Append one ReplayEvent to the Replay.

        Events are retained in the exact order in which add() is called.
        """
        if not isinstance(
            event,
            ReplayEvent,
        ):
            raise TypeError(
                "event must be a ReplayEvent."
            )

        self._events.append(event)

    def extend(
        self,
        events: Iterable[ReplayEvent],
    ) -> None:
        """
        Append multiple ReplayEvent instances in iterable order.

        The iterable is validated completely before the Replay is modified.
        This prevents a partially updated Replay when an invalid value is
        included in the iterable.
        """
        validated_events = tuple(events)

        for event in validated_events:
            if not isinstance(
                event,
                ReplayEvent,
            ):
                raise TypeError(
                    "events must contain only ReplayEvent instances."
                )

        self._events.extend(validated_events)

    def clear(self) -> None:
        """
        Remove every recorded event.
        """
        self._events.clear()