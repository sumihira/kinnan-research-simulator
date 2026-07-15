from __future__ import annotations


def derive_game_seed(
    base_seed: int | None,
    game_id: int,
) -> int | None:
    """
    Derive the deterministic seed used by one simulation game.

    A configured base seed produces a different reproducible seed for each
    non-negative game ID. When no base seed is configured, None is returned
    so the game remains non-deterministic.
    """
    if game_id < 0:
        raise ValueError("game_id must not be negative.")

    if base_seed is None:
        return None

    return base_seed + game_id