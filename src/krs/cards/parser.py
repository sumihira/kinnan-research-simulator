from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from krs.cards.card import Card


class ScryfallCardParser:
    """
    Converts a Scryfall card JSON object into a Card model.

    Mana abilities are enriched separately because Oracle-text parsing
    alone cannot represent all mana-production choices safely.
    """

    def parse(
        self,
        raw_card: Mapping[str, Any],
    ) -> Card:
        card_id = self._required_string(
            raw_card,
            "id",
        )
        name = self._required_string(
            raw_card,
            "name",
        )
        type_line = self._required_string(
            raw_card,
            "type_line",
        )

        mana_cost = self._read_combined_text(
            raw_card,
            field_name="mana_cost",
            separator=" // ",
        )
        oracle_text = self._read_combined_text(
            raw_card,
            field_name="oracle_text",
            separator="\n//\n",
        )

        mana_value = self._read_mana_value(
            raw_card.get("cmc", 0)
        )
        keywords = self._read_keywords(
            raw_card.get("keywords", [])
        )

        return Card(
            id=card_id,
            name=name,
            mana_cost=mana_cost,
            mana_value=mana_value,
            oracle_text=oracle_text,
            type_line=type_line,
            power=self._optional_string(
                raw_card.get("power")
            ),
            toughness=self._optional_string(
                raw_card.get("toughness")
            ),
            keywords=keywords,
        )

    def _read_combined_text(
        self,
        raw_card: Mapping[str, Any],
        *,
        field_name: str,
        separator: str,
    ) -> str:
        top_level_value = raw_card.get(field_name)

        if isinstance(top_level_value, str):
            return top_level_value

        card_faces = raw_card.get("card_faces")

        if not isinstance(card_faces, list):
            return ""

        values: list[str] = []

        for face in card_faces:
            if not isinstance(face, Mapping):
                continue

            value = face.get(field_name)

            if isinstance(value, str):
                values.append(value)

        return separator.join(values)

    @staticmethod
    def _required_string(
        raw_card: Mapping[str, Any],
        field_name: str,
    ) -> str:
        value = raw_card.get(field_name)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Scryfall card requires non-empty {field_name}."
            )

        return value

    @staticmethod
    def _optional_string(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                "Optional Scryfall card values must be strings."
            )

        return value

    @staticmethod
    def _read_mana_value(
        value: Any,
    ) -> int:
        if isinstance(value, bool):
            raise ValueError(
                "Scryfall cmc must be numeric."
            )

        if not isinstance(value, int | float):
            raise ValueError(
                "Scryfall cmc must be numeric."
            )

        if value < 0:
            raise ValueError(
                "Scryfall cmc must not be negative."
            )

        # 現在のManaCostモデルに合わせて整数化する。
        # 小数のマナ総量が必要になった場合はCard側をfloatへ拡張する。
        if not float(value).is_integer():
            raise ValueError(
                "Fractional mana values are not supported."
            )

        return int(value)

    @staticmethod
    def _read_keywords(
        value: Any,
    ) -> tuple[str, ...]:
        if value is None:
            return ()

        if not isinstance(value, list):
            raise ValueError(
                "Scryfall keywords must be a list."
            )

        keywords: list[str] = []

        for keyword in value:
            if not isinstance(keyword, str):
                raise ValueError(
                    "Scryfall keyword entries must be strings."
                )

            keywords.append(keyword)

        return tuple(keywords)