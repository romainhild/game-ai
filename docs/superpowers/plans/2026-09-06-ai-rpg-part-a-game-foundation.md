# AI RPG Tutorial — Part A: Game Foundation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a playable turn-based RPG battle system plus a walkable town scene in pygame, with all combat rules living in a pure-Python `battle_core` package that has no rendering or ML dependencies.

**Architecture:** `battle_core/` is the single source of truth for combat rules (entities, skills, turn resolution) and is tested hard with TDD. `game/` renders and takes input, driving the same `BattleState` objects `battle_core` exposes. A scene manager in `game/app.py` switches between a `TownScene` and a `BattleScene`. No AI yet — the enemy uses a scripted heuristic; NPCs print placeholder lines.

**Tech Stack:** Python 3.11+, `uv` for project/dependency management, `pygame-ce` for rendering/input, `pytest` for tests, `ruff` for linting. `numpy` is added now because later parts need it.

**Spec:** `docs/superpowers/specs/2026-09-06-ai-rpg-tutorial-design.md`

## Global Constraints

- **Python 3.11+.** Use `match` statements and `X | Y` union syntax freely.
- **`uv` only.** `pyproject.toml` is the sole dependency manifest. No `requirements.txt`, no `pip install`. Add deps with `uv add` / `uv add --dev`. Run everything with `uv run ...`.
- **`battle_core/` must not import `pygame`, `torch`, `numpy`, or anything from `game/`, `rl/`, `dialogue/`.** It is pure standard-library Python. A test enforces this.
- **Flat package layout** at repo root: `battle_core/`, `game/`, and later `rl/`, `dialogue/`. Run modules as `uv run python -m game.app`. Tests configured with `pythonpath = ["."]`.
- **Determinism:** all randomness in `battle_core` goes through a `random.Random` instance stored on `BattleState`. No calls to the global `random` module. Part A combat is fully deterministic given a seed.
- **Every lesson produces a markdown file** in `lessons/` and a green test suite. The lesson file is written as the final step of the task that completes that lesson.
- **Commit after every task.** Commit messages: `feat(part-a): <what>` or `docs(part-a): <what>` or `test(part-a): <what>`.
- Commit trailer for every commit:
  ```
  Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01UeDGqvd3Lq7FDpWocKW2Bj
  ```

---

## File Structure

**Created in Part A:**

| Path | Responsibility |
|---|---|
| `pyproject.toml` | project metadata, deps, pytest config (uv-managed) |
| `.python-version` | pins Python for uv (created by `uv init`) |
| `README.md` | one-paragraph project description + how to run |
| `design.md` | condensed architecture + skill/stat tables (living reference) |
| `battle_core/__init__.py` | re-exports the public API (`Character`, `Skill`, `BattleState`, `Action`, events) |
| `battle_core/entities.py` | `Character`, `StatusEffect` dataclasses + derived-stat properties |
| `battle_core/skills.py` | `Skill`, `TargetKind`, the `SKILLS` registry, damage/heal math |
| `battle_core/battle.py` | `Action`, event dataclasses, `BattleState` (turn order, `step`, `legal_actions`, `is_over`, `winner`) |
| `battle_core/heuristics.py` | `scripted_enemy_action`, `scripted_player_action` |
| `battle_core/content.py` | `make_default_player_party()`, `make_default_enemy_party()` factory helpers |
| `game/__init__.py` | empty package marker |
| `game/app.py` | `main()`, `Game` (window, clock, scene stack, transitions) |
| `game/scene.py` | `Scene` protocol/ABC: `handle_event`, `update`, `draw` |
| `game/ui.py` | shared draw helpers: `draw_bar`, `draw_text`, `draw_panel`, `Menu` widget |
| `game/scenes/__init__.py` | empty package marker |
| `game/scenes/battle.py` | `BattleScene` — renders a `BattleState`, player input, message log |
| `game/scenes/town.py` | `TownScene` — tile grid, player movement, collision, NPCs, battle trigger |
| `game/tilemap.py` | `TileMap` — grid data, `is_walkable`, pixel/tile conversion |
| `tests/test_import_isolation.py` | asserts `battle_core` imports nothing forbidden |
| `tests/test_entities.py` | `Character`, `StatusEffect` behaviour |
| `tests/test_skills.py` | damage/heal math, skill registry |
| `tests/test_battle.py` | turn order, `step`, `legal_actions`, win/lose |
| `tests/test_heuristics.py` | scripted AI picks sane actions |
| `tests/test_tilemap.py` | walkability, coordinate conversion |
| `tests/test_town_logic.py` | movement/collision/NPC-proximity (headless) |
| `lessons/00-setup.md` … `lessons/04-town.md` | the tutorial prose |

**Not created until later parts:** `rl/`, `dialogue/`, `game/policy_runtime.py`, `checkpoints/`.

---

## Task 1: Project scaffold and a blank window (Lesson 00)

**Files:**
- Create: `pyproject.toml` (via `uv init`, then edited), `.python-version`, `README.md`, `design.md`
- Create: `battle_core/__init__.py`, `game/__init__.py`, `game/app.py`
- Create: `tests/test_import_isolation.py`
- Create: `lessons/00-setup.md`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `game.app.main() -> None` — opens an 800×600 window titled "AI RPG", fills it dark grey, closes cleanly on the window close button or `Esc`.
  - `battle_core` package importable; its `__init__.py` is empty for now.

- [ ] **Step 1: Initialise the uv project**

Run in repo root (which already contains `docs/` and `.git/`):
```bash
uv init --name ai-rpg --python 3.11 --no-workspace
rm -f main.py hello.py        # remove the sample module uv creates, whichever name it used
```
Expected: `pyproject.toml`, `.python-version` created.

- [ ] **Step 2: Add dependencies**

```bash
uv add pygame-ce numpy
uv add --dev pytest ruff
```
Expected: `pyproject.toml` gains `[project].dependencies` and `[dependency-groups].dev`; `uv.lock` created; `.venv/` created.

- [ ] **Step 3: Configure pytest in `pyproject.toml`**

Append to `pyproject.toml`:
```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
```

- [ ] **Step 4: Create the package markers and the app module**

`battle_core/__init__.py`:
```python
"""Pure-Python combat rules. No pygame, torch, numpy, or game/ imports allowed here."""
```

`game/__init__.py`:
```python
```

`game/app.py`:
```python
"""Entry point: window, clock, and (later) the scene stack."""
from __future__ import annotations

import pygame

WINDOW_SIZE = (800, 600)
BG_COLOR = (24, 24, 28)
FPS = 60


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("AI RPG")
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        screen.fill(BG_COLOR)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Write the import-isolation test**

`tests/test_import_isolation.py`:
```python
"""battle_core must stay pure: no rendering or ML dependencies, no reaching into other app packages."""
import importlib
import pkgutil
import sys

import battle_core

FORBIDDEN = {"pygame", "torch", "numpy", "game", "rl", "dialogue"}


def test_battle_core_imports_nothing_forbidden():
    # Import every submodule of battle_core, then inspect what landed in sys.modules.
    for mod in pkgutil.iter_modules(battle_core.__path__, prefix="battle_core."):
        importlib.import_module(mod.name)

    leaked = {name.split(".")[0] for name in sys.modules} & FORBIDDEN
    assert not leaked, f"battle_core pulled in forbidden modules: {leaked}"
```

- [ ] **Step 6: Run the test, expect PASS**

Run: `uv run pytest tests/test_import_isolation.py -v`
Expected: PASS (battle_core has only an empty `__init__.py` so far).

- [ ] **Step 7: Manually verify the window**

Run: `uv run python -m game.app`
Expected: an 800×600 dark-grey window titled "AI RPG". Pressing `Esc` or clicking the close button exits with no traceback.

- [ ] **Step 8: Write `README.md` and `design.md`**

`README.md`:
```markdown
# AI RPG

A tutorial project: a small turn-based RPG with LLM-driven NPC dialogue and a
from-scratch reinforcement-learning policy controlling enemies.

## Run

```bash
uv run python -m game.app     # play
uv run pytest                 # tests
```

See `lessons/` for the step-by-step build and `design.md` for the architecture.
```

`design.md`: copy Sections 5 (Architecture), 5.3 (MDP), and 6 (Curriculum) from the spec, trimmed to reference form. Add an empty "## Skill & Stat Tables" section — Task 7 fills it in.

- [ ] **Step 9: Write `lessons/00-setup.md`**

Contents (write full prose, ~400–600 words):
- What we're building across the whole tutorial (one paragraph, link to `design.md`).
- Why `uv`: single tool for Python version + venv + deps + running; no manual `venv`/`pip`.
- The exact commands from Steps 1–3, explained line by line.
- Why the flat package layout and `python -m` (so `battle_core` and `game` are importable siblings).
- Walk through `game/app.py`: `pygame.init`, the display surface, the event loop, `flip` vs `update`, `clock.tick(FPS)` and why it caps the frame rate.
- The `battle_core` purity rule and what `test_import_isolation.py` enforces, and why that boundary matters (the RL env in Part C will import `battle_core` directly).
- Checkpoint: "You can run `uv run python -m game.app` and see a window; `uv run pytest` is green."

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "feat(part-a): project scaffold and blank pygame window (Lesson 00)"
```

---

## Task 2: Character and status model (Lesson 01, part 1)

**Files:**
- Create: `battle_core/entities.py`
- Create: `tests/test_entities.py`
- Modify: `battle_core/__init__.py` (re-export `Character`, `StatusEffect`)

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `StatusEffect(name: str, duration: int, hp_per_turn: int = 0, atk_mod: int = 0, def_mod: int = 0)` — a dataclass. `hp_per_turn` negative = damage over time.
  - `Character(name: str, side: str, slot: int, max_hp: int, max_mp: int, base_atk: int, base_def: int, spd: int, hp: int | None = None, mp: int | None = None, statuses: list[StatusEffect] = <factory>)` — dataclass. `hp`/`mp` default to their maxes via `__post_init__`.
  - `Character.alive: bool` (property) — `hp > 0`.
  - `Character.atk: int` (property) — `max(0, base_atk + sum(s.atk_mod for statuses))`.
  - `Character.defense: int` (property) — `max(0, base_def + sum(s.def_mod for statuses))`.
  - `Character.take_damage(amount: int) -> int` — clamps `hp` to `>= 0`, returns damage actually applied.
  - `Character.heal(amount: int) -> int` — clamps `hp` to `<= max_hp`, returns amount actually healed.
  - `Character.spend_mp(amount: int) -> None` — subtracts, asserts `>= 0` result.
  - `side` is the string `"player"` or `"enemy"`.

- [ ] **Step 1: Write the failing tests**

