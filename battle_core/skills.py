"""Skill definitions and the arithmetic that resolves them."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from battle_core.entities import Character, StatusEffect


class TargetKind(Enum):
    ONE_ENEMY = "one_enemy"
    ONE_ALLY = "one_ally"
    SELF = "self"
    ALL_ENEMIES = "all_enemies"


@dataclass(frozen=True)
class Skill:
    id: str
    name: str
    mp_cost: int
    power: int
    target_kind: TargetKind
    kind: str
    status_template: StatusEffect | None = None


def physical_damage(attacker: Character, defender: Character, power: int) -> int:
    return max(1, round(power * attacker.atk / max(1, defender.defense)))


def magic_damage(power: int) -> int:
    return max(1, power)


def heal_amount(power: int) -> int:
    return max(1, power)


SKILLS: dict[str, Skill] = {
    "attack": Skill(
        id="attack",
        name="Attack",
        mp_cost=0,
        power=6,
        target_kind=TargetKind.ONE_ENEMY,
        kind="physical",
    ),
}
