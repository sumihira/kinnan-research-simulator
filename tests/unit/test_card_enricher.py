from pathlib import Path

from krs.cards.card import Card
from krs.cards.card_config_loader import CardConfigLoader
from krs.cards.card_enricher import CardEnricher
from krs.mana.mana import Mana


def test_enriches_sol_ring_with_mana_ability(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "Sol_Ring.yaml"
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