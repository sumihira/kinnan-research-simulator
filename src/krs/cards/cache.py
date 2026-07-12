from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from krs.cards.card import Card
from krs.cards.parser import ScryfallCardParser


class CardCache:
    """
    In-memory index built from a local Scryfall JSON cache.
    """

    def __init__(
        self,
        cards_by_name: Mapping[str, Card],
        cards_by_id: Mapping[str, Card],
    ) -> None:
        self._cards_by_name = dict(cards_by_name)
        self._cards_by_id = dict(cards_by_id)

    @classmethod
    def load_json(
        cls,
        path: str | Path,
        *,
        parser: ScryfallCardParser | None = None,
    ) -> CardCache:
        cache_path = Path(path)

        if not cache_path.exists():
            raise FileNotFoundError(
                f"Card cache file not found: {cache_path}"
            )

        if not cache_path.is_file():
            raise ValueError(
                f"Card cache path is not a file: {cache_path}"
            )

        try:
            with cache_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                raw_data = json.load(file)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Card cache contains invalid JSON: {cache_path}"
            ) from error

        if not isinstance(raw_data, list):
            raise ValueError(
                "Card cache root must be a list."
            )

        card_parser = parser or ScryfallCardParser()

        cards_by_name: dict[str, Card] = {}
        cards_by_id: dict[str, Card] = {}

        for index, raw_card in enumerate(raw_data):
            if not isinstance(raw_card, Mapping):
                raise ValueError(
                    f"Card cache entry {index} must be a mapping."
                )

            card = card_parser.parse(raw_card)

            normalized_name = cls.normalize_name(
                card.name
            )

            # 同名の再録が複数ある場合は、最初のカード定義を使う。
            # Oracle ID対応は後のキャッシュ改善で追加する。
            cards_by_name.setdefault(
                normalized_name,
                card,
            )

            if card.id in cards_by_id:
                raise ValueError(
                    f"Duplicate Scryfall card ID: {card.id}"
                )

            cards_by_id[card.id] = card

        return cls(
            cards_by_name=cards_by_name,
            cards_by_id=cards_by_id,
        )

    def get_by_name(
        self,
        name: str,
    ) -> Card:
        normalized_name = self.normalize_name(
            name
        )

        if not normalized_name:
            raise ValueError(
                "Card name must not be empty."
            )

        try:
            return self._cards_by_name[
                normalized_name
            ]
        except KeyError as error:
            raise ValueError(
                f"Card not found in cache: {name}"
            ) from error

    def get_by_id(
        self,
        card_id: str,
    ) -> Card:
        normalized_id = card_id.strip()

        if not normalized_id:
            raise ValueError(
                "Card ID must not be empty."
            )

        try:
            return self._cards_by_id[
                normalized_id
            ]
        except KeyError as error:
            raise ValueError(
                f"Card ID not found in cache: {card_id}"
            ) from error

    def __len__(self) -> int:
        return len(self._cards_by_id)

    @staticmethod
    def normalize_name(
        name: str,
    ) -> str:
        return " ".join(
            name.strip().casefold().split()
        )