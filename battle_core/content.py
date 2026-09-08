"""Ready-made parties for tests, the playable demo, and (later) RL training."""

from __future__ import annotations

from battle_core.entities import Character


def make_default_player_party() -> list[Character]:
    return [
        Character(
            name="Aria", side="player", slot=0, max_hp=34, max_mp=20, base_atk=9, base_def=5, spd=7
        ),
        Character(
            name="Bran", side="player", slot=1, max_hp=42, max_mp=8, base_atk=11, base_def=7, spd=4
        ),
    ]


def make_default_enemy_party(n: int = 2) -> list[Character]:
    roster = [
        Character(
            name="Goblin", side="enemy", slot=0, max_hp=26, max_mp=6, base_atk=8, base_def=4, spd=6
        ),
        Character(
            name="Acolyte",
            side="enemy",
            slot=1,
            max_hp=22,
            max_mp=24,
            base_atk=6,
            base_def=3,
            spd=5,
        ),
        Character(
            name="Brute", side="enemy", slot=2, max_hp=48, max_mp=4, base_atk=12, base_def=6, spd=3
        ),
    ]
    return roster[:n]
