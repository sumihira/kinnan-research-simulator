from __future__ import annotations

from dataclasses import dataclass
from typing import Final


SUPPORTED_LOCALES: Final[frozenset[str]] = frozenset(
    {
        "ja",
        "en",
    }
)


def normalize_locale(
    locale: str,
) -> str:
    """
    Normalize and validate one supported report locale.

    Supported locales:

    - ja: Japanese
    - en: English
    """
    if not isinstance(locale, str):
        raise ValueError(
            "locale must be a string."
        )

    normalized_locale = locale.strip().casefold()

    if normalized_locale not in SUPPORTED_LOCALES:
        supported_locales = ", ".join(
            sorted(SUPPORTED_LOCALES)
        )
        raise ValueError(
            f"locale must be one of: {supported_locales}."
        )

    return normalized_locale


@dataclass(frozen=True, slots=True)
class ReportLocalizer:
    """
    Provides human-readable report text for one locale.

    Internal identifiers and JSON keys are intentionally not translated.
    """

    locale: str = "ja"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "locale",
            normalize_locale(self.locale),
        )

    @property
    def is_japanese(self) -> bool:
        """Return whether Japanese output is selected."""
        return self.locale == "ja"

    def text(
        self,
        *,
        ja: str,
        en: str,
    ) -> str:
        """Return text matching the selected locale."""
        return ja if self.is_japanese else en

    def boolean(
        self,
        value: bool,
    ) -> str:
        """Return a localized boolean value."""
        if self.is_japanese:
            return "はい" if value else "いいえ"

        return "Yes" if value else "No"

    def random_seed(
        self,
        value: int | None,
    ) -> str:
        """Return a localized simulation seed value."""
        if value is not None:
            return str(value)

        return self.text(
            ja="ランダム",
            en="random",
        )

    def optional_integer(
        self,
        value: int | None,
    ) -> str:
        """Return a localized optional integer value."""
        if value is not None:
            return f"{value:,}"

        return self.text(
            ja="該当なし",
            en="N/A",
        )

    def optional_float(
        self,
        value: float | None,
        *,
        decimal_places: int = 3,
    ) -> str:
        """Return a localized optional floating-point value."""
        if decimal_places < 0:
            raise ValueError(
                "decimal_places must not be negative."
            )

        if value is not None:
            return f"{value:.{decimal_places}f}"

        return self.text(
            ja="該当なし",
            en="N/A",
        )

    def optional_number(
        self,
        value: int | float | None,
    ) -> str:
        """Return a localized optional numeric value."""
        if value is None:
            return self.text(
                ja="該当なし",
                en="N/A",
            )

        if isinstance(value, int):
            return f"{value:,}"

        return str(value)