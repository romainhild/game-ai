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
    "fireball": Skill(
        id="fireball",
        name="Fireball",
        mp_cost=6,
        power=12,
        target_kind=TargetKind.ONE_ENEMY,
        kind="magic",
    ),
    "firestorm": Skill(
        id="firestorm",
        name="Firestorm",
        mp_cost=14,
        power=9,
        target_kind=TargetKind.ALL_ENEMIES,
        kind="magic",
    ),
    "heal": Skill(
        id="heal",
        name="Heal",
        mp_cost=6,
        power=14,
        target_kind=TargetKind.ONE_ALLY,
        kind="heal",
    ),
    "poison_dart": Skill(
        id="poison_dart",
        name="Poison Dart",
        mp_cost=4,
        power=2,
        target_kind=TargetKind.ONE_ENEMY,
        kind="physical",
        status_template=StatusEffect(name="Poison", duration=3, hp_per_turn=-4),
    ),
    "warcry": Skill(
        id="warcry",
        name="War Cry",
        mp_cost=3,
        power=0,
        target_kind=TargetKind.SELF,
        kind="guard",
        status_template=StatusEffect(name="Braced", duration=2, atk_mod=2, def_mod=4),
    ),
    "guard": Skill(
        id="guard",
        name="Guard",
        mp_cost=0,
        power=0,
        target_kind=TargetKind.SELF,
        kind="guard",
        status_template=StatusEffect(name="Guarding", duration=1, def_mod=6),
    ),
}
