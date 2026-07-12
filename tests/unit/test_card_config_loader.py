from pathlib import Path

from krs.cards.card_config_loader import CardConfigLoader


def test_loads_card_config_by_normalized_name(
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

    loader = CardConfigLoader(tmp_path)

    config = loader.load_by_card_name("  sol   ring ")

    assert config is not None
    assert config.card_name == "Sol Ring"
    assert len(config.abilities["mana"]) == 1