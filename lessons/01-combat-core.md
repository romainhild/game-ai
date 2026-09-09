# Lesson 01 — The combat rules engine

## The big idea

Everything in this lesson lives in `battle_core/` and imports nothing but the
standard library. No pygame, no PyTorch. That constraint is deliberate.

A turn-based battle is a **state machine**:

- there is a **state** — everyone's HP, MP, buffs, whose turn it is;
- on each turn the active character picks an **action**;
- the action **transitions** the state to a new one and produces some **events**
  ("Goblin hit Aria for 7", "Aria fainted");
- eventually the state is **terminal** — one side has no one left standing.

In Part C you'll recognise that description as a **Markov Decision Process**, the
formal object reinforcement learning optimises over. The RL agent will call
exactly the same `BattleState.step(action)` you're about to write — it doesn't
get a special simulator, it plays the real game. So the rules engine has to be:

- **pure** — no rendering or ML dependencies, so training can run thousands of
  battles per second;
- **deterministic given a seed** — so a training run is reproducible;
- **explicit about legal moves** — `legal_actions()` will become the RL "action
  mask".

We build it in four stages, each ending with green tests and a commit:

| Stage | File | What |
|---|---|---|
| 1 | `battle_core/entities.py` | `Character`, `StatusEffect` |
| 2 | `battle_core/skills.py` | `Skill`, target kinds, damage/heal math |
| 3 | `battle_core/battle.py` | turn order, the round queue |
| 4 | `battle_core/battle.py`, `content.py` | `step()`, `legal_actions()`, win/lose |

I give you the **tests** in full — writing good tests isn't the skill this
tutorial is about, and having them up front lets you work test-first. For the
implementations: type them in, don't copy-paste. Stage 4's `step()` has a "try
it yourself first" box — that method is the conceptual core.

> **A note on `ruff` and imports.** Ruff 0.16's defaults include import sorting
> (`I001`) and a few style rules (`C408` — prefer `{}` over `dict()`). When it
> flags import order or formatting, don't hand-fight it — run
> `uv run ruff check --fix .` and it rewrites imports to the canonical
> one-per-line sorted form. The code blocks below are already in that form.

---

## Stage 1 — Characters and status effects

### Design decisions, and why

**`Character` is a mutable dataclass.** During a battle we mutate `hp`, `mp`,
`statuses` in place. A fresh `BattleState` is built per battle, so there's no
long-lived shared mutable state to worry about.

**Derived stats are properties, not stored fields.** A character's *effective*
attack changes turn to turn as buffs come and go. If we stored `atk` as a
number we'd have to remember to recompute it every time a status changed.
Instead `base_atk` is stored and `atk` is computed on read:

```python
atk = max(0, base_atk + sum(status.atk_mod for status in statuses))
```

The `max(0, ...)` floor matters: two stacked -5 debuffs on a base-8 attacker
give `atk == 0`, never `-2`. Negative attack would invert the damage formula
later.

**`hp` and `mp` default to their maxima — via a `-1` sentinel.** You almost
always create a full-health character, so it's nice to omit `hp`/`mp` and have
them fill in from `max_hp`/`max_mp`. The tempting way — `hp: int | None = None` +
`__post_init__` — makes a type checker (Pylance, mypy) treat `hp` as
possibly-`None` at every `hp - dmg` for the rest of the file. So instead default
to `-1` (never a meaningful HP value) and check `if self.hp < 0` in
`__post_init__`. `hp` stays a plain `int` everywhere, and a pre-damaged
character for a test is still just `Character(..., hp=1)`.

> An alternative that avoids the magic constant is `InitVar` — a separate
> constructor-only `start_hp: InitVar[int | None]` feeding a stored
> `hp: int = field(init=False)`. More machinery; reach for it in a library where
> callers aren't trusted. The sentinel is fine here.

**`take_damage` / `heal` return the amount that actually landed.** If a
character has 6 HP and takes a 999 hit, only 6 HP is removed — and the renderer
wants to show "6", not "999". Returning the clamped value keeps that logic in
one place.

### The tests

Create `tests/test_entities.py`:

