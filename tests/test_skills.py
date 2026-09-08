from battle_core import SKILLS, Character, TargetKind
from battle_core.skills import heal_amount, magic_damage, physical_damage

BASE = {
    "name": "X",
    "side": "player",
    "slot": 0,
    "max_hp": 30,
    "max_mp": 10,
    "base_atk": 10,
    "base_def": 5,
    "spd": 5,
}


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
