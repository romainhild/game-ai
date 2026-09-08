from battle_core import (
    SKILLS,
    Action,
    BattleState,
    Character,
)


def char(name: str, side: str, slot: int, spd: int, hp: int = 30) -> Character:
    return Character(
        name=name, side=side, slot=slot, max_hp=hp, max_mp=10, base_atk=8, base_def=4, spd=spd
    )


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