`tests/test_entities.py`:
```python
from battle_core import Character, StatusEffect


def make_char(**kw) -> Character:
    defaults = dict(name="Hero", side="player", slot=0, max_hp=30, max_mp=10,
                    base_atk=8, base_def=4, spd=6)
    defaults.update(kw)
    return Character(**defaults)


def test_hp_and_mp_default_to_max():
    c = make_char()
    assert c.hp == 30 and c.mp == 10


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

- [ ] **Step 2: Run the tests, expect FAIL**

Run: `uv run pytest tests/test_entities.py -v`
Expected: FAIL — `ImportError: cannot import name 'Character' from 'battle_core'`.

- [ ] **Step 3: Implement `battle_core/entities.py`**

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
        healed = min(self.max_hp - self.hp, max(0, amount))
        self.hp += healed
        return healed

    def spend_mp(self, amount: int) -> None:
        self.mp -= amount
        assert self.mp >= 0, f"{self.name} overspent MP"
```

- [ ] **Step 4: Re-export from `battle_core/__init__.py`**

```python
"""Pure-Python combat rules. No pygame, torch, numpy, or game/ imports allowed here."""
from battle_core.entities import Character, StatusEffect

__all__ = ["Character", "StatusEffect"]
```

- [ ] **Step 5: Run the tests, expect PASS**

Run: `uv run pytest tests/test_entities.py tests/test_import_isolation.py -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat(part-a): Character and StatusEffect model (Lesson 01)"
```

---

## Task 3: Skill model and combat math (Lesson 01, part 2)

**Files:**
- Create: `battle_core/skills.py`
- Create: `tests/test_skills.py`
- Modify: `battle_core/__init__.py` (re-export `Skill`, `TargetKind`, `SKILLS`)

**Interfaces:**
- Consumes: `Character` from Task 2.
- Produces:
  - `class TargetKind(enum.Enum)` with members `ONE_ENEMY`, `ONE_ALLY`, `SELF`, `ALL_ENEMIES`.
  - `Skill` — `@dataclass(frozen=True)`: `id: str`, `name: str`, `mp_cost: int`, `power: int`, `target_kind: TargetKind`, `kind: str` (one of `"physical"`, `"magic"`, `"heal"`, `"guard"`), `status_template: StatusEffect | None = None`.
  - `physical_damage(attacker: Character, defender: Character, power: int) -> int` — `max(1, round(power * attacker.atk / max(1, defender.defense)))`.
  - `magic_damage(power: int) -> int` — `max(1, power)` (defense-ignoring; kept simple for Part A).
  - `heal_amount(power: int) -> int` — `max(1, power)`.
  - `SKILLS: dict[str, Skill]` — for Lesson 01 it contains exactly one entry, `"attack"`: `Skill("attack", "Attack", mp_cost=0, power=6, target_kind=TargetKind.ONE_ENEMY, kind="physical")`.

- [ ] **Step 1: Write the failing tests**

`tests/test_skills.py`:
```python
from battle_core import Character, SKILLS, TargetKind
from battle_core.skills import heal_amount, magic_damage, physical_damage


def make_char(**kw) -> Character:
    defaults = dict(name="X", side="player", slot=0, max_hp=30, max_mp=10,
                    base_atk=10, base_def=5, spd=5)
    defaults.update(kw)
    return Character(**defaults)


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

- [ ] **Step 2: Run the tests, expect FAIL**

Run: `uv run pytest tests/test_skills.py -v`
Expected: FAIL — `ImportError` for `SKILLS` / `TargetKind`.

- [ ] **Step 3: Implement `battle_core/skills.py`**

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

- [ ] **Step 4: Re-export from `battle_core/__init__.py`**

```python
"""Pure-Python combat rules. No pygame, torch, numpy, or game/ imports allowed here."""
from battle_core.entities import Character, StatusEffect
from battle_core.skills import SKILLS, Skill, TargetKind

__all__ = ["Character", "StatusEffect", "Skill", "TargetKind", "SKILLS"]
```

- [ ] **Step 5: Run the tests, expect PASS**

Run: `uv run pytest tests/test_skills.py tests/test_import_isolation.py -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat(part-a): Skill model and combat math (Lesson 01)"
```

---

## Task 4: BattleState — turn order and the round queue (Lesson 01, part 3)

**Files:**
- Create: `battle_core/battle.py`
- Create: `tests/test_battle.py`
- Modify: `battle_core/__init__.py` (re-export `BattleState`, `Action`, event classes)

**Interfaces:**
- Consumes: `Character` (Task 2), `Skill`, `SKILLS`, `TargetKind` (Task 3).
- Produces:
  - `Action` — `@dataclass`: `actor: Character`, `skill: Skill`, `target: Character | None` (`None` for `SELF` / `ALL_ENEMIES`).
  - Event dataclasses (all `@dataclass`): `Damage(target: Character, amount: int, source: Character, skill_id: str)`, `Heal(target: Character, amount: int, source: Character)`, `StatusApplied(target: Character, status_name: str)`, `StatusTick(target: Character, amount: int, status_name: str)`, `Faint(target: Character)`. `Event = Damage | Heal | StatusApplied | StatusTick | Faint`.
  - `BattleState` — `@dataclass`: `players: list[Character]`, `enemies: list[Character]`, `seed: int = 0`. Internals: `self.rng = random.Random(seed)`, `self.turn = 0`, `self._queue: list[Character] = []`.
  - `BattleState.all_chars -> list[Character]` (property) — `players + enemies`.
  - `BattleState.living(side: str) -> list[Character]` — alive chars on that side, slot order.
  - `BattleState.current_actor() -> Character` — the character whose turn it is; rebuilds the round queue when empty. Never returns a fainted character.
  - `BattleState.allies_of(c: Character) -> list[Character]` / `enemies_of(c: Character) -> list[Character]` — living, by slot.
  - Turn order within a round: all living characters sorted by `spd` descending; ties broken by `side` (`"player"` before `"enemy"`) then `slot` ascending. Deterministic — no RNG in ordering for Part A.

- [ ] **Step 1: Write the failing tests**

`tests/test_battle.py`:
```python
from battle_core import BattleState, Character


def char(name, side, slot, spd, hp=30) -> Character:
    return Character(name=name, side=side, slot=slot, max_hp=hp, max_mp=10,
                     base_atk=8, base_def=4, spd=spd)


def test_turn_order_is_speed_then_side_then_slot():
    p_fast = char("Pf", "player", 0, spd=10)
    p_slow = char("Ps", "player", 1, spd=1)
    e_mid_a = char("Ea", "enemy", 0, spd=5)
    e_mid_b = char("Eb", "enemy", 1, spd=5)
    bs = BattleState(players=[p_fast, p_slow], enemies=[e_mid_a, e_mid_b])

    seen = []
    for _ in range(4):
        seen.append(bs.current_actor().name)
        # pop the actor manually for this test via the private helper
        bs._advance(bs.current_actor())
    assert seen == ["Pf", "Ea", "Eb", "Ps"]


def test_new_round_rebuilds_queue():
    p = char("P", "player", 0, spd=5)
    e = char("E", "enemy", 0, spd=3)
    bs = BattleState(players=[p], enemies=[e])
    order_round_1 = [bs.current_actor().name, (bs._advance(bs.current_actor()), bs.current_actor().name)[1]]
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

- [ ] **Step 2: Run the tests, expect FAIL**

Run: `uv run pytest tests/test_battle.py -v`
Expected: FAIL — `ImportError` for `BattleState`.

- [ ] **Step 3: Implement the queue/order part of `battle_core/battle.py`**

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
        while True:
            self._queue = [c for c in self._queue if c.alive]
            if not self._queue:
                self._queue = self._build_round_queue()
            if self._queue:
                return self._queue[0]

    def _advance(self, actor: Character) -> None:
        if self._queue and self._queue[0] is actor:
            self._queue.pop(0)
```

Note the test calls `bs._advance(...)` directly — that is deliberate for this task; Task 5 adds the public `step()` that calls it.

- [ ] **Step 4: Re-export from `battle_core/__init__.py`**

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

- [ ] **Step 5: Run the tests, expect PASS**

Run: `uv run pytest tests/test_battle.py tests/test_import_isolation.py -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat(part-a): BattleState turn order and round queue (Lesson 01)"
```

---

## Task 5: BattleState — step, legal_actions, win/lose (completes Lesson 01)

**Files:**
- Modify: `battle_core/battle.py` (add methods to `BattleState`)
- Modify: `tests/test_battle.py` (add tests)
- Create: `battle_core/content.py`
- Create: `lessons/01-combat-core.md`

**Interfaces:**
- Consumes: everything from Task 4, plus `SKILLS`, `TargetKind`, `physical_damage`, `magic_damage`, `heal_amount` from Task 3.
- Produces:
  - `BattleState.legal_actions(actor: Character) -> list[Action]` — every skill in `SKILLS` the actor can afford (`mp >= mp_cost`), expanded over every valid living target for its `target_kind`. `SELF` and `ALL_ENEMIES` produce one `Action` with `target=None`.
  - `BattleState.step(action: Action) -> list[Event]` — asserts `action.actor is self.current_actor()`; ticks the actor's statuses (turn start); if the actor is still alive, spends MP and applies the skill effect; appends `Faint` events for anyone brought to 0; removes fainted characters from the queue; calls `self._advance(action.actor)`; increments `self.turn`. Returns the ordered event list.
  - `BattleState.is_over() -> bool` — one side has no living members.
  - `BattleState.winner() -> str | None` — `"player"`, `"enemy"`, or `None` if not over.
  - Status ticking: at the actor's turn start, for each `StatusEffect` on the actor: apply `hp_per_turn` (emit `StatusTick` if non-zero), decrement `duration`, drop it when `duration <= 0`.
  - `battle_core/content.py`: `make_default_player_party() -> list[Character]` (2 members) and `make_default_enemy_party(n: int = 2) -> list[Character]`. Exact stat lines go in `design.md` (Step 7) and Task 7 extends them; for Lesson 01 give each character `max_mp` large enough that MP is not yet a constraint.

- [ ] **Step 1: Write the failing tests (append to `tests/test_battle.py`)**

```python
from battle_core import SKILLS, Action


def _attack(bs, actor, target):
    return Action(actor=actor, skill=SKILLS["attack"], target=target)


def test_step_applies_damage_and_returns_events():
    p = char("P", "player", 0, spd=9)
    e = char("E", "enemy", 0, spd=1)
    bs = BattleState(players=[p], enemies=[e])
    events = bs.step(_attack(bs, p, e))
    assert e.hp < e.max_hp
    assert any(isinstance(ev, Damage) and ev.target is e for ev in events)
    assert bs.turn == 1


def test_step_rejects_wrong_actor():
    p = char("P", "player", 0, spd=1)
    e = char("E", "enemy", 0, spd=9)  # enemy is first
    bs = BattleState(players=[p], enemies=[e])
    try:
        bs.step(_attack(bs, p, e))
        assert False, "expected assertion"
    except AssertionError:
        pass


def test_faint_event_and_queue_removal():
    p = char("P", "player", 0, spd=9)
    e = char("E", "enemy", 0, spd=1, hp=1)
    bs = BattleState(players=[p], enemies=[e])
    events = bs.step(_attack(bs, p, e))
    assert any(isinstance(ev, Faint) and ev.target is e for ev in events)
    assert bs.is_over()
    assert bs.winner() == "player"


