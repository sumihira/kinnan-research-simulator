from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from krs.cards.cache import CardCache
from krs.cards.card_config import CardConfig


class CardConfigLoader:

    def __init__(
        self,
        config_directory: Path,
    ) -> None:
        self._config_directory = Path(config_directory)
        self._configs_by_name: dict[str, CardConfig] | None = None

    def load_by_card_name(
        self,
        card_name: str,
    ) -> CardConfig | None:
        normalized_name = CardCache.normalize_name(card_name)

        if not normalized_name:
            raise ValueError(
                "Card name must not be empty."
            )

        if self._configs_by_name is None:
            self._configs_by_name = self._load_all()

        return self._configs_by_name.get(normalized_name)

    def _load_all(self) -> dict[str, CardConfig]:
        if not self._config_directory.exists():
            raise FileNotFoundError(
                "Card config directory not found: "
                f"{self._config_directory}"
            )

        if not self._config_directory.is_dir():
            raise ValueError(
                "Card config path is not a directory: "
                f"{self._config_directory}"
            )

        configs: dict[str, CardConfig] = {}

        for config_path in sorted(
            self._config_directory.glob("*.yaml")
        ):
            config = self._load_file(config_path)
            normalized_name = CardCache.normalize_name(
                config.card_name
            )

            if normalized_name in configs:
                raise ValueError(
                    "Duplicate card config: "
                    f"{config.card_name}"
                )

            configs[normalized_name] = config

        return configs

    def _load_file(
        self,
        config_path: Path,
    ) -> CardConfig:
        try:
            with config_path.open(
                "r",
                encoding="utf-8",
            ) as config_file:
                raw_config = yaml.safe_load(config_file)
        except yaml.YAMLError as error:
            raise ValueError(
                f"Invalid card config YAML: {config_path}"
            ) from error

        if not isinstance(raw_config, Mapping):
            raise ValueError(
                "Card config root must be a mapping: "
                f"{config_path}"
            )

        card_name = raw_config.get("card_name")

        if not isinstance(card_name, str) or not card_name.strip():
            raise ValueError(
                "Card config requires non-empty card_name: "
                f"{config_path}"
            )

        abilities = self._read_abilities(
            raw_config.get("abilities", {}),
            config_path=config_path,
        )

        return CardConfig(
            card_name=card_name,
            abilities=abilities,
        )

    @staticmethod
    def _read_abilities(
        raw_abilities: Any,
        *,
        config_path: Path,
    ) -> dict[str, tuple[Mapping[str, object], ...]]:
        if not isinstance(raw_abilities, Mapping):
            raise ValueError(
                "Card config abilities must be a mapping: "
                f"{config_path}"
            )

        abilities: dict[
            str,
            tuple[Mapping[str, object], ...],
        ] = {}

        for ability_kind, raw_definitions in raw_abilities.items():
            if not isinstance(ability_kind, str):
                raise ValueError(
                    "Ability kind must be a string: "
                    f"{config_path}"
                )

            if not isinstance(raw_definitions, list):
                raise ValueError(
                    f"Ability definitions must be a list: "
                    f"{config_path}"
                )

            definitions: list[Mapping[str, object]] = []

            for definition in raw_definitions:
                if not isinstance(definition, Mapping):
                    raise ValueError(
                        "Ability definition must be a mapping: "
                        f"{config_path}"
                    )

                definitions.append(dict(definition))

            abilities[ability_kind] = tuple(definitions)

        return abilities