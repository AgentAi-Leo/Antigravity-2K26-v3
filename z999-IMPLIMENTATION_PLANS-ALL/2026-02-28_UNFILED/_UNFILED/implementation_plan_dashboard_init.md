# Local Web Dashboard for Antigravity Skills

We will build a lightweight, local web interface that scans the `___000A-ANTIGRAVITY-SKILLS` directory, reads what skills are available, and generates a UI allowing you to execute them via the browser.

## User Review Required
> [!IMPORTANT]
> **Framework Choice:** To make this fast, modern, and beautiful, I propose using **Streamlit**. Streamlit is a Python library that lets us build a sleek web dashboard in ~100 lines of code without writing separate HTML/CSS/JS. It's perfect for internal AI tools. Is Streamlit okay with you, or would you prefer a classic Flask + HTML/Tailwind app?

> [!CAUTION]
> **Security:** This dashboard will execute shell commands on your local machine. It will run on `localhost` (only accessible from your Mac). We must ensure it is never exposed to the public internet securely.

## Proposed Changes

### `__000-DASHBOARD-TEST1`
I will create a new folder specifically for the dashboard app.

#### [NEW] [app.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/__000-DASHBOARD-TEST1/app.py)
This will be the main Streamlit application. It will:
1. **Login Page**: Display a password input box.
    - When submitted, it will use Python `subprocess` to call the local `000C-SKILL_SECURITY-GCSecrtMgr` script to fetch the real `dev-test-1` secret value (using `--get`).
    - If the user input matches the GCP secret, it will set an authenticated flag in Streamlit's `st.session_state` and reveal the main dashboard.
2. **Dashboard**: Scan the root directory for all folders containing a `SKILL.md`.
3. Parse the YAML frontmatter in `SKILL.md` to get the skill name and description.
4. Parse the `scripts/*.py` file to find `argparse` definitions so it knows what text boxes/inputs to render for the user.
5. Provide a "Run" button that triggers the Python script using `subprocess` and streams the console output back into the web UI.

#### [NEW] [requirements.txt](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/__000-DASHBOARD-TEST1/requirements.txt)
Will contain `streamlit` and `pyyaml` (for frontmatter parsing).

## Verification Plan

### Automated Tests
- Run `python3 -m py_compile __000-DASHBOARD-TEST1/app.py` to ensure syntax is valid.

### Manual Verification
1. I will install `streamlit` on your machine.
2. I will boot up the dashboard server using `streamlit run __000-DASHBOARD-TEST1/app.py`.
3. You will navigate to `http://localhost:8501` in your browser.
4. We will verify that a lock screen appears and rejects incorrect passwords.
5. We will verify that entering the true value of `dev-test-1` unlocks the dashboard.
6. We will do a live test by running `Convtr-PlainTxt2PDF` directly from the unlocked web interface.