def test_poison_ticks_at_turn_start():
    from battle_core import StatusEffect
    p = char("P", "player", 0, spd=9)
    e = char("E", "enemy", 0, spd=1)
    p.statuses.append(StatusEffect(name="Poison", duration=2, hp_per_turn=-3))
    bs = BattleState(players=[p], enemies=[e])
    start_hp = p.hp
    events = bs.step(_attack(bs, p, e))
    assert p.hp == start_hp - 3
    assert any(isinstance(ev, StatusTick) for ev in events)
    assert p.statuses[0].duration == 1


def test_legal_actions_expands_over_targets():
    p = char("P", "player", 0, spd=5)
    e0 = char("E0", "enemy", 0, spd=5)
    e1 = char("E1", "enemy", 1, spd=5)
    bs = BattleState(players=[p], enemies=[e0, e1])
    actions = bs.legal_actions(p)
    targets = {a.target for a in actions if a.skill.id == "attack"}
    assert targets == {e0, e1}


def test_default_parties_build_and_fight():
    from battle_core.content import make_default_enemy_party, make_default_player_party
    bs = BattleState(players=make_default_player_party(), enemies=make_default_enemy_party())
    guard = 0
    while not bs.is_over() and guard < 500:
        actor = bs.current_actor()
        opts = bs.legal_actions(actor)
        bs.step(opts[0])
        guard += 1
    assert bs.is_over()
```

- [ ] **Step 2: Run the tests, expect FAIL**

Run: `uv run pytest tests/test_battle.py -v`
Expected: FAIL — `AttributeError: 'BattleState' object has no attribute 'legal_actions'` (and `content` import error).

- [ ] **Step 3: Add the methods to `BattleState` in `battle_core/battle.py`**

Add these imports at the top:
```python
from battle_core.skills import (
    SKILLS, Skill, TargetKind, physical_damage, magic_damage, heal_amount,
)
```

Add methods to `BattleState`:
```python
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

    def _tick_statuses(self, c: Character) -> list[Event]:
        events: list[Event] = []
        surviving: list = []
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
                amt = heal_amount(skill.power)
                got = v.heal(amt)
                events.append(Heal(target=v, amount=got, source=actor))
            if skill.status_template is not None:
                from dataclasses import replace
                v.statuses.append(replace(skill.status_template))
                events.append(StatusApplied(target=v, status_name=skill.status_template.name))

        # "guard" kind: a self status_template only, handled by the block above when target_kind is SELF
        return events

    def step(self, action: Action) -> list[Event]:
        actor = action.actor
        assert actor is self.current_actor(), "action.actor is not the current actor"
        events: list[Event] = []
        events += self._tick_statuses(actor)
        if actor.alive:
            events += self._apply_skill(action)
        for c in self.all_chars:
            if not c.alive and not any(isinstance(e, Faint) and e.target is c for e in events):
                # only emit Faint for someone who died this step
                pass
        newly_dead = [c for c in self.all_chars if c.hp == 0]
        for c in newly_dead:
            if not any(isinstance(e, Faint) and e.target is c for e in events):
                events.append(Faint(target=c))
        self._queue = [c for c in self._queue if c.alive]
        self._advance(actor)
        self.turn += 1
        return events

    def is_over(self) -> bool:
        return not self.living("player") or not self.living("enemy")

    def winner(self) -> str | None:
        if not self.is_over():
            return None
        return "player" if self.living("player") else "enemy"
```

Note: the `Faint` emission above is slightly loose (it re-emits nothing for already-dead, but in Part A nobody starts a step dead except via poison in the same step, which is fine). If a cleaner rule is wanted, snapshot `alive` per character before the step and diff — acceptable to add now.

Refine to the snapshot approach for correctness:
```python
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
```
Use this version.

- [ ] **Step 4: Implement `battle_core/content.py`**

```python
"""Ready-made parties for tests, the playable demo, and (later) RL training."""
from __future__ import annotations

from battle_core.entities import Character


def make_default_player_party() -> list[Character]:
    return [
        Character(name="Aria",  side="player", slot=0, max_hp=34, max_mp=20,
                  base_atk=9, base_def=5, spd=7),
        Character(name="Bran",  side="player", slot=1, max_hp=42, max_mp=8,
                  base_atk=11, base_def=7, spd=4),
    ]


def make_default_enemy_party(n: int = 2) -> list[Character]:
    roster = [
        Character(name="Goblin", side="enemy", slot=0, max_hp=26, max_mp=6,
                  base_atk=8, base_def=4, spd=6),
        Character(name="Acolyte", side="enemy", slot=1, max_hp=22, max_mp=24,
                  base_atk=6, base_def=3, spd=5),
        Character(name="Brute",  side="enemy", slot=2, max_hp=48, max_mp=4,
                  base_atk=12, base_def=6, spd=3),
    ]
    return roster[:n]
```

- [ ] **Step 5: Run the full suite, expect PASS**

Run: `uv run pytest -v`
Expected: all PASS.

- [ ] **Step 6: Lint**

Run: `uv run ruff check .`
Fix anything it flags (unused imports, etc.), re-run until clean.

- [ ] **Step 7: Fill in `design.md` "Skill & Stat Tables"**

Add a markdown table of the default parties (name, hp, mp, atk, def, spd, side) and a skills table (currently just Attack; Task 7 adds the rest).

- [ ] **Step 8: Write `lessons/01-combat-core.md`** (~700–1000 words)

- The MDP intuition, informally: a battle is a sequence of states; each turn one character picks an action; the state transitions; eventually someone wins. Part C makes this formal — Part A just builds the state machine.
- Walk through `Character`: why derived stats (`atk`, `defense`) are properties, not stored fields (statuses change them turn to turn); why `hp`/`mp` default via `__post_init__`.
- Walk through `Skill` as *data*: adding a new skill later is a dict entry, not a new class or `if` branch. Point at `SKILLS`.
- The damage formulas and why physical scales `atk/def` but magic is flat (design choice: makes mages reliable vs armoured foes; revisit in balancing).
- `BattleState`: the round queue, the speed/side/slot sort, why ties must be deterministic (tests, and Part C reproducibility).
- `step()` line by line: assert-current-actor, tick statuses first (poison can kill before you move), apply skill, diff `alive` to emit `Faint`, advance the queue, bump `turn`.
- `legal_actions()` and why the environment in Part C will call it to build the action mask.
- The `test_default_parties_build_and_fight` "monkey" test: a crude sanity check that any greedy policy terminates the battle.
- Checkpoint: "`uv run pytest` green; you can simulate a whole battle in a Python REPL."

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat(part-a): battle step, legal actions, win conditions (Lesson 01)"
```

---

## Task 6: MP economy and multi-turn status effects (Lesson 02, part 1)

**Files:**
- Modify: `tests/test_battle.py` (add MP-constraint and status-duration tests)
- Modify: `battle_core/battle.py` only if a bug surfaces (the Task 5 implementation should already cover this)
- Create: `tests/test_status_effects.py`

**Interfaces:**
- Consumes: everything so far.
- Produces: no new public API — this task hardens and documents the MP + status behaviour with tests, and fixes any bug they reveal. If `legal_actions` or `_tick_statuses` needs a fix, make it here.

- [ ] **Step 1: Write the tests**

`tests/test_status_effects.py`:
```python
from battle_core import BattleState, Character, StatusEffect, SKILLS, Action


def char(name, side, slot, spd=5, mp=10) -> Character:
    return Character(name=name, side=side, slot=slot, max_hp=40, max_mp=mp,
                     base_atk=8, base_def=4, spd=spd)


def attack(bs, actor, target):
    return Action(actor=actor, skill=SKILLS["attack"], target=target)


def test_status_expires_after_its_duration():
    p = char("P", "player", 0, spd=9)
    e = char("E", "enemy", 0, spd=1)
    p.statuses.append(StatusEffect(name="Regen", duration=2, hp_per_turn=2))
    p.take_damage(10)
    bs = BattleState(players=[p], enemies=[e])
    bs.step(attack(bs, p, e))      # tick 1: heal 2, duration -> 1
    # force P's next turn: advance through E
    bs.step(Action(actor=bs.current_actor(), skill=SKILLS["attack"], target=p))
    bs.step(attack(bs, bs.current_actor(), e))  # P again, tick 2: heal 2, duration -> 0
    assert p.statuses == []


def test_atk_debuff_reduces_damage_then_wears_off():
    attacker = char("A", "player", 0, spd=9)
    victim = char("V", "enemy", 0, spd=1)
    bs = BattleState(players=[attacker], enemies=[victim])

    baseline = None
    from battle_core.skills import physical_damage
    baseline = physical_damage(attacker, victim, SKILLS["attack"].power)

    attacker.statuses.append(StatusEffect(name="Weaken", duration=1, atk_mod=-4))
    weak = physical_damage(attacker, victim, SKILLS["attack"].power)
    assert weak < baseline


def test_legal_actions_respects_mp():
    poor = char("Poor", "player", 0, mp=0)
    bs = BattleState(players=[poor], enemies=[char("E", "enemy", 0)])
    # only the zero-cost attack is available
    assert all(a.skill.mp_cost == 0 for a in bs.legal_actions(poor))
```

- [ ] **Step 2: Run, expect FAIL or PASS**

Run: `uv run pytest tests/test_status_effects.py -v`
Expected: these should mostly PASS given Task 5's implementation. If `test_status_expires_after_its_duration` fails because of an off-by-one in duration handling, fix `_tick_statuses` so a `duration=N` status ticks exactly `N` times then is removed.

- [ ] **Step 3: Fix any bug the tests reveal**

If needed, adjust `_tick_statuses` in `battle_core/battle.py`. Re-run until green.

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "test(part-a): MP economy and status-effect duration coverage (Lesson 02)"
```

---

## Task 7: The spell and ability set (Lesson 02, part 2)

**Files:**
- Modify: `battle_core/skills.py` (add skills to `SKILLS`)
- Modify: `battle_core/battle.py` (handle `kind == "guard"`)
- Modify: `tests/test_skills.py` (add per-skill tests)
- Modify: `design.md` (skills table)

**Interfaces:**
- Consumes: `StatusEffect`, `Skill`, `TargetKind`.
- Produces — `SKILLS` gains these entries:
  - `"fireball"` — `mp_cost=6, power=12, target_kind=ONE_ENEMY, kind="magic"`.
  - `"firestorm"` — `mp_cost=14, power=9, target_kind=ALL_ENEMIES, kind="magic"`.
  - `"heal"` — `mp_cost=6, power=14, target_kind=ONE_ALLY, kind="heal"`.
  - `"poison_dart"` — `mp_cost=4, power=2, target_kind=ONE_ENEMY, kind="physical", status_template=StatusEffect("Poison", duration=3, hp_per_turn=-4)`.
  - `"warcry"` — `mp_cost=3, power=0, target_kind=SELF, kind="guard", status_template=StatusEffect("Braced", duration=2, def_mod=4, atk_mod=2)`.
  - `"guard"` — `mp_cost=0, power=0, target_kind=SELF, kind="guard", status_template=StatusEffect("Guarding", duration=1, def_mod=6)`.
- `battle_core/battle.py` `_apply_skill`: for `kind == "guard"`, apply only the `status_template` to the actor (no damage/heal). Fold this into the existing `SELF` handling — a `guard` skill has `target_kind=SELF`, so `victims == [actor]`, and the existing `if skill.status_template is not None` block already applies it. Confirm no damage path runs for `kind == "guard"` (add `elif skill.kind == "guard": pass` for clarity).

- [ ] **Step 1: Write the failing tests (append to `tests/test_skills.py`)**

```python
from battle_core import BattleState, Character, StatusEffect, Action


