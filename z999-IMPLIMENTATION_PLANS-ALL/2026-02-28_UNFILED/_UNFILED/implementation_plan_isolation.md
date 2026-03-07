# Skill State Isolation Implementation Plan

## Goal
Ensure each skill in the dashboard operates independently by isolating its session state. When a user switches skills, they should see a clean slate (or that skill's specific history), and results from one skill should never appear in another.

## User Review Required
> [!IMPORTANT]
> This change will reset the current session's processed files lists. Users will need to re-upload files to see them in the "MY CLIPS" or results sections for each skill.

## Proposed Changes

### Dashboard Application (`app.py`)

#### [MODIFY] [app.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/__000-DASHBOARD-TEST1/app.py)

- **Define Skill-State Namespacing**:
  Implement a consistent strategy for accessing session state keys. Use `f"{selected_skill_id}_{key}"` for all skill-specific data.

- **Namespace the following keys**:
  - `processed_files` -> `f"processed_files_{selected_skill_id}"`
  - `processed_popup_files` -> `f"processed_popup_files_{selected_skill_id}"`
  - `last_output` -> `f"last_output_{selected_skill_id}"`
  - `last_audio_files` -> `f"last_audio_files_{selected_skill_id}"`
  - `audio_index` -> `f"audio_index_{selected_skill_id}"`
  - `auto_open_result` -> `f"auto_open_result_{selected_skill_id}"`
  - `popup_batch_success` -> `f"popup_batch_success_{selected_skill_id}"`
  - `direct_download_file` -> `f"direct_download_file_{selected_skill_id}"`
  - `prev_upload_id` -> `f"prev_upload_id_{selected_skill_id}"`
  - `prev_file_counts_dict` -> `f"prev_file_counts_dict_{selected_skill_id}"`

- **Update Initialization Logic**:
  Near the top of the app, ensure these keys are initialized for the `selected_skill_id` if they aren't already.

- **Update Results Rendering**:
  Ensure the results rendering block (at the end of `app.py`) uses the namespaced `last_output` so it only displays if the current skill has a result.

## Verification Plan

### Manual Verification
1. **Skill A (Text2Speech)**:
   - Upload a file and process it. 
   - Verify audio player and transcript appear.
2. **Switch to Skill B (SummarizeDoc)**:
   - Verify the "PROCESSED RESULT" and "MY CLIPS" sections disappear (because Skill B hasn't run yet).
   - Upload a different file and process it.
   - Verify Skill B results appear.
3. **Switch back to Skill A**:
   - Verify Skill A's previous audio results and transcript are restored exactly as they were.
4. **Consistency check**:
   - Verify that "Recent Used" sidebar buttons correctly switch skills and reload the distinct states.
