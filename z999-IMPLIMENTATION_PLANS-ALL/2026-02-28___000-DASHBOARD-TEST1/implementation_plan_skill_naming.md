# Skill Name Matching Implementation Plan

Ensure the Antigravity Dashboard displays skill names that match the physical folder names (e.g., `AI-LLM-Speech2Text`) instead of potentially inconsistent names in the `SKILL.md` frontmatter.

## Proposed Changes

### Dashboard Application

#### [MODIFY] [app.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/__000-DASHBOARD-TEST1/app.py)
- Update `discover_skills()` to:
    1.  Use the **folder basename** (e.g., `AI-LLM-Speech2Text`) as the primary `name`.
    2.  Optionally keep the YAML `name` as a `friendly_name` or `subtitle` if it provides additional context, but the sidebar should primarily show the Antigravity name.
    3.  For specialized input checks (like `selected_skill["name"] == "Text2Speech"`), I'll update them to use `basename` or a more robust check since names are changing.

## Verification Plan

### Automated/Manual Verification
1.  **Run Dashboard**: Open the dashboard at `http://localhost:8502`.
2.  **Sidebar Check**: Verify that skills are now named according to their folders (e.g., `AI-LLM-Speech2Text` instead of `speech-to-text-with-ai`).
3.  **Specialized UI Check**: Confirm that selecting `AI-LLM-Text2Speech` still triggers the specialized upload UI.
