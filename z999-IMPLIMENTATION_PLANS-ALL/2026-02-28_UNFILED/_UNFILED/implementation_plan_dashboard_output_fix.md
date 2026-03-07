# Fix URL Output and Direct File Download

Currently, the dashboard shows logs as results and re-generates PDFs from those logs, ignoring the high-quality files produced by skills like `Md2PDF`.

## Proposed Changes

### Md2PDF Skill

#### [MODIFY] [md2pdf.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/Convtr-Md2PDF/scripts/md2pdf.py)
- When using `--url` (non-capture), print the downloaded Markdown content to `stdout` so the dashboard can display it.

### Dashboard Integration

#### [MODIFY] [app.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/__000-DASHBOARD-TEST1/app.py)
- **Identify Saved Files**: In the execution logic, scan `stdout` for `Saved: <path>`.
- **Session State**: If a file is saved, read its bytes and store them in `st.session_state["direct_download_file"]`.
- **Filter Logs**: Update the `clean_output` filter to exclude "Fetching:", "Capturing:", and "Capturing high-fidelity" logs.
- **Enhanced Popup**: Update `show_result_popup` to offer a "📥 Download Original Result" button when a direct download is available.

## Verification Plan

### Automated Tests
- Run `md2pdf.py --url <url> --capture` and verify it prints `Saved: ...`.
- Verify `app.py` logic catches the filename.

### Manual Verification
- Test Notion capture in dashboard.
- Verify the popup shows a clean interface and offers the actual PDF for download.
