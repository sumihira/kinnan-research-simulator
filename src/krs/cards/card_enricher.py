from __future__ import annotations

from dataclasses import replace

from krs.abilities.activated import ActivatedAbility
from krs.abilities.mana_ability import ManaAbility
from krs.abilities.replacement import ReplacementAbility
from krs.abilities.static import StaticAbility
from krs.abilities.triggered import TriggeredAbility
from krs.cards.ability_factory import AbilityFactory
from krs.cards.card import Card
from krs.cards.card_config import CardConfig
from krs.cards.card_config_loader import CardConfigLoader


class CardEnricher:
    """Applies card-specific YAML configuration to immutable cards."""

    def __init__(
        self,
        config_loader: CardConfigLoader,
        *,
        ability_factory: AbilityFactory | None = None,
    ) -> None:
        self._config_loader = config_loader
        self._ability_factory = ability_factory or AbilityFactory()

    def enrich(
        self,
        card: Card,
    ) -> Card:
        """Return a card enriched with configured abilities."""

        config = self._config_loader.load_by_card_name(card.name)

        if config is None:
            return card

        return replace(
            card,
            mana_abilities=(
                *card.mana_abilities,
                *self._create_mana_abilities(config),
            ),
            activated_abilities=(
                *card.activated_abilities,
                *self._create_activated_abilities(config),
            ),
            static_abilities=(
                *card.static_abilities,
                *self._create_static_abilities(config),
            ),
            triggered_abilities=(
                *card.triggered_abilities,
                *self._create_triggered_abilities(config),
            ),
            replacement_abilities=(
                *card.replacement_abilities,
                *self._create_replacement_abilities(config),
            ),
        )

    def _create_mana_abilities(
        self,
        config: CardConfig,
    ) -> tuple[ManaAbility, ...]:
        return tuple(
            self._ability_factory.create_mana_ability(definition)
            for definition in config.abilities.get("mana", ())
        )

    def _create_activated_abilities(
        self,
        config: CardConfig,
    ) -> tuple[ActivatedAbility, ...]:
        return tuple(
            self._ability_factory.create_activated_ability(
                definition
            )
            for definition in config.abilities.get(
                "activated",
                (),
            )
        )

    def _create_static_abilities(
        self,
        config: CardConfig,
    ) -> tuple[StaticAbility, ...]:
        return tuple(
            self._ability_factory.create_static_ability(
                definition
            )
            for definition in config.abilities.get(
                "static",
                (),
            )
        )

    def _create_triggered_abilities(
        self,
        config: CardConfig,
    ) -> tuple[TriggeredAbility, ...]:
        return tuple(
            self._ability_factory.create_triggered_ability(
                definition
            )
            for definition in config.abilities.get(
                "triggered",
                (),
            )
        )

    def _create_replacement_abilities(
        self,
        config: CardConfig,
    ) -> tuple[ReplacementAbility, ...]:
        return tuple(
            self._ability_factory.create_replacement_ability(
                definition
            )
            for definition in config.abilities.get(
                "replacement",
                (),
            )
        )