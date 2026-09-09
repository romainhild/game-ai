"""Turn resolution: the queue, action application, and end conditions."""

from __future__ import annotations

import random
from dataclasses import dataclass, field, replace

from battle_core.entities import Character
from battle_core.skills import SKILLS, Skill, TargetKind, heal_amount, magic_damage, physical_damage


@dataclass
class Action:
    actor: Character
    skill: Skill
    target: Character | None = None

    def __str__(self):
        return f"{self.actor.name} used {self.skill.name}" + (
            f" on {self.target.name}" if self.target else ""
        )


@dataclass
class Damage:
    target: Character
    amount: int
    source: Character
    skill_id: str

    def __str__(self):
        return f"{self.amount} damage inflicted on {self.target.name} by {self.source.name} using {self.skill_id}"


@dataclass
class Heal:
    target: Character
    amount: int
    source: Character

    def __str__(self):
        return f"{self.amount} healed on {self.target.name} by {self.source.name}"


@dataclass
class StatusApplied:
    target: Character
    status_name: str

    def __str__(self):
        return f"{self.status_name} applied to {self.target.name}"


@dataclass
class StatusTick:
    target: Character
    amount: int
    status_name: str

    def __str__(self):
        return f"{self.status_name} ticked for {self.amount} on {self.target.name}"


@dataclass
class Faint:
    target: Character

    def __str__(self):
        return f"{self.target.name} fainted"


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

    def legal_actions(self, actor: Character) -> list[Action]:
        actions = []
        for skill_id in actor.skills:
            skill = SKILLS[skill_id]
            if skill.mp_cost > actor.mp:
                continue
            if skill.target_kind is TargetKind.ALL_ENEMIES or skill.target_kind is TargetKind.SELF:
                actions.append(Action(actor=actor, skill=skill, target=None))
            elif skill.target_kind is TargetKind.ONE_ENEMY:
                for c in self.enemies_of(actor):
                    actions.append(Action(actor=actor, skill=skill, target=c))
            elif skill.target_kind is TargetKind.ONE_ALLY:
                for c in self.allies_of(actor):
                    actions.append(Action(actor=actor, skill=skill, target=c))
        return actions

    def step(self, action) -> list[Event]:
        assert action.actor is self.current_actor()
        alives = {id(c): c.alive for c in self.all_chars}
        events = self._tick_statuses(action.actor)

        if action.actor.alive:
            events += self._apply_skill(action)

        for c in self.all_chars:
            if alives[id(c)] and not c.alive:
                events.append(Faint(c))

        self._queue = [c for c in self._queue if c.alive]
        self._advance(action.actor)
        self.turn += 1

        return events

    def _apply_skill(self, action) -> list[Event]:
        events = []
        action.actor.spend_mp(action.skill.mp_cost)

        victims = []
        if action.target is None:
            if action.skill.target_kind == TargetKind.ALL_ENEMIES:
                victims = self.enemies_of(action.actor)
            elif action.skill.target_kind == TargetKind.SELF:
                victims.append(action.actor)
        else:
            victims.append(action.target)

        for v in victims:
            if action.skill.kind == "physical":
                dmg = physical_damage(action.actor, v, action.skill.power)
                applied = v.take_damage(dmg)
                events.append(Damage(v, applied, action.actor, action.skill.id))
            elif action.skill.kind == "magic":
                dmg = magic_damage(action.skill.power)
                applied = v.take_damage(dmg)
                events.append(Damage(v, applied, action.actor, action.skill.id))
            elif action.skill.kind == "heal":
                heal = heal_amount(action.skill.power)
                applied = v.heal(heal)
                events.append(Heal(v, applied, action.actor))
            if action.skill.status_template is not None:
                v.statuses.append(replace(action.skill.status_template))
                events.append(StatusApplied(v, action.skill.status_template.name))
        return events

    def _tick_statuses(self, c: Character):
        events = []
        statuses_to_keep = []
        for status in c.statuses:
            applied = 0
            if status.hp_per_turn < 0:
                applied = -c.take_damage(-status.hp_per_turn)
            elif status.hp_per_turn > 0:
                applied = c.heal(status.hp_per_turn)
            if applied:
                events.append(StatusTick(target=c, amount=applied, status_name=status.name))
            status.duration -= 1
            if status.duration > 0:
                statuses_to_keep.append(status)
        c.statuses = statuses_to_keep
        return events

    def is_over(self) -> bool:
        return (not self.living("player")) or (not self.living("enemy"))

    def winner(self) -> str | None:
        if not self.living("player"):
            return "enemy"
        if not self.living("enemy"):
            return "player"
        return None
