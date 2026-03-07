# Implementation Plan: Dashboard Skill Search

The goal is to add a search box to the dashboard sidebar, allowing users to quickly filter the list of available skills by typing part of the skill's name or description.

## Proposed Changes

### [MODIFY] [app.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/__000-DASHBOARD-TEST1/app.py)

1.  **Add Search Input**:
    Right below `st.sidebar.title("🚀 Antigravity Skills")`, add a search box:
    ```python
    search_query = st.sidebar.text_input("🔍 Search skills...", "").lower()
    ```

2.  **Filter the Skills List**:
    Before creating the radio buttons, filter the downloaded `skills` list:
    ```python
    if search_query:
        display_skills = [
            s for s in skills 
            if search_query in s['name'].lower() or search_query in s['desc'].lower()
        ]
    else:
        display_skills = skills
    ```

3.  **Update Radio State Logic**:
    Update the `st.sidebar.radio` options to use `display_skills` instead of `skills`.
    We must ensure that if a user searches and the previously selected skill disappears from the list, the radio button gracefully defaults to the first available searched skill (or displays a "No matching skills" message if empty).

## Verification Plan

### Manual Verification
1. Open the dashboard.
2. Verify the search box appears in the left sidebar.
3. Type "Text" into the search box.
4. Verify the list shrinks to only show skills like `Txt2Pdf`, `PlainTxt2PDF`, and `AI-LLM-Text2Speech`.
5. Clear the search box and verify all skills return.
