from __future__ import annotations

from pathlib import Path

from krs.cards.card import Card
from krs.cards.card_config_loader import CardConfigLoader
from krs.cards.card_enricher import CardEnricher
from krs.mana.mana import Mana


def create_card(
    *,
    name: str = "Sol Ring",
) -> Card:
    return Card(
        id="test-card-id",
        name=name,
        mana_cost="{1}",
        mana_value=1,
        oracle_text="{T}: Add {C}{C}.",
        type_line="Artifact",
    )


def write_config(
    config_directory: Path,
    *,
    filename: str,
    content: str,
) -> None:
    config_directory.mkdir(
        parents=True,
        exist_ok=True,
    )
    config_directory.joinpath(filename).write_text(
        content.strip(),
        encoding="utf-8",
    )


def test_enriches_card_with_mana_ability(
    tmp_path: Path,
) -> None:
    write_config(
        tmp_path,
        filename="sol_ring.yaml",
        content="""
card_name: Sol Ring

abilities:
  mana:
    - produces:
        COLORLESS: 2
      requires_tap: true
""",
    )

    card = create_card()
    enricher = CardEnricher(
        CardConfigLoader(tmp_path)
    )

    enriched = enricher.enrich(card)

    assert enriched is not card
    assert card.mana_abilities == ()
    assert len(enriched.mana_abilities) == 1
    assert enriched.mana_abilities[0].produced_mana == {
        Mana.COLORLESS: 2,
    }
    assert enriched.mana_abilities[0].requires_tap is True


def test_enriches_card_with_all_supported_ability_types(
    tmp_path: Path,
) -> None:
    write_config(
        tmp_path,
        filename="test_card.yaml",
        content="""
card_name: Test Card

abilities:
  mana:
    - produces:
        GREEN: 1
      requires_tap: true

  activated:
    - ability_type: untap_self
      mana_cost: "{3}"
      requires_tap: false
      parameters:
        target: self

  static:
    - ability_type: skip_normal_untap
      parameters:
        applies_during: untap_step

  triggered:
    - ability_type: draw_card
      event: enters_battlefield
      parameters:
        amount: 1

  replacement:
    - ability_type: choose_creature_type
      event: enters_battlefield
      parameters:
        choice_type: creature_type
""",
    )

    card = Card(
        id="test-card-id",
        name="Test Card",
        mana_cost="{3}",
        mana_value=3,
        oracle_text="Test oracle text.",
        type_line="Artifact Creature",
    )
    enricher = CardEnricher(
        CardConfigLoader(tmp_path)
    )

    enriched = enricher.enrich(card)

    assert len(enriched.mana_abilities) == 1
    assert len(enriched.activated_abilities) == 1
    assert len(enriched.static_abilities) == 1
    assert len(enriched.triggered_abilities) == 1
    assert len(enriched.replacement_abilities) == 1

    assert (
        enriched.activated_abilities[0].ability_type
        == "untap_self"
    )
    assert (
        enriched.static_abilities[0].ability_type
        == "skip_normal_untap"
    )
    assert (
        enriched.triggered_abilities[0].event
        == "enters_battlefield"
    )
    assert (
        enriched.replacement_abilities[0].ability_type
        == "choose_creature_type"
    )


def test_returns_original_card_when_config_does_not_exist(
    tmp_path: Path,
) -> None:
    tmp_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    card = create_card(
        name="Unconfigured Card",
    )
    enricher = CardEnricher(
        CardConfigLoader(tmp_path)
    )

    enriched = enricher.enrich(card)

    assert enriched is card


def test_preserves_existing_card_abilities(
    tmp_path: Path,
) -> None:
    write_config(
        tmp_path,
        filename="sol_ring.yaml",
        content="""
card_name: Sol Ring

abilities:
  mana:
    - produces:
        COLORLESS: 2
      requires_tap: true
""",
    )

    configured_enricher = CardEnricher(
        CardConfigLoader(tmp_path)
    )
    base_card = create_card()
    first_enriched = configured_enricher.enrich(base_card)

    second_directory = tmp_path / "second"
    write_config(
        second_directory,
        filename="sol_ring.yaml",
        content="""
card_name: Sol Ring

abilities:
  static:
    - ability_type: test_static
      parameters: {}
""",
    )

    second_enricher = CardEnricher(
        CardConfigLoader(second_directory)
    )

    enriched = second_enricher.enrich(first_enriched)

    assert len(enriched.mana_abilities) == 1
    assert len(enriched.static_abilities) == 1


def test_card_loader_can_enrich_mapping_card(
    tmp_path: Path,
) -> None:
    from krs.cards.card_loader import CardLoader

    write_config(
        tmp_path,
        filename="sol_ring.yaml",
        content="""
card_name: Sol Ring

abilities:
  mana:
    - produces:
        COLORLESS: 2
      requires_tap: true
""",
    )

    card = create_card()
    enricher = CardEnricher(
        CardConfigLoader(tmp_path)
    )
    loader = CardLoader(
        {
            "Sol Ring": card,
        },
        enricher=enricher,
    )

    loaded = loader.load_by_name("sol ring")

    assert loaded is not card
    assert len(loaded.mana_abilities) == 1
    assert loaded.mana_abilities[0].total_produced == 2


def test_card_loader_without_enricher_preserves_existing_behavior(
    tmp_path: Path,
) -> None:
    del tmp_path

    card = create_card()
    loader = __import__(
        "krs.cards.card_loader",
        fromlist=["CardLoader"],
    ).CardLoader(
        {
            "Sol Ring": card,
        }
    )

    loaded = loader.load_by_name("sol ring")

    assert loaded is card