```python
from battle_core import Character, StatusEffect

BASE = {"name": "Hero", "side": "player", "slot": 0, "max_hp": 30, "max_mp": 10,
        "base_atk": 8, "base_def": 4, "spd": 6}


def make_char(**kw) -> Character:
    return Character(**{**BASE, **kw})


def test_hp_and_mp_default_to_max():
    c = make_char()
    assert c.hp == 30
    assert c.mp == 10


def test_alive_reflects_hp():
    c = make_char()
    assert c.alive
    c.take_damage(100)
    assert c.hp == 0
    assert not c.alive


def test_take_damage_returns_applied_and_clamps():
    c = make_char(max_hp=10)
    assert c.take_damage(4) == 4
    assert c.hp == 6
    assert c.take_damage(999) == 6  # only 6 left to remove
    assert c.hp == 0


def test_heal_clamps_to_max():
    c = make_char(max_hp=10)
    c.take_damage(8)
    assert c.heal(999) == 8
    assert c.hp == 10


def test_status_modifies_derived_stats():
    c = make_char(base_atk=8, base_def=4)
    c.statuses.append(StatusEffect(name="Weaken", duration=2, atk_mod=-5))
    assert c.atk == 3
    c.statuses.append(StatusEffect(name="Curse", duration=2, atk_mod=-10))
    assert c.atk == 0  # floored at 0, never negative


def test_spend_mp():
    c = make_char(max_mp=10)
    c.spend_mp(3)
    assert c.mp == 7
```

Run it — everything fails with `ImportError`, because `battle_core` doesn't
export `Character` yet:

```bash
uv run pytest tests/test_entities.py -v
```

### The implementation

Create `battle_core/entities.py`:

```python
"""Combatants and the transient effects applied to them."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StatusEffect:
    name: str
    duration: int          # turns remaining; decremented at the owner's turn start
    hp_per_turn: int = 0    # applied at the owner's turn start; negative = damage
    atk_mod: int = 0
    def_mod: int = 0


@dataclass
class Character:
    name: str
    side: str               # "player" | "enemy"
    slot: int               # position within its side, 0-indexed
    max_hp: int
    max_mp: int
    base_atk: int
    base_def: int
    spd: int
    hp: int = -1            # -1 => fill from max_hp in __post_init__
    mp: int = -1            # -1 => fill from max_mp
    statuses: list[StatusEffect] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.hp < 0:
            self.hp = self.max_hp
        if self.mp < 0:
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
        healed = min(self.max_hp - self.hp, max(0, amount))
        self.hp += healed
        return healed

    def spend_mp(self, amount: int) -> None:
        self.mp -= amount
        assert self.mp >= 0, f"{self.name} overspent MP"
```

> **Why `field(default_factory=list)` and not `= []`?** A bare `[]` default is
> shared by *every* instance of the dataclass — a classic Python foot-gun.
> `default_factory` calls `list()` fresh for each new `Character`.

> **Why `-1` and not `None` for the hp/mp default?** `hp: int | None` is honest
> about the constructor but forces a type checker to assume `hp` might be `None`
> at every `hp - dmg` afterward — noise for the whole file. `-1` is never a real
> HP, `hp` stays a plain `int`, and `if self.hp < 0` in `__post_init__` does the
> fill. The cost: `Character(..., hp=-1)` would quietly become full HP. Nothing
> in this codebase constructs with `hp=` except the odd test, so that's a
> non-issue here.

Now export the names. Edit `battle_core/__init__.py`:

```python
"""Pure-Python combat rules. No pygame, torch, numpy, or game/ imports allowed here."""
from battle_core.entities import Character, StatusEffect

__all__ = ["Character", "StatusEffect"]
```

Run the tests plus the isolation test:

```bash
uv run pytest tests/test_entities.py tests/test_import_isolation.py -v
```

All green? Commit:

```bash
git add -A
git commit -m "feat(part-a): Character and StatusEffect model (Lesson 01)"
```

---

## Stage 2 — Skills and combat math

### Design decisions

**A skill is *data*, not code.** `Skill` is a frozen dataclass; the whole game's
ability list is a dict `SKILLS: dict[str, Skill]`. Adding "Ice Lance" later is
one dict entry — no new class, no new `if` branch in the battle loop. This
matters for RL too: the action space is "pick a skill id × pick a target", and
a data-driven skill list makes that enumeration trivial.

