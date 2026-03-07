# Recently Used Skills Implementation Plan

## Goal
Add a persistent "Recently Used" section to the top of the dashboard sidebar, displaying up to the last 4 accessed skills. This allows the user to quickly return to common scripts without scrolling or searching through the alphabetical list.

## Approach

1. **Persistence Mechanism**:
   - Create a helper function to manage persistent storage via a JSON file (`recent_skills.json`).
   - The file will live inside the `__000-DASHBOARD-TEST1` directory (or be ignored by git if necessary).
   - The file will store a list of skill IDs (e.g., `["AI-LLM-Text2Speech", "AI-LLM-SummarizeDoc"]`).

2. **Integration into Sidebar**:
   - At the top of the sidebar (below search, above the main list), read the recent skills file.
   - Display a header `### Recently Used:`.
   - Render up to 4 Streamlit `st.sidebar.button()` elements (or a compact format) representing these skills.
   - When a user clicks a "Recently Used" button, update Streamlit's `st.session_state` to switch the main radio button selection to that skill.

3. **Tracking Usage**:
   - Whenever the main radio button changes (or right after rendering the skill view), push the currently `selected_skill_id` to the front of the recent list.
   - Distinct values only (remove duplicates).
   - Slice the list to keep only the top 4.
   - Save back to `recent_skills.json`.

## Files to Modify

### `app.py`
- Import `json`.
- Define path: `RECENT_SKILLS_FILE = os.path.join(os.path.dirname(__file__), "recent_skills.json")`
- `load_recent_skills()` & `save_recent_skill(skill_id)`.
- Update the sidebar UI to display the buttons dynamically based on recently saved IDs.
- Ensure the main radio button respects `st.session_state.selected_skill_id` so clicking a recent button effectively "jumps" to it.

## Verification Plan
- Verify that selecting a skill adds it to the list.
- Verify the list caps at 4 entries.
- Verify that refreshing the page retains the 4 chosen skills.
- Verify that clicking a "recent" button successfully navigates to that skill.
