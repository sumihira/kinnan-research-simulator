from pathlib import Path

from krs.cards.card import Card
from krs.cards.card_config_loader import CardConfigLoader
from krs.cards.card_enricher import CardEnricher
from krs.mana.mana import Mana


def test_enriches_sol_ring_with_mana_ability(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "sol_ring.yaml"
    config_path.write_text(
        """
card_name: Sol Ring
abilities:
  mana:
    - produces:
        COLORLESS: 2
      requires_tap: true
""".strip(),
        encoding="utf-8",
    )

    card = Card(
        id="sol-ring-id",
        name="Sol Ring",
        mana_cost="{1}",
        mana_value=1,
        oracle_text="{T}: Add {C}{C}.",
        type_line="Artifact",
    )

    enricher = CardEnricher(
        CardConfigLoader(tmp_path)
    )

    enriched = enricher.enrich(card)

    assert enriched is not card
    assert card.mana_abilities == ()
    assert len(enriched.mana_abilities) == 1
    assert (
        enriched.mana_abilities[0]
        .produced_mana[Mana.COLORLESS]
        == 2
    )


def test_enriches_card_with_all_supported_ability_types(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "test_card.yaml"
    config_path.write_text(
        """
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
      event: upkeep
      parameters:
        amount: 1

  etb:
    - ability_type: draw_card
      parameters:
        amount: 2

  replacement:
    - ability_type: choose_creature_type
      event: enters_battlefield
      parameters:
        choice_type: creature_type
""".strip(),
        encoding="utf-8",
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

    assert enriched is not card

    assert card.mana_abilities == ()
    assert card.activated_abilities == ()
    assert card.static_abilities == ()
    assert card.triggered_abilities == ()
    assert card.etb_abilities == ()
    assert card.replacement_abilities == ()

    assert len(enriched.mana_abilities) == 1
    assert len(enriched.activated_abilities) == 1
    assert len(enriched.static_abilities) == 1
    assert len(enriched.triggered_abilities) == 1
    assert len(enriched.etb_abilities) == 1
    assert len(enriched.replacement_abilities) == 1

    assert (
        enriched.mana_abilities[0]
        .produced_mana[Mana.GREEN]
        == 1
    )
    assert (
        enriched.activated_abilities[0].ability_type
        == "untap_self"
    )
    assert enriched.activated_abilities[0].mana_cost == "{3}"
    assert enriched.activated_abilities[0].requires_tap is False
    assert enriched.activated_abilities[0].parameters == {
        "target": "self",
    }

    assert (
        enriched.static_abilities[0].ability_type
        == "skip_normal_untap"
    )
    assert enriched.static_abilities[0].parameters == {
        "applies_during": "untap_step",
    }

    assert (
        enriched.triggered_abilities[0].ability_type
        == "draw_card"
    )
    assert enriched.triggered_abilities[0].event == "upkeep"
    assert enriched.triggered_abilities[0].parameters == {
        "amount": 1,
    }

    assert enriched.etb_abilities[0].ability_type == "draw_card"
    assert enriched.etb_abilities[0].parameters == {
        "amount": 2,
    }

    assert (
        enriched.replacement_abilities[0].ability_type
        == "choose_creature_type"
    )
    assert (
        enriched.replacement_abilities[0].event
        == "enters_battlefield"
    )
    assert enriched.replacement_abilities[0].parameters == {
        "choice_type": "creature_type",
    }


def test_returns_original_card_when_config_does_not_exist(
    tmp_path: Path,
) -> None:
    card = Card(
        id="forest-id",
        name="Forest",
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line="Basic Land — Forest",
    )

    enricher = CardEnricher(
        CardConfigLoader(tmp_path)
    )

    enriched = enricher.enrich(card)

    assert enriched is card
    assert enriched.mana_abilities == ()
    assert enriched.activated_abilities == ()
    assert enriched.static_abilities == ()
    assert enriched.triggered_abilities == ()
    assert enriched.etb_abilities == ()
    assert enriched.replacement_abilities == ()