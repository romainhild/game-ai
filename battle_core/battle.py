"""Turn resolution: the queue, action application, and end conditions."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from battle_core.entities import Character
from battle_core.skills import Skill


@dataclass
class Action:
    actor: Character
    skill: Skill
    target: Character | None = None


@dataclass
class Damage:
    target: Character
    amount: int
    source: Character
    skill_id: str


@dataclass
class Heal:
    target: Character
    amount: int
    source: Character


@dataclass
class StatusApplied:
    target: Character
    status_name: str


@dataclass
class StatusTick:
    target: Character
    amount: int
    status_name: str


@dataclass
class Faint:
    target: Character


Event = Damage | Heal | StatusApplied | StatusTick | Faint

_SIDE_RANK = {"player": 0, "enemy": 1}


@dataclass
class BattleState:
    players: list[Character]
    enemies: list[Character]
    seed: int = 0
    turn: int = 0
    rng: random.Random = field(init=False)
    _queue: list[Character] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)

    @property
    def all_chars(self) -> list[Character]:
        return self.players + self.enemies

    def living(self, side: str) -> list[Character]:
        pool = self.players if side == "player" else self.enemies
        return [c for c in pool if c.alive]

    def allies_of(self, c: Character) -> list[Character]:
        return self.living(c.side)

    def enemies_of(self, c: Character) -> list[Character]:
        other = "enemy" if c.side == "player" else "player"
        return self.living(other)

    def _build_round_queue(self) -> list[Character]:
        living = [c for c in self.all_chars if c.alive]
        return sorted(living, key=lambda c: (-c.spd, _SIDE_RANK[c.side], c.slot))

    def current_actor(self) -> Character:
        self._queue = [c for c in self._queue if c.alive]
        if not self._queue:
            self._queue = self._build_round_queue()
        return self._queue[0]

    def _advance(self, actor: Character) -> None:
        if self._queue and self._queue[0] is actor:
            self._queue.pop(0)
