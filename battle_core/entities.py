"""Combatants and the transient effects applied to them."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StatusEffect:
    name: str
    duration: int
    hp_per_turn: int = 0
    atk_mod: int = 0
    def_mod: int = 0


@dataclass
class Character:
    name: str
    side: str
    slot: int
    max_hp: int
    max_mp: int
    base_atk: int
    base_def: int
    spd: int
    hp: int | None = None
    mp: int | None = None
    statuses: list[StatusEffect] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.hp is None:
            self.hp = self.max_hp
        if self.mp is None:
            self.mp = self.max_mp

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def atk(self) -> int:
        return max(0, self.base_atk + sum(s.atk_mod for s in self.statuses))

    @property
    def defense(self) -> int:
        return max(0, self.base_def + sum(s.def_mod for s in self.statuses))

    def take_damage(self, amount: int) -> int:
        applied = min(self.hp, max(0, amount))
        self.hp -= applied
        return applied

    def heal(self, amount: int) -> int:
        applied = min(self.max_hp - self.hp, max(0, amount))
        self.hp += applied
        return applied

    def spend_mp(self, amount: int) -> None:
        self.mp -= amount
        assert self.mp >= 0, f"{self.name} overspent MP"
