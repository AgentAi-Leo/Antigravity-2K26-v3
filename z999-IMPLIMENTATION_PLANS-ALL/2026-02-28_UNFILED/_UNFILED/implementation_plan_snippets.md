# Implementation Plan: Allow Snippet Injection in Login

The user is unable to use Raycast snippets in the login window. This is caused by macOS **Secure Input Mode**, which is automatically triggered by `<input type="password">` to prevent third-party apps from seeing or injecting text.

## Proposed Changes

### Dashboard Application

#### [MODIFY] [app.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/__000-DASHBOARD-TEST1/app.py)

1.  **Add Visibility Toggle**: Introduce a checkbox or toggle labeled "Allow Snippets (Unmasks Field)" inside the login form.
2.  **Dynamic Input Type**: Update the `st.text_input` call to use `type="default"` when the toggle is enabled, and `type="password"` when disabled.
3.  **Explain the Feature**: Add a small note or tooltip explaining that this disables macOS Secure Input so tools like Raycast can work.

## Verification Plan

### Manual Verification
1. Open the dashboard login page.
2. Try using a Raycast snippet in the password field (it should fail).
3. Check the "Allow Snippets" box.
4. Try the Raycast snippet again (it should now successfully inject the text).
5. Uncheck the box and verify it returns to a secure password field.
