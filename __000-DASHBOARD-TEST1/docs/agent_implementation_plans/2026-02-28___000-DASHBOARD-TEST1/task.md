# GLOBAL DOCUMENTATION POLICY
- **Requirement**: ALL new and updated Implementation Plans and Walkthroughs MUST be saved to BOTH:
    1.  The specific skill's documentation folder: `[SKILL]/docs/agent_implementation_plans/[DATE]/`
    2.  The global mirror folder: `000z-IMPLIMENTATION_PLANS/[DATE]_[SKILL]/`
- **Adherence**: This is a mandatory, persistent requirement for all future tasks.

# Task: Resolve Missing visual output for Convtr-Md2PDF

- [x] Investigate skill implementation and output directory <!-- id: 0 -->
- [x] Determine why visual result is not showing <!-- id: 1 -->
- [x] Provide instructions or fix to show visual result/download <!-- id: 2 -->
- [x] Verify fix with user <!-- id: 3 -->

# Task: Resolve Missing visual output for Convtr-PlainTxt2PDF
- [x] Investigate skill implementation and output directory <!-- id: 4 -->
- [x] Determine why visual result is not showing <!-- id: 5 -->
- [x] Provide instructions or fix to show visual result/download <!-- id: 6 -->
- [x] Verify fix with user <!-- id: 7 -->

# Task: Refine Dashboard for Document Visibility
- [x] Analyze `app.py` for popup trigger logic <!-- id: 8 -->
- [x] Implement document preview in `show_result_popup` <!-- id: 9 -->
- [x] Refine RTF List Parsing (Indentation & Numbers)
- [x] Improve Copy-Paste Fidelity (2-space model)
- [x] Relocate PDF Download Button
- [x] Style "PROCESSED RESULT" Header (#eb4c1f)
- [x] Fix PDF Character Rendering (?)
- [x] Map Hollow Bullets to Asterisks
- [x] Tighten Download/Copy Button Spacing
- [x] Implement Native TTF Emoji Support in PDF
- [x] Implement "Emoji Weaver" Manual Fragmenter for 1️⃣, 2️⃣ composition
- [x] Ensure Dashboard uses .venv Python for all skills
- [x] Tag Stable Release as REF_0
- [x] Implement Unified Document Navigation (Previous/Next)
- [x] Verify with `Consistency_SAMSON.rtf` <!-- id: 13 -->
- [x] Verify and fix skill state isolation
    - [x] Namespace `audio_index`
    - [x] Namespace `auto_open_result`
    - [x] Namespace `popup_batch_success`
    - [x] Namespace `direct_download_file`
    - [x] Ensure "Recent Used" skills sidebar logic is independent
- [x] Final Verification and Walkthrough
<!-- [x] **Project Documentation Archiving**
    - [x] Archive Skill Isolation Plan/Walkthrough to `Convtr-PlainTxt2PDF/docs/...`
    - [x] Always archive all future implementation plans and walkthroughs to the project docs folder.
    - [x] Archive all plans to global `000z-IMPLIMENTATION_PLANS` folder. -->
- [x] **UI Refinement: Custom Processing Overlay**
    - [x] Hide default Streamlit "Running" status icon (Running Man).
    - [x] Implement centered "PROCESSING..." overlay with progress bar.
    - [x] Ensure overlay is prominent and visually consistent with Cyan accent.
- [x] **Isolate Skill States and Filter Results**
    - [x] Namespace session state keys by `selected_skill_id` in `app.py`.
    - [x] Update state initialization for namespaced keys.
    - [x] Update all state usage to use namespaced versions.
    - [x] Verify results area only displays active skill's output.
    - [x] Test state persistence when switching between skills.
- [x] **RTF Display Issues**
    - [x] Identify raw RTF jibberish in display.
    - [x] Remove `.rtf` from plaintext whitelist in `process_tts_files`.
    - [x] Save actual parsed text in `text2speech.py`.
    - [x] Read and display parsed `.txt` instead of raw file or placeholder.
- [x] **Add Search Icons**
    - [x] Integrate FontAwesome or similar for search/help.
- [x] **Dashboard Styling**
    - [x] Add 7px radius to search field.
- [x] **Dashboard Refinements**
    - [x] Set default skill to `AI-LLM-Text2Speech` on first load.
- [x] Implement an alternative method to guarantee popup opening <!-- id: 14 -->
- [x] Verify fix with user <!-- id: 15 -->

# Task: Recently Used Skills Area
- [x] Read and write a persistent recent_skills.json file
- [x] Render up to 4 recent skills at the top of the sidebar
- [x] Add logic to update recent list on skill selection
- [x] Connect recent buttons to session_state to jump to skill
- [x] Verify fix with user
