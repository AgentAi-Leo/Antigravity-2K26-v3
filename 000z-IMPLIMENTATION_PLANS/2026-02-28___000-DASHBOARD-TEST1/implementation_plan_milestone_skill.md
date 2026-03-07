# Milestone Git Backup Skill (REF_0)

This plan outlines the creation of a new specialized skill that automates the transition from local development to a tagged "Milestone" state on GitHub.

## User Review Required

> [!IMPORTANT]
> This skill will perform a **force-push for tags**. Ensure that the `REF_0` tag is not being used by other collaborators in a way that would cause data loss if overwritten.

## Proposed Changes

### [NEW] 000A_BKUP-GitBackup-REF_0
A new master skill folder containing the automated milestone update logic.

#### [NEW] [SKILL.md](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/_000_MASTER-SKIILS/000A_BKUP-GitBackup-REF_0/SKILL.md)
- Define the `name` and `description` for discovery.
- Document use cases: "Marking a software release", "Creating a major milestone", "Syncing all skills to cloud with a tag".

#### [NEW] [milestone_backup.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/_000_MASTER-SKIILS/000A_BKUP-GitBackup-REF_0/scripts/milestone_backup.py)
- A robust Python script that:
    1. Stages all changes (`git add .`).
    2. Commits with a mandatory message (prefixed with the tag name).
    3. Manages the `REF_0` tag:
        - Checks for existing local/remote tag.
        - Deletes stale tags to allow "moving" the milestone label.
        - Creates the fresh `REF_0` tag on the current head.
    4. Pushes the branch and the tags to `origin` with `--force`.

## Verification Plan

### Automated Verification
- I will run the script in a test directory to ensure it correctly stages, commits, tags, and pushes.
- I will verify that it handles the "tag already exists" case gracefully by deleting the old tag first.

### Manual Verification
- I will ask the user to run the skill once through their terminal or I can trigger it once to verify the remote reflects the `REF_0` update.
