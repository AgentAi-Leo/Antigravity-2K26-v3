---
name: creating-antigravity-skills
description: Generates well-structured Antigravity skill directories with a compliant SKILL.md and optional supporting files. Use when the user asks to create, build, add, or scaffold a new skill, agent skill, or .agent/skills/ entry for the Antigravity environment.
---

# Antigravity Skill Creator

## When to Use This Skill

- User says "create a skill", "build a new skill", "add a skill", or "scaffold a skill"
- User describes a repeatable workflow they want packaged as an agent skill
- User asks to convert an existing script or process into a reusable skill

---

## Output Structure

Every skill lives in its own named folder inside the skills root:

```
<skill-name>/
├── SKILL.md          ← Required. Main logic and instructions.
├── scripts/          ← Optional. Helper scripts.
├── examples/         ← Optional. Reference implementations.
└── resources/        ← Optional. Templates, assets, static files.
```

> **Rule:** The file must always be named exactly `SKILL.md`. Do not rename it.

---

## Workflow

- [ ] 1. Clarify the skill's purpose and triggers with the user if ambiguous
- [ ] 2. Determine which optional folders are needed (`scripts/`, `examples/`, `resources/`)
- [ ] 3. Write `SKILL.md` following the standards below
- [ ] 4. Write any supporting scripts or resource files
- [ ] 5. Validate the YAML frontmatter and folder structure
- [ ] 6. Confirm with the user

---

## Instructions

### YAML Frontmatter Rules

```yaml
---
name: gerund-verb-noun          # e.g., converting-text, managing-configs
description: Third-person description ending with trigger keywords. Max 1024 chars.
---
```

| Field | Rules |
|---|---|
| `name` | Gerund form. Lowercase, hyphens, numbers only. Max 64 chars. No "claude" or "anthropic". |
| `description` | Third person. Must include specific trigger phrases the agent will match against. |

**Good example:**
```yaml
name: converting-text-to-pdf
description: Converts structured text files into formatted PDFs. Use when the user mentions PDF generation, prompt export, or document conversion.
```

---

### SKILL.md Body Template

```markdown
# [Skill Title]

## When to Use This Skill
- [Trigger condition 1]
- [Trigger condition 2]

---

## Workflow
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

---

## Instructions

[Core logic here. Be concise — the agent is smart.]

### Key Rules
- Use `/` for all paths, never `\`
- Keep SKILL.md under 500 lines; link to secondary files for depth
- Use `--help` on any unfamiliar script before running it

---

## Resources
- `scripts/` — [brief description]
- `resources/` — [brief description]
```

---

### Degrees of Freedom Guide

| Task Type | Format to Use |
|---|---|
| High freedom (heuristics, judgment calls) | Bullet points |
| Medium freedom (repeatable patterns) | Code block templates |
| Low freedom (fragile, exact commands) | Specific bash commands |

---

### Writing Principles

- **Concise**: Skip basic explanations. Focus only on the skill's unique logic.
- **Progressive disclosure**: Keep `SKILL.md` lean; offload detail to secondary `.md` files linked one level deep.
- **Black-box scripts**: Tell the agent to run `--help` if script behavior is unclear.
- **Validation before execution**: For destructive or config-changing operations, include a check step before the action step.

---

### Validation Checklist (before finalizing)

- [ ] `SKILL.md` filename is exactly `SKILL.md`
- [ ] YAML frontmatter is present and valid
- [ ] `name` is in gerund form, lowercase, hyphens only
- [ ] `description` is third-person and includes trigger keywords
- [ ] Body is under 500 lines
- [ ] All paths use forward slashes
- [ ] Supporting files are placed in correct subfolders
