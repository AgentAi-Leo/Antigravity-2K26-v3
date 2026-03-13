---
description: How to save implementation plans (global requirement)
---

# Implementation Plan Saving — Global Requirement

Every implementation plan MUST be saved to **two locations**:

## 1. Skill Folder — Dated Subfolder
Save the implementation plan inside the relevant skill's own `implementation_plans/` directory, in a **dated subfolder**.

```
<skill-folder>/implementation_plans/YYYY-MM-DD_<Feature-Name>/implementation_plan.md
```

**Example:**
```
_001-ElevenLabs/AI-LLM-Speech2Text/implementation_plans/2026-02-28_API-Quota/implementation_plan_api_quota.md
```

## 2. Centralized Archive — Dated Subfolder
Save a copy to the global implementation plans directory, also in a **dated subfolder**:

```
z999-IMPLIMENTATION_PLANS-ALL/YYYY-MM-DD_<Feature-Name>/implementation_plan.md
```

**Example:**
```
z999-IMPLIMENTATION_PLANS-ALL/2026-02-28_API-Quota/implementation_plan_api_quota.md
```

## Summary
| Location | Path Pattern |
|----------|-------------|
| Skill folder | `<skill>/implementation_plans/YYYY-MM-DD_<Name>/` |
| Centralized archive | `z999-IMPLIMENTATION_PLANS-ALL/YYYY-MM-DD_<Name>/` |

## Checklist
- [ ] Implementation plan saved to **skill folder** under `implementation_plans/YYYY-MM-DD_<Name>/`
- [ ] Implementation plan copied to **z999-IMPLIMENTATION_PLANS-ALL/YYYY-MM-DD_<Name>/**
