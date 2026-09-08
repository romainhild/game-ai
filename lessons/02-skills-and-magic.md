# Lesson 02 — Skills, magic, and status effects

## Why this lesson exists

After Lesson 01 the only move anyone can make is "Attack". There's nothing to
*decide*. Reinforcement learning is the art of learning a good policy over
choices — so before Part C there have to be choices worth learning:

- spend MP now on a Fireball, or save it for a Heal later?
- the Brute is on 8 HP — finish it, or AoE the whole back line?
- I'm about to get focused — Guard, or race them?

This lesson adds six skills and a per-character skill list. The remarkable part
is how little the *engine* changes: the turn loop, `step()`, and `_apply_skill`
barely move. That's the payoff of the data-driven `Skill` design from Lesson 01.

Two stages, each ending in a commit:

| Stage | Files | What |
|---|---|---|
| 1 | `entities.py`, `battle.py` | `Character.skills` — characters know a *subset* of all skills |
| 2 | `skills.py`, `content.py` | the six skills; give each party member a kit |

---

## Stage 1 — Characters know a subset of skills

### The idea

Right now `legal_actions` offers *every* skill in `SKILLS` to *every* character.
Once there's a Fireball, that's wrong — the Brute shouldn't cast spells. A
character needs a **skill list**: the ids it's allowed to use.

```python
skills: list[str] = field(default_factory=lambda: ["attack"])
```

Default `["attack"]` so every existing test that builds a bare `Character` keeps
working unchanged. `legal_actions` then iterates `actor.skills` instead of
`SKILLS.values()`.

Why store **ids** (`"fireball"`) and not `Skill` objects? Two reasons. `Skill`
is frozen data that lives in one place (`SKILLS`); duplicating the objects onto
every character invites drift. And in Part C the skill list becomes part of the
RL observation — a list of small integers (skill indices) encodes far more
cleanly than a list of dataclasses.

### The tests

Add to `tests/test_status_effects.py` (new file):

```python
from battle_core import SKILLS, Action, BattleState, Character, StatusEffect
from battle_core.skills import physical_damage

BASE = {"name": "C", "side": "player", "slot": 0, "max_hp": 40, "max_mp": 30,
        "base_atk": 10, "base_def": 5, "spd": 5}


def mk(**kw) -> Character:
    return Character(**{**BASE, **kw})


def act(actor: Character, skill_id: str, target: Character | None = None) -> Action:
    return Action(actor=actor, skill=SKILLS[skill_id], target=target)


def test_status_ticks_exactly_duration_times_then_expires():
    p = mk(name="P", spd=9)
    e = mk(name="E", side="enemy", spd=1, skills=["guard"])  # E won't touch P's HP
    p.statuses.append(StatusEffect(name="Regen", duration=2, hp_per_turn=2))
    p.take_damage(20)
    bs = BattleState(players=[p], enemies=[e])
    bs.step(act(p, "attack", e))                   # P tick 1: heal 2, dur 2 -> 1
    bs.step(act(bs.current_actor(), "guard"))      # E guards
    bs.step(act(bs.current_actor(), "attack", e))  # P tick 2: heal 2, dur 1 -> 0, dropped
    assert p.statuses == []
    assert p.hp == 20 + 2 + 2


def test_debuff_lowers_damage_while_active():
    a = mk(name="A", spd=9)
    v = mk(name="V", side="enemy", spd=1)
    base = physical_damage(a, v, SKILLS["attack"].power)
    a.statuses.append(StatusEffect(name="Weaken", duration=1, atk_mod=-4))
    assert physical_damage(a, v, SKILLS["attack"].power) < base


def test_legal_actions_hides_skills_you_cannot_afford():
    poor = mk(name="Poor", max_mp=0, skills=["attack", "fireball"])
    bs = BattleState(players=[poor], enemies=[mk(name="E", side="enemy")])
    assert {a.skill.id for a in bs.legal_actions(poor)} == {"attack"}


def test_legal_actions_only_offers_known_skills():
    mage = mk(name="Mage", skills=["attack", "fireball"])
    bs = BattleState(players=[mage], enemies=[mk(name="E", side="enemy")])
    assert {a.skill.id for a in bs.legal_actions(mage)} == {"attack", "fireball"}
```