**Four `kind`s, four `TargetKind`s.** `kind` says *what the skill does*
(`physical`, `magic`, `heal`, `guard`); `TargetKind` says *who it can hit*
(`ONE_ENEMY`, `ONE_ALLY`, `SELF`, `ALL_ENEMIES`). They compose — a heal is
usually `heal` + `ONE_ALLY`, an AoE nuke is `magic` + `ALL_ENEMIES`. The battle
engine switches on `kind` (a handful of cases) and expands targets from
`TargetKind` (a handful of cases), so it never grows per-skill.

**Physical damage scales `atk / def`; magic damage is flat.** Design choice with
gameplay consequences: a physical attacker is unreliable against an armoured foe
but scales with buffs; a mage does predictable damage regardless of enemy armour
but is gated by MP. This gives the RL agent a real decision to learn ("is this
target too tanky to punch?"). `max(1, ...)` everywhere guarantees every hit does
*something*.

### The tests

Create `tests/test_skills.py`:

```python
from battle_core import SKILLS, Character, TargetKind
from battle_core.skills import heal_amount, magic_damage, physical_damage

BASE = {"name": "X", "side": "player", "slot": 0, "max_hp": 30, "max_mp": 10,
        "base_atk": 10, "base_def": 5, "spd": 5}


def make_char(**kw) -> Character:
    return Character(**{**BASE, **kw})


def test_physical_damage_scales_with_atk_over_def():
    a = make_char(base_atk=10)
    weak = make_char(base_def=2)
    tough = make_char(base_def=10)
    assert physical_damage(a, weak, power=6) > physical_damage(a, tough, power=6)


def test_physical_damage_never_below_one():
    a = make_char(base_atk=1)
    tank = make_char(base_def=99)
    assert physical_damage(a, tank, power=1) == 1


def test_magic_damage_ignores_stats():
    assert magic_damage(power=12) == 12
    assert magic_damage(power=0) == 1


def test_heal_amount():
    assert heal_amount(power=8) == 8


def test_attack_skill_registered():
    atk = SKILLS["attack"]
    assert atk.mp_cost == 0
    assert atk.target_kind is TargetKind.ONE_ENEMY
    assert atk.kind == "physical"
```

```bash
uv run pytest tests/test_skills.py -v   # fails: no SKILLS / TargetKind yet
```

### The implementation

Create `battle_core/skills.py`:

```python
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
    kind: str                                   # "physical" | "magic" | "heal" | "guard"
    status_template: StatusEffect | None = None


def physical_damage(attacker: Character, defender: Character, power: int) -> int:
    return max(1, round(power * attacker.atk / max(1, defender.defense)))


def magic_damage(power: int) -> int:
    return max(1, power)


def heal_amount(power: int) -> int:
    return max(1, power)


SKILLS: dict[str, Skill] = {
    "attack": Skill(
        id="attack", name="Attack", mp_cost=0, power=6,
        target_kind=TargetKind.ONE_ENEMY, kind="physical",
    ),
}
```

For now `SKILLS` has one entry. Lesson 02 fills in the spells and the buffs.

Update `battle_core/__init__.py`:

```python
"""Pure-Python combat rules. No pygame, torch, numpy, or game/ imports allowed here."""
from battle_core.entities import Character, StatusEffect
from battle_core.skills import SKILLS, Skill, TargetKind

__all__ = ["Character", "StatusEffect", "Skill", "TargetKind", "SKILLS"]
```

```bash
uv run pytest tests/test_skills.py tests/test_import_isolation.py -v
git add -A
git commit -m "feat(part-a): Skill model and combat math (Lesson 01)"
```

---

## Stage 3 — Turn order and the round queue

### The model

Combat runs in **rounds**. At the start of a round we build a queue of every
living character, sorted fastest-first. Characters act in queue order. When the
queue empties, a new round begins and the queue is rebuilt (so a character who
died mid-round is simply gone next round; a newly-summoned one would appear).

The sort key is `(-spd, side_rank, slot)`:

- `-spd` — higher speed acts first;
- `side_rank` — ties broken players-before-enemies (`{"player": 0, "enemy": 1}`);
- `slot` — still-tied characters act in slot order.

**Every tie is broken deterministically.** No RNG in turn ordering. Two reasons:
tests need a predictable order, and Part C needs training runs to be
reproducible from a seed.

`BattleState` also holds `self.rng = random.Random(seed)` now, even though Part A
combat doesn't use it yet — damage variance and hit chance come in a later
balancing pass, and they must go through this instance, never the global
`random` module.

### The tests

Create `tests/test_battle.py`. Import everything now — Stage 4 adds more tests to
this same file and they use these names:

```python
import pytest

from battle_core import (
    SKILLS,
    Action,
    BattleState,
    Character,
    Damage,
    Faint,
    StatusEffect,
    StatusTick,
)


def char(name: str, side: str, slot: int, spd: int, hp: int = 30) -> Character:
    return Character(name=name, side=side, slot=slot, max_hp=hp, max_mp=10,
                     base_atk=8, base_def=4, spd=spd)


def attack(actor: Character, target: Character) -> Action:
    return Action(actor=actor, skill=SKILLS["attack"], target=target)


def test_turn_order_is_speed_then_side_then_slot():
    p_fast = char("Pf", "player", 0, spd=10)
    p_slow = char("Ps", "player", 1, spd=1)
    e_a = char("Ea", "enemy", 0, spd=5)
    e_b = char("Eb", "enemy", 1, spd=5)
    bs = BattleState(players=[p_fast, p_slow], enemies=[e_a, e_b])

    seen = []
    for _ in range(4):
        seen.append(bs.current_actor().name)
        bs._advance(bs.current_actor())
    assert seen == ["Pf", "Ea", "Eb", "Ps"]


def test_new_round_rebuilds_queue():
    p = char("P", "player", 0, spd=5)
    e = char("E", "enemy", 0, spd=3)
    bs = BattleState(players=[p], enemies=[e])
    assert bs.current_actor().name == "P"
    bs._advance(bs.current_actor())
    assert bs.current_actor().name == "E"
    bs._advance(bs.current_actor())
    assert bs.current_actor().name == "P"  # round 2 starts over


def test_current_actor_skips_the_dead():
    p = char("P", "player", 0, spd=5)
    dead = char("D", "enemy", 0, spd=10)
    live = char("L", "enemy", 1, spd=1)
    dead.hp = 0
    bs = BattleState(players=[p], enemies=[dead, live])
    assert bs.current_actor().name == "P"
    bs._advance(bs.current_actor())
    assert bs.current_actor().name == "L"


def test_allies_and_enemies_of():
    p0 = char("P0", "player", 0, spd=5)
    p1 = char("P1", "player", 1, spd=5)
    e0 = char("E0", "enemy", 0, spd=5)
    bs = BattleState(players=[p0, p1], enemies=[e0])
    assert bs.allies_of(p0) == [p0, p1]
    assert bs.enemies_of(p0) == [e0]
    assert bs.enemies_of(e0) == [p0, p1]
```

The tests call `bs._advance(...)` directly — that's fine for this stage. The
public `step()` that wraps it comes in Stage 4.

```bash
uv run pytest tests/test_battle.py -v   # fails: no BattleState
```

### The implementation

Create `battle_core/battle.py`. This stage only needs the queue machinery —
you'll add methods to this same file in Stage 4.

```python
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
```

> **`field(init=False)`** keeps `rng` and `_queue` out of the generated
> `__init__` — you construct a `BattleState` with just parties and an optional
> `seed`, and `__post_init__` sets `rng` up.

> **Why `current_actor()` rebuilds lazily.** Two cases: the queue still has
> living characters (return the first), or it drained this round (rebuild, return
> the first). One filter, one optional rebuild, done — no loop, because a
> freshly built queue already contains only living characters, so re-filtering it
> would change nothing.
>
> If *every* character is dead, `self._queue[0]` raises `IndexError`. That's
> deliberate: callers must check `is_over()` before asking whose turn it is
> (`step()` and the game loop both do). A broken contract should fail loudly on
> the next line, not hang.

Now the event dataclasses need exporting so Stage 4's tests can import them.
Update `battle_core/__init__.py`:

```python
"""Pure-Python combat rules. No pygame, torch, numpy, or game/ imports allowed here."""
from battle_core.battle import (
    Action, BattleState, Damage, Event, Faint, Heal, StatusApplied, StatusTick,
)
from battle_core.entities import Character, StatusEffect
from battle_core.skills import SKILLS, Skill, TargetKind

__all__ = [
    "Character", "StatusEffect", "Skill", "TargetKind", "SKILLS",
    "Action", "BattleState", "Damage", "Heal", "StatusApplied", "StatusTick",
    "Faint", "Event",
]
```

```bash
uv run pytest tests/test_battle.py tests/test_import_isolation.py -v
git add -A
git commit -m "feat(part-a): BattleState turn order and round queue (Lesson 01)"
```

---

## Stage 4 — `step()`, `legal_actions()`, and win/lose

This is the heart of the engine — the transition function the RL agent will
call. Three methods on `BattleState`, plus a `content.py` with ready-made
parties.

### What each method does

**`legal_actions(actor) -> list[Action]`** — enumerate every move `actor` can
legally make right now: for each skill they know and can afford (`mp >=
mp_cost`), one `Action` per valid living target. `SELF` and `ALL_ENEMIES` skills
produce a single `Action` with `target=None`. This method is the single source
of truth for "what's allowed" — the UI menus and the RL action mask both derive
from it.

**`step(action) -> list[Event]`** — advance one turn:

1. assert `action.actor is self.current_actor()` (you can't act out of turn);
2. **tick the actor's statuses first** — poison damage lands at *your* turn
   start, and can kill you before you move;
3. if the actor is still alive, spend the MP and apply the skill's effect,
   collecting `Event`s;
4. compare who was alive before vs after, emit a `Faint` for anyone who dropped;
5. drop fainted characters from the queue, `_advance` past the actor, `turn += 1`;
6. return the ordered event list.

**`is_over()` / `winner()`** — one side has no living members; `winner()` returns
`"player"`, `"enemy"`, or `None`.

**Status ticking rule:** at the actor's turn start, for each `StatusEffect` on
them: apply `hp_per_turn` (emit a `StatusTick` if non-zero), then `duration -=
1`, then drop it if `duration <= 0`. A `duration=3` poison ticks exactly three
times.

### The tests (append to `tests/test_battle.py`)

The imports and the `attack()` helper are already at the top of the file from
Stage 3 — just append these functions:

```python
def test_step_applies_damage_and_returns_events():
    p = char("P", "player", 0, spd=9)
    e = char("E", "enemy", 0, spd=1)
    bs = BattleState(players=[p], enemies=[e])
    events = bs.step(attack(p, e))
    assert e.hp < e.max_hp
    assert any(isinstance(ev, Damage) and ev.target is e for ev in events)
    assert bs.turn == 1


def test_step_rejects_wrong_actor():
    p = char("P", "player", 0, spd=1)
    e = char("E", "enemy", 0, spd=9)  # enemy is first
    bs = BattleState(players=[p], enemies=[e])
    with pytest.raises(AssertionError):
        bs.step(attack(p, e))


def test_faint_event_and_win_condition():
    p = char("P", "player", 0, spd=9)
    e = char("E", "enemy", 0, spd=1, hp=1)
    bs = BattleState(players=[p], enemies=[e])
    events = bs.step(attack(p, e))
    assert any(isinstance(ev, Faint) and ev.target is e for ev in events)
    assert bs.is_over()
    assert bs.winner() == "player"


def test_poison_ticks_at_turn_start():
    p = char("P", "player", 0, spd=9)
    e = char("E", "enemy", 0, spd=1)
    p.statuses.append(StatusEffect(name="Poison", duration=2, hp_per_turn=-3))
    bs = BattleState(players=[p], enemies=[e])
    start_hp = p.hp
    events = bs.step(attack(p, e))
    assert p.hp == start_hp - 3
    assert any(isinstance(ev, StatusTick) for ev in events)
    assert p.statuses[0].duration == 1


def test_legal_actions_expands_over_targets():
    p = char("P", "player", 0, spd=5)
    e0 = char("E0", "enemy", 0, spd=5)
    e1 = char("E1", "enemy", 1, spd=5)
    bs = BattleState(players=[p], enemies=[e0, e1])
    actions = bs.legal_actions(p)
    hit = [a.target for a in actions if a.skill.id == "attack"]
    assert hit == [e0, e1]   # a list, not a set: Character isn't hashable


def test_default_parties_build_and_fight():
    from battle_core.content import make_default_enemy_party, make_default_player_party

    bs = BattleState(players=make_default_player_party(),
                     enemies=make_default_enemy_party())
    for _ in range(500):
        if bs.is_over():
            break
        actor = bs.current_actor()
        bs.step(bs.legal_actions(actor)[0])
    assert bs.is_over()
```

```bash
uv run pytest tests/test_battle.py -v   # the Stage-4 tests fail
```

### Try `step()` yourself first

> Before reading the implementation below, try writing `step()`, `legal_actions()`,
> `is_over()`, and `winner()` from the spec above. Get the Stage-4 tests to pass.
> Then compare with mine — the interesting differences are usually in *ordering*
> (tick before or after the action? advance before or after emitting Faint?) and
> in how you detect "who died this step".

### The implementation

Adjust the imports at the top of `battle_core/battle.py` — add `replace` to the
`dataclasses` line, pull in `StatusEffect`, and widen the skills import. After
`uv run ruff check --fix .` the block looks like this:

```python
from __future__ import annotations

import random
from dataclasses import dataclass, field, replace

from battle_core.entities import Character, StatusEffect
from battle_core.skills import (
    SKILLS,
    Skill,
    TargetKind,
    heal_amount,
    magic_damage,
    physical_damage,
)
```

Add these methods to `BattleState`:

```python
    # ----- enumerating legal moves ------------------------------------
    def _valid_targets(self, actor: Character, kind: TargetKind) -> list[Character | None]:
        match kind:
            case TargetKind.ONE_ENEMY:
                return list(self.enemies_of(actor))
            case TargetKind.ONE_ALLY:
                return list(self.allies_of(actor))
            case TargetKind.SELF | TargetKind.ALL_ENEMIES:
                return [None]

    def legal_actions(self, actor: Character) -> list[Action]:
        out: list[Action] = []
        for skill in SKILLS.values():
            if actor.mp < skill.mp_cost:
                continue
            for target in self._valid_targets(actor, skill.target_kind):
                out.append(Action(actor=actor, skill=skill, target=target))
        return out

    # ----- applying one turn ----------------------------------------
    def _tick_statuses(self, c: Character) -> list[Event]:
        events: list[Event] = []
        surviving: list[StatusEffect] = []
        for st in c.statuses:
            if st.hp_per_turn < 0:
                applied = c.take_damage(-st.hp_per_turn)
                events.append(StatusTick(target=c, amount=-applied, status_name=st.name))
            elif st.hp_per_turn > 0:
                healed = c.heal(st.hp_per_turn)
                events.append(StatusTick(target=c, amount=healed, status_name=st.name))
            st.duration -= 1
            if st.duration > 0:
                surviving.append(st)
        c.statuses = surviving
        return events

    def _apply_skill(self, action: Action) -> list[Event]:
        actor, skill = action.actor, action.skill
        actor.spend_mp(skill.mp_cost)
        events: list[Event] = []

        if skill.target_kind is TargetKind.ALL_ENEMIES:
            victims = list(self.enemies_of(actor))
        elif skill.target_kind is TargetKind.SELF:
            victims = [actor]
        else:
            victims = [action.target] if action.target is not None else []

        for v in victims:
            if skill.kind == "physical":
                dmg = physical_damage(actor, v, skill.power)
                v.take_damage(dmg)
                events.append(Damage(target=v, amount=dmg, source=actor, skill_id=skill.id))
            elif skill.kind == "magic":
                dmg = magic_damage(skill.power)
                v.take_damage(dmg)
                events.append(Damage(target=v, amount=dmg, source=actor, skill_id=skill.id))
            elif skill.kind == "heal":
                got = v.heal(heal_amount(skill.power))
                events.append(Heal(target=v, amount=got, source=actor))
            if skill.status_template is not None:
                v.statuses.append(replace(skill.status_template))
                events.append(StatusApplied(target=v, status_name=skill.status_template.name))
        return events

    def step(self, action: Action) -> list[Event]:
        actor = action.actor
        assert actor is self.current_actor(), "action.actor is not the current actor"
        alive_before = {id(c): c.alive for c in self.all_chars}

        events: list[Event] = []
        events += self._tick_statuses(actor)
        if actor.alive:
            events += self._apply_skill(action)

        for c in self.all_chars:
            if alive_before[id(c)] and not c.alive:
                events.append(Faint(target=c))

        self._queue = [c for c in self._queue if c.alive]
        self._advance(actor)
        self.turn += 1
        return events

    # ----- end conditions -----------------------------------------
    def is_over(self) -> bool:
        return not self.living("player") or not self.living("enemy")

    def winner(self) -> str | None:
        if not self.is_over():
            return None
        return "player" if self.living("player") else "enemy"
```

> **`replace(skill.status_template)`** copies the template so each affected
> character gets its *own* `StatusEffect` instance — otherwise two poisoned
> enemies would share one object and one `duration` counter.

> **`id(c)` as the dict key**, not `c` itself: `Character` is a mutable
> dataclass, so it isn't hashable, and even if it were, `__eq__` compares field
> values — two characters with identical stats would collide. `id()` is
> identity.

### `content.py`

Create `battle_core/content.py`:

```python
"""Ready-made parties for tests, the playable demo, and (later) RL training."""
from __future__ import annotations

from battle_core.entities import Character


def make_default_player_party() -> list[Character]:
    return [
        Character(name="Aria", side="player", slot=0, max_hp=34, max_mp=20,
                  base_atk=9, base_def=5, spd=7),
        Character(name="Bran", side="player", slot=1, max_hp=42, max_mp=8,
                  base_atk=11, base_def=7, spd=4),
    ]


def make_default_enemy_party(n: int = 2) -> list[Character]:
    roster = [
        Character(name="Goblin", side="enemy", slot=0, max_hp=26, max_mp=6,
                  base_atk=8, base_def=4, spd=6),
        Character(name="Acolyte", side="enemy", slot=1, max_hp=22, max_mp=24,
                  base_atk=6, base_def=3, spd=5),
        Character(name="Brute", side="enemy", slot=2, max_hp=48, max_mp=4,
                  base_atk=12, base_def=6, spd=3),
    ]
    return roster[:n]
```

### Verify and record

```bash
uv run pytest -v          # everything green
uv run ruff check .       # clean (fix unused imports etc. if any)
```

Fill in `design.md` → "Skill & Stat Tables" with a table of the default parties
(name / hp / mp / atk / def / spd / side) and the one skill so far (Attack). You
extend both in Lesson 02.

```bash
git add -A
git commit -m "feat(part-a): battle step, legal actions, win conditions (Lesson 01)"
```

---

## Checkpoint

- [ ] `uv run pytest` — all tests pass (`test_entities`, `test_skills`,
      `test_battle`, `test_import_isolation`).
- [ ] `uv run ruff check .` clean.
- [ ] You can open a Python REPL (`uv run python`) and play out a whole battle by
      hand:
      ```python
      from battle_core import BattleState
      from battle_core.content import make_default_player_party, make_default_enemy_party
      bs = BattleState(players=make_default_player_party(), enemies=make_default_enemy_party())
      while not bs.is_over():
          a = bs.current_actor()
          print(a.name, "->", [ (x.skill.id, x.target.name if x.target else None) for x in bs.legal_actions(a) ])
          for ev in bs.step(bs.legal_actions(a)[0]):
              print("  ", ev)
      print("winner:", bs.winner())
      ```
- [ ] Four commits, one per stage.

### What you just built, in RL terms

- `BattleState` is the environment's internal state.
- `legal_actions(actor)` is the action mask.
- `step(action) -> events` is the transition function; the events are what a
  reward function will read.
- `is_over()` / `winner()` give episode termination and the terminal reward.

Lesson 02 adds the actual spells and buffs (so there are interesting decisions to
make), then Lesson 03 puts a pygame face on it. The formal MDP wrapper is
Lesson 08.

Tell me when the checkpoint passes and I'll review before Lesson 02.
