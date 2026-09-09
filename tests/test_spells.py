from battle_core import SKILLS, Action, BattleState, Character

BASE = {
    "name": "C",
    "side": "player",
    "slot": 0,
    "max_hp": 40,
    "max_mp": 30,
    "base_atk": 10,
    "base_def": 5,
    "spd": 5,
    "skills": ["attack", "fireball", "firestorm", "heal", "poison_dart", "warcry", "guard"],
}


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