The `mk`/`act` helpers here reference skills (`"fireball"`, `"guard"`) that don't
exist until Stage 2, so `test_legal_actions_*` and the tick test fail with
`KeyError` for now — that's expected; Stage 2 clears them.

### The change

**`battle_core/entities.py`** — one field on `Character`, right after `statuses`:

```python
    statuses: list[StatusEffect] = field(default_factory=list)
    skills: list[str] = field(default_factory=lambda: ["attack"])
```

**`battle_core/battle.py`** — `legal_actions` iterates the actor's own list:

```python
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
```

(If your `legal_actions` from Lesson 01 looks a little different — a helper
method, a different loop shape — keep your structure; just swap the *source* of
skills from `SKILLS.values()` to `actor.skills` and add the `SKILLS[skill_id]`
lookup.)

Run the Lesson 01 tests — still green. The new tests still fail on missing
skills. Commit Stage 1 together with Stage 2 (they're one lesson's worth of
change and the new tests only pass after Stage 2).

---

## Stage 2 — The spell and ability set

### The six skills

| id | name | MP | power | target | kind | effect |
|---|---|---|---|---|---|---|
| `fireball` | Fireball | 6 | 12 | one enemy | magic | flat 12, ignores armour |
| `firestorm` | Firestorm | 14 | 9 | all enemies | magic | flat 9 to every living foe |
| `heal` | Heal | 6 | 14 | one ally | heal | restore 14, capped at max HP |
| `poison_dart` | Poison Dart | 4 | 2 | one enemy | physical | 2 damage + Poison (−4/turn, 3 turns) |
| `warcry` | War Cry | 3 | 0 | self | guard | Braced: +2 atk, +4 def, 2 turns |
| `guard` | Guard | 0 | 0 | self | guard | Guarding: +6 def, 1 turn |

### `battle_core/skills.py`

Replace the `SKILLS` dict:

```python
SKILLS: dict[str, Skill] = {
    "attack": Skill(
        id="attack", name="Attack", mp_cost=0, power=6,
        target_kind=TargetKind.ONE_ENEMY, kind="physical",
    ),
    "fireball": Skill(
        id="fireball", name="Fireball", mp_cost=6, power=12,
        target_kind=TargetKind.ONE_ENEMY, kind="magic",
    ),
    "firestorm": Skill(
        id="firestorm", name="Firestorm", mp_cost=14, power=9,
        target_kind=TargetKind.ALL_ENEMIES, kind="magic",
    ),
    "heal": Skill(
        id="heal", name="Heal", mp_cost=6, power=14,
        target_kind=TargetKind.ONE_ALLY, kind="heal",
    ),
    "poison_dart": Skill(
        id="poison_dart", name="Poison Dart", mp_cost=4, power=2,
        target_kind=TargetKind.ONE_ENEMY, kind="physical",
        status_template=StatusEffect(name="Poison", duration=3, hp_per_turn=-4),
    ),
    "warcry": Skill(
        id="warcry", name="War Cry", mp_cost=3, power=0,
        target_kind=TargetKind.SELF, kind="guard",
        status_template=StatusEffect(name="Braced", duration=2, atk_mod=2, def_mod=4),
    ),
    "guard": Skill(
        id="guard", name="Guard", mp_cost=0, power=0,
        target_kind=TargetKind.SELF, kind="guard",
        status_template=StatusEffect(name="Guarding", duration=1, def_mod=6),
    ),
}
```

### What the engine needs: almost nothing

Look at your `_apply_skill` from Lesson 01. It already:

- branches on `kind` for `"physical"` / `"magic"` / `"heal"`;
- expands `victims` from `target_kind` (`ALL_ENEMIES` → every foe, `SELF` →
  the actor, otherwise `[action.target]`);
- applies `status_template` (via `replace()`) to every victim afterwards.

So:

- **Fireball** — `kind="magic"`, one victim, existing magic branch. ✅
- **Firestorm** — `target_kind=ALL_ENEMIES`, existing victim expansion + magic
  branch, runs once per foe. ✅
- **Heal** — `kind="heal"`, existing heal branch. ✅
- **Poison Dart** — `kind="physical"` (the 2 damage) **then** `status_template`
  (the Poison), both already handled. ✅