def _c(name, side, slot, **kw):
    d = dict(name=name, side=side, slot=slot, max_hp=40, max_mp=30,
             base_atk=10, base_def=5, spd=5)
    d.update(kw)
    return Character(**d)


def test_fireball_costs_mp_and_deals_flat_magic_damage():
    caster = _c("Mage", "player", 0, spd=9)
    foe = _c("Orc", "enemy", 0, spd=1, base_def=99)  # armour should not matter
    bs = BattleState(players=[caster], enemies=[foe])
    before_mp = caster.mp
    bs.step(Action(actor=caster, skill=SKILLS["fireball"], target=foe))
    assert caster.mp == before_mp - 6
    assert foe.hp == foe.max_hp - 12


def test_firestorm_hits_every_enemy():
    caster = _c("Mage", "player", 0, spd=9)
    e0 = _c("E0", "enemy", 0, spd=1)
    e1 = _c("E1", "enemy", 1, spd=1)
    bs = BattleState(players=[caster], enemies=[e0, e1])
    bs.step(Action(actor=caster, skill=SKILLS["firestorm"], target=None))
    assert e0.hp < e0.max_hp and e1.hp < e1.max_hp


def test_heal_restores_an_ally_not_past_max():
    medic = _c("Medic", "player", 0, spd=9)
    hurt = _c("Tank", "player", 1, spd=1)
    hurt.take_damage(10)
    bs = BattleState(players=[medic, hurt], enemies=[_c("E", "enemy", 0, spd=0)])
    bs.step(Action(actor=medic, skill=SKILLS["heal"], target=hurt))
    assert hurt.hp == hurt.max_hp  # 30 + 14 capped at 40


def test_poison_dart_applies_poison_status():
    rogue = _c("Rogue", "player", 0, spd=9)
    foe = _c("E", "enemy", 0, spd=1)
    bs = BattleState(players=[rogue], enemies=[foe])
    bs.step(Action(actor=rogue, skill=SKILLS["poison_dart"], target=foe))
    assert any(s.name == "Poison" for s in foe.statuses)


def test_warcry_buffs_the_caster():
    fighter = _c("Fighter", "player", 0, spd=9)
    bs = BattleState(players=[fighter], enemies=[_c("E", "enemy", 0, spd=0)])
    before = fighter.defense
    bs.step(Action(actor=fighter, skill=SKILLS["warcry"], target=None))
    assert fighter.defense == before + 4
```

- [ ] **Step 2: Run, expect FAIL**

Run: `uv run pytest tests/test_skills.py -v`
Expected: FAIL — `KeyError: 'fireball'` etc.

- [ ] **Step 3: Add the skills to `battle_core/skills.py`**

```python
SKILLS: dict[str, Skill] = {
    "attack": Skill("attack", "Attack", mp_cost=0, power=6,
                    target_kind=TargetKind.ONE_ENEMY, kind="physical"),
    "fireball": Skill("fireball", "Fireball", mp_cost=6, power=12,
                      target_kind=TargetKind.ONE_ENEMY, kind="magic"),
    "firestorm": Skill("firestorm", "Firestorm", mp_cost=14, power=9,
                       target_kind=TargetKind.ALL_ENEMIES, kind="magic"),
    "heal": Skill("heal", "Heal", mp_cost=6, power=14,
                  target_kind=TargetKind.ONE_ALLY, kind="heal"),
    "poison_dart": Skill("poison_dart", "Poison Dart", mp_cost=4, power=2,
                         target_kind=TargetKind.ONE_ENEMY, kind="physical",
                         status_template=StatusEffect("Poison", duration=3, hp_per_turn=-4)),
    "warcry": Skill("warcry", "War Cry", mp_cost=3, power=0,
                    target_kind=TargetKind.SELF, kind="guard",
                    status_template=StatusEffect("Braced", duration=2, def_mod=4, atk_mod=2)),
    "guard": Skill("guard", "Guard", mp_cost=0, power=0,
                   target_kind=TargetKind.SELF, kind="guard",
                   status_template=StatusEffect("Guarding", duration=1, def_mod=6)),
}
```

- [ ] **Step 4: Handle `"guard"` kind explicitly in `_apply_skill`**

In `battle_core/battle.py` `_apply_skill`, inside the `for v in victims:` loop, add before the `status_template` block:
```python
            elif skill.kind == "guard":
                pass  # effect is entirely the status_template applied below
```

- [ ] **Step 5: Run, expect PASS**

Run: `uv run pytest -v`
Expected: all PASS.

- [ ] **Step 6: Give each default party member a skill list**

The `Character` dataclass currently has no notion of *which* skills a character knows — `legal_actions` offers all of `SKILLS`. Add a field:
```python
    skills: list[str] = field(default_factory=lambda: ["attack"])
```
to `Character` (after `statuses`). Then in `BattleState.legal_actions`, iterate `actor.skills` instead of `SKILLS.values()`:
```python
    def legal_actions(self, actor: Character) -> list[Action]:
        out: list[Action] = []
        for skill_id in actor.skills:
            skill = SKILLS[skill_id]
            if actor.mp < skill.mp_cost:
                continue
            for target in self._valid_targets(actor, skill.target_kind):
                out.append(Action(actor=actor, skill=skill, target=target))
        return out
```
Update `content.py` to give each character a real kit, e.g. Aria `["attack", "fireball", "heal", "guard"]`, Bran `["attack", "warcry", "guard"]`, Goblin `["attack", "poison_dart"]`, Acolyte `["attack", "fireball", "heal"]`, Brute `["attack", "firestorm", "warcry"]`. Update `tests/test_battle.py` helpers that build bare `Character`s only if they now fail (they default to `["attack"]`, so they should be fine).

- [ ] **Step 7: Run the full suite + lint**

Run: `uv run pytest -v && uv run ruff check .`
Expected: all green.

- [ ] **Step 8: Update `design.md`**

Fill the skills table: id, name, MP, power, target, kind, effect. Update the party table with each character's skill list.

- [ ] **Step 9: Write `lessons/02-skills-and-magic.md`** (~600–900 words)

- Data-driven design revisited: six new skills, zero new branches in `step()` — only `_apply_skill` grew by one `elif` per *kind*, not per *skill*.
- The four `kind`s (`physical`, `magic`, `heal`, `guard`) and the four `TargetKind`s, and how they compose.
- Status effects as the game's stateful core: poison (damage over time), War Cry (timed buff), Guard (one-turn wall). Why they tick at turn start.
- `Character.skills`: characters know a subset of all skills; `legal_actions` reads it. This list becomes part of the RL observation in Part C.
- Balancing notes: flat magic vs scaling physical, MP as the limiter on burst, why the Acolyte has a big MP pool and the Brute almost none.
- Checkpoint: "Every skill has a test; a full auto-battle with mixed kits terminates."

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "feat(part-a): spells, buffs, poison, and per-character skill kits (Lesson 02)"
```

---

## Task 8: Scripted combat AI (Lesson 03, part 1)

**Files:**
- Create: `battle_core/heuristics.py`
- Create: `tests/test_heuristics.py`
- Modify: `battle_core/__init__.py` (re-export `scripted_enemy_action`, `scripted_player_action`)

**Interfaces:**
- Consumes: `BattleState`, `Action`, `SKILLS`, `TargetKind`.
- Produces:
  - `scripted_enemy_action(bs: BattleState, actor: Character) -> Action` — a rule-based policy: (1) if `actor` knows `"heal"`, can afford it, and any living ally is below 40% HP → heal the lowest ally; (2) else if a damaging skill can bring a foe to ≤ 0 this turn → take the kill (prefer lowest MP cost); (3) else if `actor` knows a magic AoE and there are ≥ 2 living foes and MP allows → use it; (4) else attack the foe with the lowest current HP with the best affordable single-target damage skill; (5) fallback → `SKILLS["attack"]` on the lowest-HP foe. Always returns a member of `bs.legal_actions(actor)`.
  - `scripted_player_action(bs: BattleState, actor: Character) -> Action` — same logic, mirror-imaged (used later as the RL training opponent and as an "auto" button in the demo).
  - Both are deterministic given the state (ties broken by slot).

- [ ] **Step 1: Write the failing tests**

`tests/test_heuristics.py`:
```python
from battle_core import BattleState, Character, SKILLS
from battle_core.heuristics import scripted_enemy_action


def _c(name, side, slot, **kw):
    d = dict(name=name, side=side, slot=slot, max_hp=40, max_mp=30,
             base_atk=10, base_def=5, spd=5, skills=["attack"])
    d.update(kw)
    return Character(**d)


def test_enemy_returns_a_legal_action():
    e = _c("E", "enemy", 0, skills=["attack", "fireball", "heal"])
    p = _c("P", "player", 0)
    bs = BattleState(players=[p], enemies=[e])
    action = scripted_enemy_action(bs, e)
    assert action in bs.legal_actions(e)


def test_enemy_heals_a_badly_hurt_ally():
    medic = _c("Medic", "enemy", 0, skills=["attack", "heal"])
    ally = _c("Ally", "enemy", 1, skills=["attack"])
    ally.take_damage(int(ally.max_hp * 0.8))
    bs = BattleState(players=[_c("P", "player", 0)], enemies=[medic, ally])
    action = scripted_enemy_action(bs, medic)
    assert action.skill.id == "heal" and action.target is ally


def test_enemy_takes_a_lethal_hit_when_available():
    bruiser = _c("Bruiser", "enemy", 0, base_atk=50, skills=["attack"])
    frail = _c("Frail", "player", 0, base_def=1, max_hp=3)
    frail.hp = 3
    bs = BattleState(players=[frail], enemies=[bruiser])
    action = scripted_enemy_action(bs, bruiser)
    assert action.target is frail  # goes for the kill


def test_enemy_prefers_lowest_hp_target():
    e = _c("E", "enemy", 0, skills=["attack"])
    healthy = _c("Healthy", "player", 0)
    wounded = _c("Wounded", "player", 1)
    wounded.take_damage(20)
    bs = BattleState(players=[healthy, wounded], enemies=[e])
    action = scripted_enemy_action(bs, e)
    assert action.target is wounded
```

- [ ] **Step 2: Run, expect FAIL**

Run: `uv run pytest tests/test_heuristics.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Implement `battle_core/heuristics.py`**

```python
"""Rule-based combat policies: the enemy AI for the playable demo, and the RL training opponent."""
from __future__ import annotations

from battle_core.battle import Action, BattleState
from battle_core.entities import Character
from battle_core.skills import SKILLS, TargetKind, magic_damage, physical_damage


