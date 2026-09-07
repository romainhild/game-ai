from battle_core import Character, StatusEffect

BASE = {
    "name": "Hero",
    "side": "player",
    "slot": 0,
    "max_hp": 30,
    "max_mp": 10,
    "base_atk": 8,
    "base_def": 4,
    "spd": 6,
}


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
