# AI RPG — Design Reference

See `docs/superpowers/specs/2026-09-06-ai-rpg-tutorial-design.md` for the full spec.

## Architecture

- `battle_core/` — pure-Python combat rules. No pygame/torch/numpy. Source of truth.
- `game/` — pygame rendering, input, scenes.
- `rl/` — (Part C) Gymnasium env + from-scratch DQN.
- `dialogue/` — (Part B) swappable LLM backend + NPC personas.

## Skill & Stat Tables

|| id | name | MP | power | target | kind | effect |
|---|---|---|---|---|---|---|--|
| `fireball` | Fireball | 6 | 12 | one enemy | magic | flat 12, ignores armour |
| `firestorm` | Firestorm | 14 | 9 | all enemies | magic | flat 9 to every living foe |
| `heal` | Heal | 6 | 14 | one ally | heal | restore 14, capped at max HP |
| `poison_dart` | Poison Dart | 4 | 2 | one enemy | physical | 2 damage + Poison (−4/turn, 3 turns) |
| `warcry` | War Cry | 3 | 0 | self | guard | Braced: +2 atk, +4 def, 2 turns |
| `guard` | Guard | 0 | 0 | self | guard | Guarding: +6 def, 1 turn |


| Name | Side | Slot | Max HP | Max MP | Base Attack | Base Defense | Speed | Skills |
|---|---|---|---|---|---|---|---|---|
| Aria | player | 0 | 34 | 20 | 9 | 5 | 7 | "attack", "fireball", "heal", "guard" |
| Bran | player | 1 | 42 | 8 | 11 | 7 | 4 | "attack", "warcry", "guard" |
| Goblin | enemy | 0 | 26 | 6 | 8 | 4 | 6 | "attack", "poison_dart" |
| Acolyte | enemy | 1 | 22 | 24 | 6 | 3 | 5 | "attack", "fireball", "heal" |
| Brute | enemy | 2 | 48 | 4 | 12 | 6 | 3 | "attack", "firestorm", "warcry" |

