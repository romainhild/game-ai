# AI RPG — Design Reference

See `docs/superpowers/specs/2026-09-06-ai-rpg-tutorial-design.md` for the full spec.

## Architecture

- `battle_core/` — pure-Python combat rules. No pygame/torch/numpy. Source of truth.
- `game/` — pygame rendering, input, scenes.
- `rl/` — (Part C) Gymnasium env + from-scratch DQN.
- `dialogue/` — (Part B) swappable LLM backend + NPC personas.

## Skill & Stat Tables

_Filled in during Lessons 01–02._
