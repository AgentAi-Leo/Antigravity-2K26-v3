# GLOBAL DOCUMENTATION POLICY
**Mandatory "Definition of Done" for all tasks:**
Every new or updated `implementation_plan` and `walkthrough` MUST be automatically and silently archived to both:
1. **Skill-Specific Docs:** `.../[SKILL]/docs/agent_implementation_plans/[DATE]/`
2. **Global Archive:** `.../z999-IMPLIMENTATION_PLANS-ALL/[DATE]_[SKILL]/`
*This must be completed before any `notify_user` call. No further prompting required.*

---

- [x] Investigation of `app.py` logic and UI requirements
- [x] Implementation of specialized UI inputs for AI skills:
    - [x] `AI-LLM-ImageGenerate`
    - [x] `AI-LLM-EmbedText`
    - [x] `AI-LLM-RAGQuery`
    - [x] `AI-LLM-TranslateText`
- [x] Implementation of manual text input fallback for skills without file uploads
- [x] Refinement of results display to support image rendering and multiple generated files
- [x] Styling refinement for duplicate error message (5s visibility)
- [x] Verification of full UI flow via browser tool
- [x] Clean up temporary bypasses and restore password check
- [x] Final walkthrough documentation
- [x] Implement basic recursive skill discovery
- [x] Refine skill discovery for nested folders (unique IDs)
- [x] Implement sidebar categorization by subfolder
- [x] Verify discovery and specialized inputs with new structure
- [x] Fix authentication and secret fetching via direct gcloud calls
- [x] Update walkthrough with categorization and auth fix details
- [x] Ensure strict redaction of sensitive data
- [x] Establish secure protocol for passing secrets to subagents (via temp files)
- [x] Verify no secrets are present in any current artifacts
- [x] Intercept ElevenLabs API quota errors in sub-scripts
- [x] Implement dashboard intercept for user-friendly quota warning popup
- [x] Copy implementation plan to master `z999-IMPLIMENTATION_PLANS-ALL` directory
- [x] Copy implementation plan to individual `_001-ElevenLabs` skill directories
