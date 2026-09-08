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
    assert events[0].amount == -3
    assert p.statuses[0].duration == 1


def test_legal_actions_expands_over_targets():
    p = char("P", "player", 0, spd=5)
    e0 = char("E0", "enemy", 0, spd=5)
    e1 = char("E1", "enemy", 1, spd=5)
    bs = BattleState(players=[p], enemies=[e0, e1])
    actions = bs.legal_actions(p)
    hit = [a.target for a in actions if a.skill.id == "attack"]
    assert hit == [e0, e1]  # a list, not a set: Character isn't hashable


def test_default_parties_build_and_fight():
    from battle_core.content import make_default_enemy_party, make_default_player_party

    bs = BattleState(players=make_default_player_party(), enemies=make_default_enemy_party())
    for _ in range(500):
        if bs.is_over():
            break
        actor = bs.current_actor()
        bs.step(bs.legal_actions(actor)[0])
    assert bs.is_over()