def _expected_damage(actor: Character, target: Character, skill_id: str) -> int:
    skill = SKILLS[skill_id]
    if skill.kind == "physical":
        return physical_damage(actor, target, skill.power)
    if skill.kind == "magic":
        return magic_damage(skill.power)
    return 0


def _choose(bs: BattleState, actor: Character) -> Action:
    legal = bs.legal_actions(actor)
    foes = bs.enemies_of(actor)
    allies = bs.allies_of(actor)

    # 1. Emergency heal.
    if "heal" in actor.skills and actor.mp >= SKILLS["heal"].mp_cost:
        hurt = [a for a in allies if a.hp < 0.4 * a.max_hp]
        if hurt:
            worst = min(hurt, key=lambda a: (a.hp, a.slot))
            for act in legal:
                if act.skill.id == "heal" and act.target is worst:
                    return act

    # 2. Lethal single-target hit.
    lethal: list[Action] = []
    for act in legal:
        if act.target is not None and act.skill.kind in ("physical", "magic"):
            if _expected_damage(actor, act.target, act.skill.id) >= act.target.hp:
                lethal.append(act)
    if lethal:
        return min(lethal, key=lambda a: (a.skill.mp_cost, a.target.slot))

    # 3. AoE when it hits two or more.
    if len(foes) >= 2:
        for act in legal:
            if act.skill.target_kind is TargetKind.ALL_ENEMIES:
                return act

    # 4. Best affordable single-target damage on the lowest-HP foe.
    if foes:
        weakest = min(foes, key=lambda f: (f.hp, f.slot))
        dmg_actions = [
            a for a in legal
            if a.target is weakest and a.skill.kind in ("physical", "magic")
        ]
        if dmg_actions:
            return max(dmg_actions, key=lambda a: _expected_damage(actor, weakest, a.skill.id))

    # 5. Fallback.
    return min(legal, key=lambda a: (a.skill.mp_cost, a.skill.id))


def scripted_enemy_action(bs: BattleState, actor: Character) -> Action:
    return _choose(bs, actor)


def scripted_player_action(bs: BattleState, actor: Character) -> Action:
    return _choose(bs, actor)
```

- [ ] **Step 4: Re-export and run**

Add to `battle_core/__init__.py`:
```python
from battle_core.heuristics import scripted_enemy_action, scripted_player_action
```
and append both names to `__all__`.

Run: `uv run pytest -v && uv run ruff check .`
Expected: all green.

- [ ] **Step 5: Write `lessons/03-playable-battle.md` — section 1 only (the AI)**

Start the lesson file. First section (~300 words): why a scripted baseline matters — it's the opponent the RL agent trains against in Part C and the yardstick `evaluate.py` measures against. Walk the five rules. Note its blind spots (no lookahead, ignores status effects, never uses War Cry) — deliberate, so a learned policy has room to beat it.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat(part-a): scripted combat AI for demo and RL baseline (Lesson 03)"
```

---

## Task 9: Battle renderer — layout, bars, message log (Lesson 03, part 2)

**Files:**
- Create: `game/scene.py`, `game/ui.py`
- Create: `game/scenes/__init__.py`, `game/scenes/battle.py`
- Modify: `game/app.py` (scene stack, launch `BattleScene`)

**Interfaces:**
- Consumes: `BattleState`, event classes, `content.make_default_*` from `battle_core`.
- Produces:
  - `game/scene.py`: `class Scene(abc.ABC)` with `handle_event(self, event: pygame.event.Event) -> None`, `update(self, dt: float) -> None`, `draw(self, surface: pygame.Surface) -> None`, and `next_scene: Scene | None = None` plus `done: bool = False` for transitions.
  - `game/ui.py`: `draw_text(surface, text, pos, *, size=20, color=(230,230,230), font_cache={})`, `draw_bar(surface, rect, frac, *, fg, bg=(50,50,55))`, `draw_panel(surface, rect, *, color=(18,18,22), border=(90,90,100))`.
  - `game/app.py`: `class Game` holds `self.scenes: list[Scene]` (a stack), runs the loop, and on `scene.done` pops it (or swaps to `scene.next_scene`). `main()` pushes a `BattleScene` for now.
  - `game/scenes/battle.py`: `class BattleScene(Scene)` — `__init__(self, battle: BattleState)`. Draws player party bottom-left, enemy party top-right, each as a panel with name + HP bar + MP bar + status icons (text tags for now). Bottom strip: a scrolling message log (last ~5 lines) built from `format_event(event) -> str`. This task does **rendering + a passive "watch two scripted parties fight" mode**; input comes in Task 10.
  - `format_event(event) -> str` in `game/scenes/battle.py`: `Damage` → `"Goblin hits Aria for 7"`, `Heal` → `"Aria heals Bran for 12"`, `StatusApplied` → `"Orc is now Poisoned"`, `StatusTick` → `"Aria takes 4 from Poison"`, `Faint` → `"Goblin faints!"`.

- [ ] **Step 1: Write the headless logic test**

`tests/test_battle_scene.py`:
```python
import pygame

from battle_core import BattleState
from battle_core.content import make_default_enemy_party, make_default_player_party
from battle_core.heuristics import scripted_enemy_action, scripted_player_action
from game.scenes.battle import BattleScene, format_event


def test_format_event_covers_all_event_types():
    from battle_core import Character, Damage, Heal, StatusApplied, StatusTick, Faint
    a = Character(name="Aria", side="player", slot=0, max_hp=10, max_mp=0,
                  base_atk=1, base_def=1, spd=1)
    b = Character(name="Orc", side="enemy", slot=0, max_hp=10, max_mp=0,
                  base_atk=1, base_def=1, spd=1)
    assert "Aria" in format_event(Damage(target=a, amount=7, source=b, skill_id="attack"))
    assert "12" in format_event(Heal(target=a, amount=12, source=a))
    assert "Poison" in format_event(StatusApplied(target=b, status_name="Poison"))
    assert format_event(StatusTick(target=a, amount=4, status_name="Poison"))
    assert "faint" in format_event(Faint(target=b)).lower()


def test_battle_scene_runs_a_full_auto_battle_without_error():
    pygame.init()
    surface = pygame.Surface((800, 600))
    bs = BattleState(players=make_default_player_party(), enemies=make_default_enemy_party())
    scene = BattleScene(bs, auto=True)
    guard = 0
    while not scene.done and guard < 2000:
        scene.update(1 / 60)
        scene.draw(surface)
        guard += 1
    assert bs.is_over()
    pygame.quit()
```

- [ ] **Step 2: Run, expect FAIL**

Run: `uv run pytest tests/test_battle_scene.py -v`
Expected: FAIL — modules missing.

- [ ] **Step 3: Implement `game/scene.py`**

```python
"""Base class for game scenes and the transition contract."""
from __future__ import annotations

import abc

import pygame


class Scene(abc.ABC):
    def __init__(self) -> None:
        self.done: bool = False
        self.next_scene: "Scene | None" = None

    @abc.abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None: ...

    @abc.abstractmethod
    def update(self, dt: float) -> None: ...

    @abc.abstractmethod
    def draw(self, surface: pygame.Surface) -> None: ...
```

- [ ] **Step 4: Implement `game/ui.py`**

```python
"""Tiny immediate-mode draw helpers shared by scenes."""
from __future__ import annotations

import pygame

_FONTS: dict[int, pygame.font.Font] = {}


def _font(size: int) -> pygame.font.Font:
    if size not in _FONTS:
        _FONTS[size] = pygame.font.SysFont("menlo,consolas,monospace", size)
    return _FONTS[size]


def draw_text(surface, text, pos, *, size=20, color=(230, 230, 230)):
    surface.blit(_font(size).render(text, True, color), pos)


def draw_panel(surface, rect, *, color=(18, 18, 22), border=(90, 90, 100)):
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, border, rect, width=1)


def draw_bar(surface, rect, frac, *, fg, bg=(50, 50, 55)):
    frac = max(0.0, min(1.0, frac))
    pygame.draw.rect(surface, bg, rect)
    inner = pygame.Rect(rect.x, rect.y, int(rect.w * frac), rect.h)
    pygame.draw.rect(surface, fg, inner)
```

- [ ] **Step 5: Implement `game/scenes/battle.py`** (rendering + auto mode)

```python
"""Renders a BattleState. Input handling arrives in Lesson 03 part 3."""
from __future__ import annotations

import pygame

from battle_core import (
    BattleState, Damage, Faint, Heal, StatusApplied, StatusTick,
)
from battle_core.heuristics import scripted_enemy_action, scripted_player_action
from game.scene import Scene
from game.ui import draw_bar, draw_panel, draw_text

HP_FG = (200, 70, 70)
MP_FG = (70, 120, 210)
STEP_DELAY = 0.35  # seconds between auto turns / animation beats


def format_event(event) -> str:
    match event:
        case Damage(target=t, amount=a, source=s):
            return f"{s.name} hits {t.name} for {a}"
        case Heal(target=t, amount=a, source=s):
            return f"{s.name} heals {t.name} for {a}"
        case StatusApplied(target=t, status_name=n):
            return f"{t.name} is now {n}"
        case StatusTick(target=t, amount=a, status_name=n):
            return f"{t.name} takes {a} from {n}"
        case Faint(target=t):
            return f"{t.name} faints!"
    return ""


class BattleScene(Scene):
    def __init__(self, battle: BattleState, *, auto: bool = False) -> None:
        super().__init__()
        self.bs = battle
        self.auto = auto
        self.log: list[str] = []
        self._timer = 0.0

    # -- turn driving -------------------------------------------------------
    def _take_auto_turn(self) -> None:
        actor = self.bs.current_actor()
        policy = scripted_player_action if actor.side == "player" else scripted_enemy_action
        events = self.bs.step(policy(self.bs, actor))
        self._record(events)

    def _record(self, events) -> None:
        for ev in events:
            line = format_event(ev)
            if line:
                self.log.append(line)
        self.log = self.log[-6:]

    def _check_end(self) -> None:
        if self.bs.is_over():
            self.log.append(f"{self.bs.winner().title()} wins the battle.")
            self.done = True

    # -- Scene API --------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        return  # Task 10 fills this in

    def update(self, dt: float) -> None:
        if self.done:
            return
        self._timer += dt
        if self.auto and self._timer >= STEP_DELAY:
            self._timer = 0.0
            self._take_auto_turn()
            self._check_end()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((28, 28, 34))
        self._draw_party(surface, self.bs.players, origin=(30, 360))
        self._draw_party(surface, self.bs.enemies, origin=(470, 40))
        self._draw_log(surface)

    def _draw_party(self, surface, party, *, origin) -> None:
        x, y = origin
        for i, c in enumerate(party):
            rect = pygame.Rect(x, y + i * 84, 300, 74)
            draw_panel(surface, rect)
            name = c.name if c.alive else f"{c.name} (down)"
            draw_text(surface, name, (rect.x + 8, rect.y + 6), size=18)
            draw_bar(surface, pygame.Rect(rect.x + 8, rect.y + 30, 200, 10),
                     c.hp / c.max_hp, fg=HP_FG)
            draw_bar(surface, pygame.Rect(rect.x + 8, rect.y + 44, 200, 8),
                     c.mp / max(1, c.max_mp), fg=MP_FG)
            tags = " ".join(f"[{s.name}]" for s in c.statuses)
            if tags:
                draw_text(surface, tags, (rect.x + 8, rect.y + 56), size=12,
                          color=(180, 180, 120))

    def _draw_log(self, surface) -> None:
        panel = pygame.Rect(30, 520, 740, 60)
        draw_panel(surface, panel)
        for i, line in enumerate(self.log[-3:]):
            draw_text(surface, line, (panel.x + 8, panel.y + 6 + i * 18), size=14)
```

