from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class KinnanChainStatistics:
    """
    Tracks Kinnan activation results within one game.

    A chain continues while Kinnan activations are performed
    without explicitly resetting the current chain.
    """

    activation_count: int = 0
    hit_count: int = 0
    miss_count: int = 0

    current_chain_length: int = 0
    longest_chain_length: int = 0

    hit_card_ids: list[str] = field(default_factory=list)

    def record_hit(self, card_id: str) -> None:
        if not card_id.strip():
            raise ValueError(
                "Hit card ID must not be empty."
            )

        self.activation_count += 1
        self.hit_count += 1
        self.current_chain_length += 1
        self.hit_card_ids.append(card_id)

        self.longest_chain_length = max(
            self.longest_chain_length,
            self.current_chain_length,
        )

    def record_miss(self) -> None:
        self.activation_count += 1
        self.miss_count += 1
        self.current_chain_length = 0

    def reset_current_chain(self) -> None:
        self.current_chain_length = 0

    @property
    def hit_rate(self) -> float:
        if self.activation_count == 0:
            return 0.0

        return self.hit_count / self.activation_count