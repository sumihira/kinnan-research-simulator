from __future__ import annotations

from dataclasses import dataclass, field

from krs.cards.card import Card


@dataclass(slots=True)
class Permanent:
    """
    Runtime representation of a permanent on the battlefield.
    """

    # 必須フィールド
    permanent_id: int
    card: Card
    owner_id: int
    controller_id: int

    # 状態
    tapped: bool = False
    summoning_sick: bool = True
    is_token: bool = False

    # コピー情報
    copied_from: Card | None = None

    # ターン情報
    entered_turn: int = 0

    # カウンター
    counters: dict[str, int] = field(default_factory=dict)