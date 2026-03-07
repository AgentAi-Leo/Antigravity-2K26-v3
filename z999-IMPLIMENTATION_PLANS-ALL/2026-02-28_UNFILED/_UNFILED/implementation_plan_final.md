# Dashboard Final Refinement & Skill Integration

This plan resumes the dashboard project by integrating specialized UI inputs for remaining "AI-LLM" skills and refining the duplicate file warning behavior.

## User Review Required

> [!IMPORTANT]
> - New text inputs will appear for specialized skills (Image, Embed, RAG, Translate).
> - The duplicate file warning will now stay visible for 5 seconds instead of 2.

## Proposed Changes

### Dashboard Styles (`style.css`)

#### [MODIFY] [style.css](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/__000-DASHBOARD-TEST1/style.css)

- Update `fadeOutError` animation duration from `2s` to `5s`.
- Update `fadeOutError` keyframes to hold opacity at 1 until 80% of the duration.

---

### Dashboard Application (`app.py`)

#### [MODIFY] [app.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/__000-DASHBOARD-TEST1/app.py)

- **Add Specialized Skill Logic**:
    - `AI-LLM-ImageGenerate`: Show a text area for `--prompt`.
    - `AI-LLM-EmbedText`: Show a text area for `--text` or two inputs for `--compare`.
    - `AI-LLM-RAGQuery`: Show a text input for `--query`. Provide an "Index Documents" toggle.
    - `AI-LLM-TranslateText`: Show a text input for target language (`--to`).

- **Generalize Input Handling**:
    - For non-specialized skills, if no file is uploaded, offer a "Manual Text Input" text area that saves to a temp file and uses it as `--input`.

- **Refine Execution Loop**:
    - Ensure `shlex.split` handles the newly injected arguments correctly.
    - Add logic to display generated images (PNG) directly in the results section if the skill is `AI-LLM-ImageGenerate`.

---

## Verification Plan

### Automated Tests
- No automated tests available. Verification will be manual.

### Manual Verification
1. **Duplicate Error**: Upload a duplicate file and verify the warning stays for 5 seconds.
2. **Image Gen**: Select `AI-LLM-ImageGenerate`, enter a prompt, and verify the image is generated and displayed.
3. **Embeddings**: Select `AI-LLM-EmbedText`, enter text, and verify JSON output.
4. **Translate**: Select `AI-LLM-TranslateText`, enter a target language and text, and verify translation.
5. **RAG Query**: Select `AI-LLM-RAGQuery`, upload a file, enter a query, and verify the answer.
