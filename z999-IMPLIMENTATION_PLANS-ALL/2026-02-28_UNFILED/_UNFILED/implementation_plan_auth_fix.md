# Authentication and Redaction Fix Implementation Plan

Fix the "Failed to fetch secret from GCP" error by simplifying the authentication logic and ensuring strict redaction of sensitive data in all logs and conversation history.

## User Review Required

> [!IMPORTANT]
> This change simplifies the secret fetching logic to call `gcloud` directly, which bypasses the local `secret_manager.py` script. This should be more robust in the Streamlit environment.
> I will also ensure that any sensitive data (passwords, API keys) is never printed to the logs or conversation.

## Proposed Changes

### Dashboard Application

#### [MODIFY] [app.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/__000-DASHBOARD-TEST1/app.py)
1.  **Refactor `_fetch_gcp_secret()`**:
    -   Call `gcloud secrets versions access latest` directly using `subprocess.run`.
    -   Ensure `PATH` includes the local `google-cloud-sdk/bin` if it exists.
    -   Do NOT pass `--project` explicitly, allowing `gcloud` to use its default configured project (which was verified to work in the terminal).
    -   Add silent error logging (to a file, not to the UI/terminal) for easier debugging if it fails again.
2.  **Strict Redaction**:
    -   Scan `app.py` for any `print()` or `st.write()` that might output secret values.
    -   Ensure `load_api_keys` feedback is clear but redacted (e.g., "GEMINI_API_KEY loaded: [REDACTED]").

### Cleanup
- [DELETE] Any temporary files created during secret retrieval (e.g., `/tmp/get_login_secret.py` if still exists).

## Verification Plan

### Automated/Manual Verification
1.  **Run Dashboard**: Open the dashboard at `http://localhost:8502`.
2.  **Login Test**: Enter the password (which I have securely retrieved and will enter into the browser).
3.  **Authentication Success**: Verify that successful login occurs and "Failed to fetch secret" no longer appears.
4.  **API Key Verification**: Confirm that "🔑 GEMINI_API_KEY loaded from GCP" appeared in the sidebar after login.
5.  **Log Check**: Verify that no passwords or raw keys are visible in the terminal output or browser console.
