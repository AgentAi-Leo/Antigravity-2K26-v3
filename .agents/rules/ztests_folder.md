---
description: Auto-create ztests folder for skills and store test files inside
---

# Global Rule: ztests Folder for Skills

Whenever you generate or initialize a new skill, you **MUST automatically** create a folder named `ztests` within the skill's root directory.

1. **Folder Creation**: Ensure the path `<SkillDirectory>/ztests/` is created when setting up the skill's folder structure.
2. **Test File Location**: Any file that acts as a test script (e.g. `test_*.py`, API test scripts) or any test input/output data (e.g. `test_audio.mp3`, `test_transcript.txt`, `sample_output.pdf`) **MUST** be saved inside this `ztests` directory.
3. **Keep Root Clean**: Do not leave ad-hoc test files or scripts in the root of the skill directory. Everything related to testing should be kept organized within `ztests`.

This guarantees that the skill's root directory remains clean and test files are logically grouped together out of the main execution paths.
