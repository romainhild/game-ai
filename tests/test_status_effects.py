from battle_core import SKILLS, Action, BattleState, Character, StatusEffect
from battle_core.skills import physical_damage

BASE = {
    "name": "C",
    "side": "player",
    "slot": 0,
    "max_hp": 40,
    "max_mp": 30,
    "base_atk": 10,
    "base_def": 5,
    "spd": 5,
}


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
    bs.step(act(p, "attack", e))  # P tick 1: heal 2, dur 2 -> 1
    bs.step(act(bs.current_actor(), "guard"))  # E guards
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
