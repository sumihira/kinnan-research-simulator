from __future__ import annotations

from dataclasses import replace

from krs.cards.ability_factory import AbilityFactory
from krs.cards.card import Card
from krs.cards.card_config import CardConfig
from krs.cards.card_config_loader import CardConfigLoader


class CardEnricher:
    """Applies card-specific YAML definitions to immutable cards."""

    def __init__(
        self,
        config_loader: CardConfigLoader,
        *,
        ability_factory: AbilityFactory | None = None,
    ) -> None:
        self._config_loader = config_loader
        self._ability_factory = (
            ability_factory or AbilityFactory()
        )

    def enrich(
        self,
        card: Card,
    ) -> Card:
        config = self._config_loader.load_by_card_name(
            card.name
        )

        if config is None:
            return card

        return replace(
            card,
            mana_abilities=(
                *card.mana_abilities,
                *self._mana_abilities(config),
            ),
            activated_abilities=(
                *card.activated_abilities,
                *self._activated_abilities(config),
            ),
            static_abilities=(
                *card.static_abilities,
                *self._static_abilities(config),
            ),
            triggered_abilities=(
                *card.triggered_abilities,
                *self._triggered_abilities(config),
            ),
            etb_abilities=(
                *card.etb_abilities,
                *self._etb_abilities(config),
            ),
            replacement_abilities=(
                *card.replacement_abilities,
                *self._replacement_abilities(config),
            ),
        )

    def _mana_abilities(
        self,
        config: CardConfig,
    ) -> tuple:
        return tuple(
            self._ability_factory.create_mana_ability(definition)
            for definition in config.abilities.get("mana", ())
        )

    def _activated_abilities(
        self,
        config: CardConfig,
    ) -> tuple:
        return tuple(
            self._ability_factory.create_activated_ability(
                definition
            )
            for definition
            in config.abilities.get("activated", ())
        )

    def _static_abilities(
        self,
        config: CardConfig,
    ) -> tuple:
        return tuple(
            self._ability_factory.create_static_ability(
                definition
            )
            for definition
            in config.abilities.get("static", ())
        )

    def _triggered_abilities(
        self,
        config: CardConfig,
    ) -> tuple:
        return tuple(
            self._ability_factory.create_triggered_ability(
                definition
            )
            for definition
            in config.abilities.get("triggered", ())
        )

    def _etb_abilities(
        self,
        config: CardConfig,
    ) -> tuple:
        return tuple(
            self._ability_factory.create_etb_ability(
                definition
            )
            for definition in config.abilities.get("etb", ())
        )

    def _replacement_abilities(
        self,
        config: CardConfig,
    ) -> tuple:
        return tuple(
            self._ability_factory.create_replacement_ability(
                definition
            )
            for definition
            in config.abilities.get("replacement", ())
        )