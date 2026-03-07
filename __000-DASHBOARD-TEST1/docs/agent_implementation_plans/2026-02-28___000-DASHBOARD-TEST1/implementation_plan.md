# Implementation Plan: High-Fidelity Emoji Keycap Rendering

The user is experiencing "Digit + Grey Square" rendering for keycap emojis (1️⃣, 2️⃣, 3️⃣) in generated PDFs. This happens because the automatic font fallback splits the sequence into two different font runs (Noto Sans for the digit, Noto Emoji for the keycap), which prevents the HarfBuzz shaper from combining them.

## Proposed Changes

### PDF Generator

#### [MODIFY] [plain_txt2pdf.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/Convtr-PlainTxt2PDF/scripts/plain_txt2pdf.py)

1.  **Manual Fragmenter**: Implement a custom line-rendering function that uses Regex to tokenize strings into "Plain Text" and "Emoji Clusters" (specifically targeting keycaps like `[0-9#*]\ufe0f?\u20e3`).
2.  **Unitary Font Runs**: Ensure that each identified "Emoji Cluster" is rendered in a single `pdf.write()` call using the **Noto Emoji** font, while surrounding text uses **Noto Sans**.
3.  **Remove Automatic Fallback**: Disable the unreliable `set_fallback_fonts` which is causing the fragmentation, and instead rely on this surgical manual fragmentation.

## Verification Plan

### Automated Tests
1. Generate a PDF from `Consistency_SAMSON.rtf`.
2. Verify that 1️⃣, 2️⃣, and 3️⃣ are rendered as single, solid icons.

### Manual Verification
1. Ask the user to verify the PDF download from the dashboard.
