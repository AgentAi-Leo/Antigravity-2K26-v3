# Dashboard Nested Folder Support Implementation Plan

Update the Antigravity Dashboard to robustly handle the new nested folder structure, ensuring unique skill identification and improved sidebar organization through categorization.

## Proposed Changes

### Dashboard Application

#### [MODIFY] [app.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/__000-DASHBOARD-TEST1/app.py)
1. **Update `discover_skills()`**:
   - Use `os.path.relpath(dirpath, root_dir)` as the skill `id` instead of just the basename.
   - Detect the "category" by taking the top-level folder name relative to `root_dir`.
   - Ensure the `id` is stable even when skills are moved.
2. **Improve Sidebar UI**:
   - Group skills by their detected category.
   - Use headers for categories and display skills underneath.
   - Update the radio button or selection mechanism to handle the new ID format.
3. **Refine Skill Identification Logic**:
   - Update specific UI logic (like the Speech2Text/Text2Speech specialized inputs) to check against the basename of the ID, ensuring they still work regardless of subfolder.

## Verification Plan

### Automated/Manual Verification
1. **Run Dashboard**: Verify that all skills (including those in `_000-ElevenLabs`) are detected.
2. **Sidebar Check**: Confirm that skills are grouped by their parent folder name in the sidebar.
3. **Functionality Check**: Select "Text2Speech" and verify that the specialized UI inputs (Upload Plain Text Files, Narration options) still appear and function correctly.
4. **Search Check**: Verify that searching still works across categorized skills.