- **War Cry / Guard** — `kind="guard"`. None of the physical/magic/heal branches
  match, so no damage happens; then `status_template` applies to the victim,
  which for a `SELF` skill is the actor. ✅

**Zero engine changes.** If you want a `guard` case for readability you can add
`elif skill.kind == "guard": pass` in the `kind` branch, but it changes no
behaviour — the fall-through already does the right thing. That's the whole
point of pushing behaviour into data: a new *kind* of effect might need a branch;
a new *skill* of an existing kind never does.

> **One thing to double-check in your code:** the `status_template` must be
> `replace()`d, not appended directly. Two enemies hit by the same Poison Dart
> must get *independent* `StatusEffect` objects — otherwise they share one
> `duration` counter and both expire when the first one ticks out. Your Lesson 01
> `test_poison_ticks_at_turn_start` doesn't catch this; the auto-battle in the
> checkpoint would eventually behave strangely.

### The tests

New file `tests/test_spells.py`:

```python
from battle_core import SKILLS, Action, BattleState, Character

BASE = {"name": "C", "side": "player", "slot": 0, "max_hp": 40, "max_mp": 30,
        "base_atk": 10, "base_def": 5, "spd": 5,
        "skills": ["attack", "fireball", "firestorm", "heal", "poison_dart",
                   "warcry", "guard"]}


def mk(**kw) -> Character:
    return Character(**{**BASE, **kw})


def act(actor: Character, skill_id: str, target: Character | None = None) -> Action:
    return Action(actor=actor, skill=SKILLS[skill_id], target=target)


def test_fireball_spends_mp_and_ignores_armour():
    caster = mk(name="Mage", spd=9)
    orc = mk(name="Orc", side="enemy", spd=1, base_def=99)
    bs = BattleState(players=[caster], enemies=[orc])
    bs.step(act(caster, "fireball", orc))
    assert caster.mp == 30 - 6
    assert orc.hp == orc.max_hp - 12


def test_firestorm_hits_every_living_enemy():
    caster = mk(name="Mage", spd=9)
    e0 = mk(name="E0", side="enemy", slot=0, spd=1)
    e1 = mk(name="E1", side="enemy", slot=1, spd=1)
    bs = BattleState(players=[caster], enemies=[e0, e1])
    bs.step(act(caster, "firestorm"))
    assert e0.hp < e0.max_hp
    assert e1.hp < e1.max_hp


def test_heal_restores_an_ally_without_overshoot():
    medic = mk(name="Medic", slot=0, spd=9)
    tank = mk(name="Tank", slot=1, spd=1)
    tank.take_damage(10)
    bs = BattleState(players=[medic, tank], enemies=[mk(name="E", side="enemy", spd=0)])
    bs.step(act(medic, "heal", tank))
    assert tank.hp == tank.max_hp


def test_poison_dart_hits_and_applies_poison():
    rogue = mk(name="Rogue", spd=9)
    foe = mk(name="Foe", side="enemy", spd=1)
    bs = BattleState(players=[rogue], enemies=[foe])
    bs.step(act(rogue, "poison_dart", foe))
    assert foe.hp < foe.max_hp
    assert [s.name for s in foe.statuses] == ["Poison"]


def test_warcry_buffs_the_caster_only():
    fighter = mk(name="Fighter", spd=9)
    bs = BattleState(players=[fighter], enemies=[mk(name="E", side="enemy", spd=0)])
    d0, a0 = fighter.defense, fighter.atk
    bs.step(act(fighter, "warcry"))
    assert fighter.defense == d0 + 4
    assert fighter.atk == a0 + 2


def test_guard_is_free_and_shields_for_one_turn():
    p = mk(name="P", spd=9)
    e = mk(name="E", side="enemy", spd=1)
    bs = BattleState(players=[p], enemies=[e])
    bs.step(act(p, "guard"))
    assert p.mp == 30
    assert p.defense == p.base_def + 6
    bs.step(act(e, "attack", p))
    bs.step(act(p, "attack", e))
    assert p.defense == p.base_def
```

```bash
uv run pytest -v      # all green now, including the Stage-1 tests
uv run ruff check .
```