- [ ] **Step 6: Wire `game/app.py` to the scene stack**

```python
"""Entry point: window, clock, and the scene stack."""
from __future__ import annotations

import pygame

from battle_core import BattleState
from battle_core.content import make_default_enemy_party, make_default_player_party
from game.scene import Scene
from game.scenes.battle import BattleScene

WINDOW_SIZE = (800, 600)
FPS = 60


class Game:
    def __init__(self, root: Scene) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("AI RPG")
        self.clock = pygame.time.Clock()
        self.scenes: list[Scene] = [root]

    @property
    def scene(self) -> Scene:
        return self.scenes[-1]

    def run(self) -> None:
        running = True
        while running and self.scenes:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    self.scene.handle_event(event)
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()

            if self.scene.done:
                nxt = self.scene.next_scene
                self.scenes.pop()
                if nxt is not None:
                    self.scenes.append(nxt)

        pygame.quit()


def main() -> None:
    bs = BattleState(players=make_default_player_party(), enemies=make_default_enemy_party())
    Game(BattleScene(bs, auto=True)).run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: Run tests + manual check**

Run: `uv run pytest -v`
Expected: all PASS.

Run: `uv run python -m game.app`
Expected: watch two scripted parties fight; HP/MP bars drain; log scrolls; window closes cleanly when the battle ends or on `Esc`.

- [ ] **Step 8: Continue `lessons/03-playable-battle.md` — section 2**

Add (~400 words): the `Scene` ABC and the scene stack in `Game.run`; immediate-mode drawing (`ui.py` redraws everything every frame — no retained widgets); `format_event` turning the rules engine's events into log lines; why `auto` mode exists (a rendering smoke test you can watch, and it's reused as a demo attract-mode).

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat(part-a): battle renderer with auto-battle mode (Lesson 03)"
```

---

## Task 10: Battle input — action menu, targeting, player turns (completes Lesson 03)

**Files:**
- Modify: `game/scenes/battle.py` (input state machine)
- Create: `game/ui.py` `Menu` widget (append to the file)
- Modify: `tests/test_battle_scene.py` (add an input-driven test using synthetic events)

**Interfaces:**
- Consumes: `BattleScene` from Task 9, `bs.legal_actions`.
- Produces:
  - `game/ui.py`: `class Menu` — `__init__(self, items: list[str])`, `move(self, delta: int) -> None`, `current -> int`, `draw(self, surface, pos, *, size=18)`. Wraps around at the ends.
  - `BattleScene` gains an input state machine with phases: `"enemy_or_ally_auto"` (non-player actor → step via scripted policy on a timer), `"choose_skill"` (player actor → skill `Menu` from `set(a.skill for a in legal_actions)`), `"choose_target"` (target `Menu` over the valid targets for the chosen skill; skipped for `SELF`/`ALL_ENEMIES`), `"resolving"` (brief delay showing the log). Keys: `↑/↓` move, `Enter` confirm, `Backspace` cancel back to `choose_skill`, `A` toggles "auto" for the player party.
  - When the battle ends, `self.done = True` and `self.next_scene` stays `None` (Task 13 sets it to a `TownScene` when the battle was launched from town).

- [ ] **Step 1: Write the input test (append to `tests/test_battle_scene.py`)**

```python
def _key(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def test_player_can_drive_a_turn_via_keyboard():
    pygame.init()
    surface = pygame.Surface((800, 600))
    from battle_core import BattleState, Character
    p = Character(name="P", side="player", slot=0, max_hp=30, max_mp=10,
                  base_atk=30, base_def=5, spd=9, skills=["attack"])
    e = Character(name="E", side="enemy", slot=0, max_hp=6, max_mp=0,
                  base_atk=1, base_def=1, spd=1, skills=["attack"])
    bs = BattleState(players=[p], enemies=[e])
    scene = BattleScene(bs)

    scene.update(0.0)                 # enter choose_skill for P
    scene.handle_event(_key(pygame.K_RETURN))   # confirm "Attack"
    scene.handle_event(_key(pygame.K_RETURN))   # confirm target E
    for _ in range(20):
        scene.update(0.1)
        if scene.done:
            break
    assert bs.is_over() and bs.winner() == "player"
```

- [ ] **Step 2: Run, expect FAIL**

Run: `uv run pytest tests/test_battle_scene.py::test_player_can_drive_a_turn_via_keyboard -v`
Expected: FAIL (no input handling yet — battle never progresses, `scene.done` stays False).

- [ ] **Step 3: Add the `Menu` widget to `game/ui.py`**

```python
class Menu:
    def __init__(self, items: list[str]) -> None:
        self.items = items
        self._i = 0

    @property
    def current(self) -> int:
        return self._i

    def move(self, delta: int) -> None:
        if self.items:
            self._i = (self._i + delta) % len(self.items)

    def draw(self, surface, pos, *, size=18) -> None:
        x, y = pos
        for i, label in enumerate(self.items):
            prefix = "> " if i == self._i else "  "
            color = (255, 240, 180) if i == self._i else (200, 200, 200)
            draw_text(surface, prefix + label, (x, y + i * (size + 6)), size=size, color=color)
```

- [ ] **Step 4: Add the input state machine to `BattleScene`**

Replace `handle_event` / `update` and add helpers:
```python
    # in __init__, after self._timer = 0.0:
        self.phase = "resolving"
        self.player_auto = False
        self._skill_menu = None
        self._target_menu = None
        self._pending_skill = None

    def _legal(self):
        return self.bs.legal_actions(self.bs.current_actor())

    def _enter_choose_skill(self) -> None:
        skills = []
        seen = set()
        for a in self._legal():
            if a.skill.id not in seen:
                seen.add(a.skill.id)
                skills.append(a.skill)
        self._skill_options = skills
        self._skill_menu = Menu([s.name for s in skills])
        self.phase = "choose_skill"

    def _enter_choose_target(self) -> None:
        skill = self._pending_skill
        opts = [a.target for a in self._legal()
                if a.skill.id == skill.id]
        if opts == [None] or (opts and opts[0] is None):
            self._commit(skill, None)
            return
        self._target_options = opts
        self._target_menu = Menu([t.name for t in opts])
        self.phase = "choose_target"

    def _commit(self, skill, target) -> None:
        action = next(a for a in self._legal()
                      if a.skill.id == skill.id and a.target is target)
        self._record(self.bs.step(action))
        self._pending_skill = None
        self.phase = "resolving"
        self._timer = 0.0
        self._check_end()

    def handle_event(self, event) -> None:
        if self.done or event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_a:
            self.player_auto = not self.player_auto
            return
        if self.phase == "choose_skill" and self._skill_menu:
            if event.key == pygame.K_UP:
                self._skill_menu.move(-1)
            elif event.key == pygame.K_DOWN:
                self._skill_menu.move(1)
            elif event.key == pygame.K_RETURN:
                self._pending_skill = self._skill_options[self._skill_menu.current]
                self._enter_choose_target()
        elif self.phase == "choose_target" and self._target_menu:
            if event.key == pygame.K_UP:
                self._target_menu.move(-1)
            elif event.key == pygame.K_DOWN:
                self._target_menu.move(1)
            elif event.key == pygame.K_BACKSPACE:
                self._enter_choose_skill()
            elif event.key == pygame.K_RETURN:
                self._commit(self._pending_skill,
                             self._target_options[self._target_menu.current])

    def update(self, dt: float) -> None:
        if self.done:
            return
        self._timer += dt
        if self.phase == "resolving":
            if self._timer < STEP_DELAY:
                return
            self._timer = 0.0
            if self.bs.is_over():
                self._check_end()
                return
            actor = self.bs.current_actor()
            if actor.side == "enemy" or self.player_auto:
                policy = scripted_player_action if actor.side == "player" else scripted_enemy_action
                self._record(self.bs.step(policy(self.bs, actor)))
                self._check_end()
            else:
                self._enter_choose_skill()
        # choose_skill / choose_target: wait for input
```

Update `draw` to render the active menu near the log panel when `phase` is `choose_skill` or `choose_target`.

Remove the old `auto` constructor arg? No — keep it: `auto=True` sets `self.player_auto = True` and leaves enemies scripted, so `main()`'s attract-mode still works. Adjust `__init__` accordingly.

- [ ] **Step 5: Run tests + manual check**

Run: `uv run pytest -v`
Expected: all PASS.

Run: `uv run python -m game.app` — but first change `main()` to `BattleScene(bs)` (interactive, not `auto=True`).
Expected: on your characters' turns a skill menu appears; `↑/↓`, `Enter`, `Backspace` work; targeting works; enemies act on their own; the battle ends and the window closes.

- [ ] **Step 6: Finish `lessons/03-playable-battle.md` — section 3** (~500 words)

