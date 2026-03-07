---
description: Auto-saving implementation plans to dual directories
---

# Global Rule: Dual-Saving Implementation Plans

Whenever you generate an implementation plan or design document (such as `implementation_plan.md`) for a task or a skill, you **MUST automatically** physically copy that markdown file to TWO distinct physical locations on disk before notifying the user of completion.

1. **Decentralized (Local to the Skill)**: 
   Copy the plan into the specific skill's directory under `docs/agent_implementation_plans/YYYY-MM-DD/`.
   *Example*: `___000A-ANTIGRAVITY-SKILLS/AI-LLM-Text2Speech/docs/agent_implementation_plans/2026-02-28/implementation_plan.md`

2. **Centralized (Global Tracker)**:
   By default (until otherwise instructed), copy the plan into the root project's master documentation tracker under `000z-IMPLIMENTATION_PLANS/YYYY-MM-DD_[SkillName]/`.
   *Example*: `___000A-ANTIGRAVITY-SKILLS/000z-IMPLIMENTATION_PLANS/2026-02-28_AI-LLM-Text2Speech/implementation_plan.md`

This guarantees that the skill remains portable while simultaneously keeping an easily browsable chronological history for the user at the root of the project.