### Give the parties real kits

`battle_core/content.py` — add a `skills=` argument to each `Character`:

```python
def make_default_player_party() -> list[Character]:
    return [
        Character(name="Aria", side="player", slot=0, max_hp=34, max_mp=20,
                  base_atk=9, base_def=5, spd=7,
                  skills=["attack", "fireball", "heal", "guard"]),
        Character(name="Bran", side="player", slot=1, max_hp=42, max_mp=8,
                  base_atk=11, base_def=7, spd=4,
                  skills=["attack", "warcry", "guard"]),
    ]


def make_default_enemy_party(n: int = 2) -> list[Character]:
    roster = [
        Character(name="Goblin", side="enemy", slot=0, max_hp=26, max_mp=6,
                  base_atk=8, base_def=4, spd=6,
                  skills=["attack", "poison_dart"]),
        Character(name="Acolyte", side="enemy", slot=1, max_hp=22, max_mp=24,
                  base_atk=6, base_def=3, spd=5,
                  skills=["attack", "fireball", "heal"]),
        Character(name="Brute", side="enemy", slot=2, max_hp=48, max_mp=4,
                  base_atk=12, base_def=6, spd=3,
                  skills=["attack", "firestorm", "warcry"]),
    ]
    return roster[:n]
```

(Ruff will reflow the argument formatting — run `--fix`, don't fight it.)

Aria is the glass-cannon support: fire and heals on a big MP pool. Bran is the
front line: little MP, War Cry, Guard. The Acolyte mirrors Aria — the enemy has
its own healer, which is exactly the kind of thing an RL policy will have to
learn to play around (focus the healer first?).

### Balancing notes (read these — they're the *design* content)

- **Flat magic vs scaling physical.** Fireball always does 12. Attack does
  `round(6·atk/def)` — great against the def-4 Goblin, feeble against the def-6
  Brute. So a mage is your answer to armour, and a physical attacker wants War
  Cry up first.
- **MP is the whole economy.** Aria can cast ~3 Fireballs *or* ~3 Heals, not
  both. Every spell is a bet that this fight ends before she needs the other.
- **Poison is tempo.** 2 + 4 + 4 + 4 = 14 total for 4 MP, but spread over three
  turns — worth it on a tanky target early, wasted on something that'll die
  first.
- **Firestorm is a back-line answer** priced so you basically can't open with it
  (14 MP). The Brute *can*, barely, once.

You'll revisit every one of these numbers in a balancing pass once the RL agent
starts exploiting them. That's a feature.

### Update `design.md`

Fill in the skills table (the six-row table above, plus Attack) and add each
character's `skills` list to the party table.

### Commit

```bash
git add -A
git commit -m "feat(part-a): spells, buffs, poison, and per-character skill kits (Lesson 02)"
```

---

## Checkpoint

- [ ] `uv run pytest` — all green (Lesson 01 tests + `test_status_effects.py` +
      `test_spells.py`).
- [ ] `uv run ruff check .` clean.
- [ ] In a REPL, an auto-battle with kits still terminates:
      ```python
      from battle_core import BattleState
      from battle_core.content import make_default_player_party, make_default_enemy_party
      bs = BattleState(players=make_default_player_party(), enemies=make_default_enemy_party(3))
      while not bs.is_over():
          a = bs.current_actor()
          act = bs.legal_actions(a)[0]
          print(a.name, act.skill.id, "->", act.target.name if act.target else "-")
          bs.step(act)
      print("winner:", bs.winner())
      ```
- [ ] One commit for the lesson (Stage 1 + Stage 2 together).

### In RL terms

Your action space just went from "pick a target" to "pick a skill **and** a
target, from a set that changes every turn as MP drains and enemies die". In
Part C that variable-size set becomes a **fixed-size action vector with a
legality mask** — `legal_actions()` is what generates the mask. The skill kits
you just wrote are the reason the mask is interesting: a policy controlling the
Brute has a genuinely different decision problem from one controlling the
Acolyte, and *one shared network* has to handle both.

Next: Lesson 03 — a pygame face on all this. HP/MP bars, an action menu, target
selection, and a scripted enemy AI (which doubles as the RL baseline).

Ping me when the checkpoint passes.