The input state machine: phases, why combat UIs are naturally state machines (skill → target → resolve), the `Menu` widget, `player_auto` for testing and accessibility, how `_commit` maps a (skill, target) pick back to the exact `Action` from `legal_actions` (the single source of truth — the UI never constructs an `Action` the rules engine wouldn't allow). Checkpoint: "You can play a full battle with the keyboard."

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat(part-a): keyboard-driven battle input (Lesson 03)"
```

---

## Task 11: Tile map and player movement (Lesson 04, part 1)

**Files:**
- Create: `game/tilemap.py`
- Create: `game/scenes/town.py` (movement only; NPCs in Task 12)
- Create: `tests/test_tilemap.py`, `tests/test_town_logic.py`
- Modify: `game/app.py` (`main()` starts in town)

**Interfaces:**
- Consumes: `game/scene.py`, `game/ui.py`.
- Produces:
  - `game/tilemap.py`:
    - `TILE = 32` (pixels).
    - `class TileMap` — `__init__(self, rows: list[str])` where each string is a row, `'#'` = wall, `'.'` = floor, `'D'` = the door/battle trigger tile. `width`/`height` in tiles.
    - `TileMap.is_walkable(self, tx: int, ty: int) -> bool` — False for out-of-bounds and walls.
    - `TileMap.tile_at(self, tx: int, ty: int) -> str`.
    - `TileMap.to_pixel(self, tx: int, ty: int) -> tuple[int, int]` and `to_tile(self, px: int, py: int) -> tuple[int, int]`.
    - `DEFAULT_TOWN: list[str]` — a ~16×12 room with walls around the edge, some interior obstacles, one `'D'` tile.
  - `game/scenes/town.py`:
    - `class TownScene(Scene)` — `__init__(self, tilemap: TileMap | None = None)`. Holds `self.player_tile: tuple[int,int]`, starts on a floor tile.
    - Grid movement: `↑/↓/←/→` (and WASD) move the player one tile if `is_walkable`; no diagonal; one move per key-press (not per-frame hold, for Part A simplicity).
    - `on_enter_tile(self, tile: str) -> None` — hook; for now, if `tile == 'D'`, set `self._wants_battle = True` (Task 13 turns this into a real transition).
    - `draw`: render tiles (wall = dark block, floor = grid dots, door = coloured block) and the player as a circle.

- [ ] **Step 1: Write the failing tests**

`tests/test_tilemap.py`:
```python
from game.tilemap import TILE, TileMap


def test_walls_and_bounds_block_movement():
    tm = TileMap(["###", "#.#", "###"])
    assert tm.is_walkable(1, 1)
    assert not tm.is_walkable(0, 0)
    assert not tm.is_walkable(-1, 1)
    assert not tm.is_walkable(1, 99)


def test_coordinate_round_trip():
    tm = TileMap(["...", "..."])
    assert tm.to_pixel(2, 1) == (2 * TILE, 1 * TILE)
    assert tm.to_tile(2 * TILE + 5, 1 * TILE + 5) == (2, 1)


def test_default_town_has_one_door():
    from game.tilemap import DEFAULT_TOWN
    tm = TileMap(DEFAULT_TOWN)
    doors = sum(row.count("D") for row in DEFAULT_TOWN)
    assert doors == 1
    assert tm.width >= 12 and tm.height >= 8
```

`tests/test_town_logic.py`:
```python
import pygame

from game.scenes.town import TownScene
from game.tilemap import TileMap


def _key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def test_player_moves_onto_floor_but_not_into_walls():
    tm = TileMap(["#####", "#...#", "#...#", "#####"])
    scene = TownScene(tm)
    scene.player_tile = (1, 1)
    scene.handle_event(_key(pygame.K_RIGHT))
    assert scene.player_tile == (2, 1)
    scene.handle_event(_key(pygame.K_UP))       # wall above
    assert scene.player_tile == (2, 1)


def test_stepping_on_door_sets_battle_flag():
    tm = TileMap(["#####", "#..D#", "#####"])
    scene = TownScene(tm)
    scene.player_tile = (1, 1)
    scene.handle_event(_key(pygame.K_RIGHT))
    scene.handle_event(_key(pygame.K_RIGHT))
    assert scene.player_tile == (3, 1)
    assert scene._wants_battle
```

- [ ] **Step 2: Run, expect FAIL**

Run: `uv run pytest tests/test_tilemap.py tests/test_town_logic.py -v`
Expected: FAIL — modules missing.

- [ ] **Step 3: Implement `game/tilemap.py`**

```python
"""A static grid of tiles: walls, floor, and a battle-trigger door."""
from __future__ import annotations

TILE = 32


class TileMap:
    def __init__(self, rows: list[str]) -> None:
        self.rows = rows
        self.height = len(rows)
        self.width = max(len(r) for r in rows)

    def tile_at(self, tx: int, ty: int) -> str:
        if 0 <= ty < self.height and 0 <= tx < len(self.rows[ty]):
            return self.rows[ty][tx]
        return "#"

    def is_walkable(self, tx: int, ty: int) -> bool:
        return self.tile_at(tx, ty) != "#"

    def to_pixel(self, tx: int, ty: int) -> tuple[int, int]:
        return tx * TILE, ty * TILE

    def to_tile(self, px: int, py: int) -> tuple[int, int]:
        return px // TILE, py // TILE


DEFAULT_TOWN = [
    "################",
    "#..............#",
    "#..##......##..#",
    "#..##......##..#",
    "#.............D#",
    "#..............#",
    "#....##..##....#",
    "#....##..##....#",
    "#..............#",
    "#..............#",
    "#..............#",
    "################",
]
```

- [ ] **Step 4: Implement `game/scenes/town.py`** (movement only)

```python
"""The walkable town. NPCs are added in Lesson 04 part 2."""
from __future__ import annotations

import pygame

from game.scene import Scene
from game.tilemap import TILE, TileMap, DEFAULT_TOWN
from game.ui import draw_text

_MOVES = {
    pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
    pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
    pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
    pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
}


class TownScene(Scene):
    def __init__(self, tilemap: TileMap | None = None) -> None:
        super().__init__()
        self.map = tilemap or TileMap(DEFAULT_TOWN)
        self.player_tile = self._first_floor()
        self._wants_battle = False

    def _first_floor(self) -> tuple[int, int]:
        for ty in range(self.map.height):
            for tx in range(len(self.map.rows[ty])):
                if self.map.tile_at(tx, ty) == ".":
                    return (tx, ty)
        return (1, 1)

    def on_enter_tile(self, tile: str) -> None:
        if tile == "D":
            self._wants_battle = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN or event.key not in _MOVES:
            return
        dx, dy = _MOVES[event.key]
        nx, ny = self.player_tile[0] + dx, self.player_tile[1] + dy
        if self.map.is_walkable(nx, ny):
            self.player_tile = (nx, ny)
            self.on_enter_tile(self.map.tile_at(nx, ny))

    def update(self, dt: float) -> None:
        return

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((20, 22, 20))
        for ty in range(self.map.height):
            for tx in range(len(self.map.rows[ty])):
                t = self.map.tile_at(tx, ty)
                px, py = self.map.to_pixel(tx, ty)
                if t == "#":
                    pygame.draw.rect(surface, (45, 45, 55), (px, py, TILE, TILE))
                elif t == "D":
                    pygame.draw.rect(surface, (150, 110, 40), (px, py, TILE, TILE))
                else:
                    pygame.draw.circle(surface, (40, 44, 40), (px + TILE // 2, py + TILE // 2), 2)
        ppx, ppy = self.map.to_pixel(*self.player_tile)
        pygame.draw.circle(surface, (120, 200, 255), (ppx + TILE // 2, ppy + TILE // 2), TILE // 2 - 4)
        draw_text(surface, "Arrow keys / WASD to move. Reach the door.", (10, surface.get_height() - 24), size=14)
```

- [ ] **Step 5: Point `main()` at the town**

In `game/app.py`, change `main()`:
```python
def main() -> None:
    from game.scenes.town import TownScene
    Game(TownScene()).run()
```

- [ ] **Step 6: Run tests + manual check**

Run: `uv run pytest -v`
Expected: all PASS.

Run: `uv run python -m game.app`
Expected: a room you can walk around with arrow keys/WASD; walls block; the door tile is visible. (Nothing happens on the door yet — Task 13.)

- [ ] **Step 7: Write `lessons/04-town.md` — section 1** (~400 words)

Tile maps as ASCII: readable, diffable, trivially testable. `TileMap` as pure data + queries, no pygame in its logic (only the scene draws). Grid movement vs free movement — grid keeps collision to a single `is_walkable` check. The `on_enter_tile` hook as the seam for triggers.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat(part-a): tile map and grid-based town movement (Lesson 04)"
```

---

## Task 12: NPCs and proximity interaction (Lesson 04, part 2)

**Files:**
- Modify: `game/scenes/town.py` (NPC entities, interaction)
- Create: `game/npc_stub.py` (placeholder dialogue — replaced wholesale in Part B)
- Modify: `tests/test_town_logic.py` (interaction tests)

**Interfaces:**
- Consumes: `TownScene` from Task 11.
- Produces:
  - `game/npc_stub.py`: `@dataclass class TownNPC: npc_id: str; name: str; tile: tuple[int, int]; lines: list[str]`. `def talk(self) -> str` — returns the next line, cycling. This module is a deliberate stand-in; Part B replaces it with `dialogue/npc.py`.
  - `TownScene.__init__` gains `npcs: list[TownNPC] | None = None`, defaulting to two placed on floor tiles of `DEFAULT_TOWN` (a guard near the door, a villager elsewhere), each with 2–3 canned lines. One line on the guard hints at the fight ("The road past the gate is crawling with goblins.").
  - `TownScene.adjacent_npc() -> TownNPC | None` — the NPC orthogonally adjacent to (or on) the player tile, if any.
  - Pressing `E`/`Space` when `adjacent_npc()` is not None sets `self.active_dialogue: str | None` to `npc.talk()`; pressing it again (or any move key) clears it.
  - `draw`: NPCs as coloured squares with a name label; when `active_dialogue` is set, a text box across the bottom.

- [ ] **Step 1: Write the failing tests (append to `tests/test_town_logic.py`)**

```python
def test_talk_to_adjacent_npc_opens_dialogue():
    tm = TileMap(["#####", "#...#", "#...#", "#####"])
    from game.npc_stub import TownNPC
    npc = TownNPC(npc_id="guard", name="Guard", tile=(2, 1), lines=["Halt.", "Move along."])
    scene = TownScene(tm, npcs=[npc])
    scene.player_tile = (1, 1)
    assert scene.adjacent_npc() is npc
    scene.handle_event(_key(pygame.K_e))
    assert scene.active_dialogue == "Halt."
    scene.handle_event(_key(pygame.K_e))       # advance / close
    assert scene.active_dialogue in (None, "Move along.")


def test_cannot_talk_when_not_adjacent():
    tm = TileMap(["######", "#....#", "#....#", "######"])
    from game.npc_stub import TownNPC
    npc = TownNPC(npc_id="v", name="Villager", tile=(4, 2), lines=["Hi"])
    scene = TownScene(tm, npcs=[npc])
    scene.player_tile = (1, 1)
    assert scene.adjacent_npc() is None
    scene.handle_event(_key(pygame.K_e))
    assert scene.active_dialogue is None


def test_npc_tile_blocks_movement():
    tm = TileMap(["#####", "#...#", "#####"])
    from game.npc_stub import TownNPC
    npc = TownNPC(npc_id="v", name="V", tile=(2, 1), lines=["Hi"])
    scene = TownScene(tm, npcs=[npc])
    scene.player_tile = (1, 1)
    scene.handle_event(_key(pygame.K_RIGHT))    # into the NPC
    assert scene.player_tile == (1, 1)
```

- [ ] **Step 2: Run, expect FAIL**

Run: `uv run pytest tests/test_town_logic.py -v`
Expected: FAIL — `npc_stub` missing, `adjacent_npc` missing.

- [ ] **Step 3: Implement `game/npc_stub.py`**

```python
"""Placeholder town NPCs with canned lines. Replaced by dialogue/npc.py in Part B."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TownNPC:
    npc_id: str
    name: str
    tile: tuple[int, int]
    lines: list[str]
    _next: int = field(default=0, repr=False)

    def talk(self) -> str:
        line = self.lines[self._next % len(self.lines)]
        self._next += 1
        return line
```

- [ ] **Step 4: Extend `TownScene`**

- Add `npcs` param; default:
```python
        self.npcs = npcs if npcs is not None else [
            TownNPC("guard", "Guard", (13, 5),
                    ["The road past the gate is crawling with goblins.",
                     "Don't say I didn't warn you."]),
            TownNPC("villager", "Mara", (3, 9),
                    ["Lovely weather, isn't it?",
                     "The blacksmith's away till next week."]),
        ]
        self.active_dialogue: str | None = None
```
- In `handle_event`: on a move key, clear `self.active_dialogue` first; block the move if the target tile holds an NPC (`any(n.tile == (nx, ny) for n in self.npcs)`).
- Add:
```python
    def adjacent_npc(self):
        px, py = self.player_tile
        for n in self.npcs:
            if abs(n.tile[0] - px) + abs(n.tile[1] - py) <= 1:
                return n
        return None

    def _interact(self):
        npc = self.adjacent_npc()
        if npc is None:
            return
        if self.active_dialogue is None:
            self.active_dialogue = npc.talk()
        else:
            self.active_dialogue = None
```
- In `handle_event`, handle `pygame.K_e` and `pygame.K_SPACE` → `self._interact()`.
- In `draw`: draw each NPC as a square + name; if `active_dialogue`, draw a bottom text box with the line and the NPC name.

- [ ] **Step 5: Run tests + manual check**

Run: `uv run pytest -v`
Expected: all PASS.

Run: `uv run python -m game.app`
Expected: two NPCs in the room; walk up to one, press `E`, see a line; press again to close; you can't walk through them.

- [ ] **Step 6: Continue `lessons/04-town.md` — section 2** (~350 words)

Entities as plain dataclasses; proximity via Manhattan distance ≤ 1; the "press E advances or closes" micro-state-machine; why `npc_stub.py` is explicitly a stub (Part B swaps in real LLM-backed dialogue and the seam is `talk() -> str`).

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat(part-a): town NPCs with proximity dialogue (Lesson 04)"
```

---

## Task 13: Scene transitions — town ⇄ battle (completes Lesson 04 and Part A)

**Files:**
- Modify: `game/scenes/town.py` (`update` triggers the transition)
- Modify: `game/scenes/battle.py` (`__init__` takes an optional `return_to` scene; on battle end, set `next_scene`)
- Modify: `game/app.py` (`main()` starts in town; the door launches a battle; winning returns to town, losing quits to a game-over)
- Create: `game/scenes/gameover.py`
- Modify: `tests/` — `tests/test_transitions.py`

**Interfaces:**
- Consumes: `TownScene`, `BattleScene`, `Game`.
- Produces:
  - `TownScene.update(dt)` — when `self._wants_battle`, set `self.done = True` and `self.next_scene = BattleScene(fresh_battle, return_to=self)` (reuse the same town instance so the player's position persists), then reset `self._wants_battle = False`.
  - `BattleScene.__init__(self, battle, *, auto=False, return_to: Scene | None = None)`.
  - `BattleScene._check_end`: on player win → `self.next_scene = self.return_to`; on player loss → `self.next_scene = GameOverScene()`. `self.done = True` either way. If `return_to` is None (ran from `main` directly), leave `next_scene` None.
  - After a won battle, move the player off the `'D'` tile (e.g. one tile back the way they came, or to the nearest floor tile) so they don't instantly re-trigger.
  - `game/scenes/gameover.py`: `class GameOverScene(Scene)` — shows "Defeated. Press Enter." and on Enter sets `done = True`, `next_scene = None` (the `Game` loop then exits because the stack empties).

- [ ] **Step 1: Write the transition test**

`tests/test_transitions.py`:
```python
import pygame

from game.scenes.town import TownScene
from game.scenes.battle import BattleScene
from game.tilemap import TileMap


def _key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def test_reaching_the_door_produces_a_battle_scene():
    pygame.init()
    tm = TileMap(["#####", "#..D#", "#####"])
    town = TownScene(tm)
    town.player_tile = (1, 1)
    town.handle_event(_key(pygame.K_RIGHT))
    town.handle_event(_key(pygame.K_RIGHT))   # onto D
    town.update(0.0)
    assert town.done
    assert isinstance(town.next_scene, BattleScene)
    assert town.next_scene.return_to is town


def test_won_battle_returns_to_town_and_clears_trigger():
    pygame.init()
    from battle_core import BattleState, Character
    town = TownScene(TileMap(["#####", "#..D#", "#####"]))
    town.player_tile = (3, 1)
    p = Character(name="P", side="player", slot=0, max_hp=30, max_mp=0,
                  base_atk=99, base_def=9, spd=9, skills=["attack"])
    e = Character(name="E", side="enemy", slot=0, max_hp=1, max_mp=0,
                  base_atk=1, base_def=1, spd=1, skills=["attack"])
    battle = BattleScene(BattleState(players=[p], enemies=[e]), return_to=town)
    battle.player_auto = True
    for _ in range(50):
        battle.update(0.1)
        if battle.done:
            break
    assert battle.done
    assert battle.next_scene is town
    assert town.player_tile != (3, 1) or not town._wants_battle
```

- [ ] **Step 2: Run, expect FAIL**

Run: `uv run pytest tests/test_transitions.py -v`
Expected: FAIL — `return_to` kwarg unknown, no transition logic.

- [ ] **Step 3: Implement `GameOverScene`**

```python
"""Shown when the player's party is wiped out."""
from __future__ import annotations

import pygame

from game.scene import Scene
from game.ui import draw_text


class GameOverScene(Scene):
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.done = True
            self.next_scene = None

    def update(self, dt: float) -> None:
        return

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((10, 10, 12))
        draw_text(surface, "Defeated. Press Enter.", (260, 280), size=28,
                  color=(220, 120, 120))
```

- [ ] **Step 4: Wire transitions in `TownScene` and `BattleScene`**

`TownScene`:
```python
    def update(self, dt: float) -> None:
        if self._wants_battle and not self.done:
            from battle_core import BattleState
            from battle_core.content import make_default_enemy_party, make_default_player_party
            from game.scenes.battle import BattleScene
            self._wants_battle = False
            battle = BattleState(players=make_default_player_party(),
                                 enemies=make_default_enemy_party())
            self.done = True
            self.next_scene = BattleScene(battle, return_to=self)

    def resume_from_battle(self) -> None:
        """Called by Game when control returns here after a win."""
        self.done = False
        self.next_scene = None
        # nudge the player off the door so they don't re-trigger instantly
        px, py = self.player_tile
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if self.map.is_walkable(px + dx, py + dy) and self.map.tile_at(px + dx, py + dy) != "D":
                self.player_tile = (px + dx, py + dy)
                break
```

`BattleScene`:
```python
    def __init__(self, battle, *, auto=False, return_to=None):
        super().__init__()
        ...
        self.return_to = return_to
        self.player_auto = auto

    def _check_end(self) -> None:
        if not self.bs.is_over():
            return
        self.log.append(f"{self.bs.winner().title()} wins the battle.")
        self.done = True
        if self.bs.winner() == "player":
            self.next_scene = self.return_to
        else:
            from game.scenes.gameover import GameOverScene
            self.next_scene = GameOverScene()
```

`Game.run` — when popping a finished scene, if the next scene is a `TownScene` we're returning to, call its resume hook:
```python
            if self.scene.done:
                nxt = self.scene.next_scene
                self.scenes.pop()
                if nxt is not None:
                    from game.scenes.town import TownScene
                    if isinstance(nxt, TownScene):
                        nxt.resume_from_battle()
                    self.scenes.append(nxt)
```

- [ ] **Step 5: Update `main()`**

```python
def main() -> None:
    from game.scenes.town import TownScene
    Game(TownScene()).run()
```

- [ ] **Step 6: Run the full suite + lint**

Run: `uv run pytest -v && uv run ruff check .`
Expected: all green.

- [ ] **Step 7: Full manual playthrough**

Run: `uv run python -m game.app`
Expected: start in town → talk to the guard → walk to the door → battle starts → play it (or press `A` for auto) → on a win, back in town, standing next to the door, not re-triggering → walk back onto the door → battle again → lose on purpose (let enemies win) → game-over screen → Enter quits.

- [ ] **Step 8: Finish `lessons/04-town.md` — section 3** (~450 words)

Scene transitions via `done` + `next_scene`; why the town instance is *reused* (player position is state that must survive the battle); the `resume_from_battle` nudge; the full scene graph (Town → Battle → Town | GameOver); where Part B (LLM dialogue) and Part C (RL enemies) plug in — `npc_stub.talk()` and `scripted_enemy_action` are the two seams. End with a recap of everything Part A built and a pointer to the Part B plan.

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat(part-a): town/battle/game-over scene transitions (Lesson 04, Part A complete)"
```

---

## Self-Review

**1. Spec coverage (Part A scope only):**

| Spec item | Task |
|---|---|
| `battle_core` pure-Python, purity enforced | Task 1 (test), Tasks 2–8 |
| `entities.py` — Character, StatusEffect, derived stats | Task 2 |
| `skills.py` — Skill, TargetKind, registry, math | Tasks 3, 7 |
| `battle.py` — BattleState, turn order, step, legal_actions, is_over, winner, events | Tasks 4, 5 |
| MP costs, status effects (poison, buff, debuff, guard) | Tasks 5, 6, 7 |
| Targeting rules (one enemy / one ally / self / all enemies) | Tasks 5, 7 |
| `heuristics.py` — scripted player + enemy | Task 8 |
| `content.py` — default parties | Tasks 5, 7 |
| Lesson 00–04 markdown + runnable checkpoints | every task's final steps |
| `scenes/battle.py` — HP/MP bars, action menu, target picker, message log | Tasks 9, 10 |
| `scenes/town.py` — tilemap, movement, collision, NPCs, "press E", battle trigger | Tasks 11, 12, 13 |
| Scene transition to battle and back | Task 13 |
| `uv`, `pyproject.toml` only, `pygame-ce`, pytest config | Task 1 |
| Tests: `battle_core` hard, rendering = smoke + headless logic | Tasks 2–8 vs 9–13 |

Deferred to later parts by design: `rl/`, `dialogue/` (Part B replaces `npc_stub.py`), `policy_runtime.py`, packaging.

**2. Placeholder scan:** No "TBD"/"TODO" in task steps. Lesson-doc steps give concrete section outlines with the actual teaching points rather than full prose — the prose is the deliverable of that step, and the outline is specific enough to write from. The one "refine to the snapshot approach" note in Task 5 includes the full replacement code.

**3. Type consistency:**
- `Character` fields and `Character.skills` (added in Task 7) — `legal_actions` updated in the same task.
- `BattleState.step` returns `list[Event]` everywhere (Task 4 defines, Task 5 implements, Tasks 6–13 consume).
- `Action(actor, skill, target)` — consistent across Tasks 4, 5, 8, 10.
- `Scene.done` / `Scene.next_scene` — defined Task 9, used Tasks 10–13.
- `BattleScene.__init__` gains `return_to` in Task 13; earlier tasks call `BattleScene(bs)` / `BattleScene(bs, auto=True)` which stay valid (new kwarg is optional).
- `scripted_enemy_action(bs, actor)` / `scripted_player_action(bs, actor)` — signature stable from Task 8.
- `TownNPC.talk() -> str` — the seam Part B preserves.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-06-ai-rpg-part-a-game-foundation.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — I execute tasks in this session using executing-plans, batching with checkpoints for your review.

Which approach?
