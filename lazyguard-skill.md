---
description: How to validate completed tasks and use the LazyGuard MVP.
---

# LazyGuard MVP - Worker Agent Skill

As a worker agent, you do **not** determine when a task is complete. A separate validation script called "LazyGuard" evaluates your work based on determinable criteria (files existing, precise content, passing tests).

Whenever you think you have finished all objectives of a task, you **MUST** run the validation command and read the resulting report.

## The Validation Workflow

### 1. Execute Your Task

Perform your standard work inside the `project_path` defined for your current task.

### 2. Run the Validator

When you believe you are done, do not simply report success to the user. Instead, run the validator script against your task JSON.

```bash
python validator.py task.json
```

### 3. Read the Report

The script will output a file named `report.json`.
You must wait for the script to finish and then read `report.json` to inspect the results.

### 4. Interpret the Result

The `report.json` will contain a `"status"` key and an array of `"reasons"`.

- **If `status` is `"FAIL"` or `"PARTIAL"`:**
  Your work is **NOT DONE**.
  Read the `"reasons"` array to see exactly what failed (e.g., "Missing required file: src/components/Header.tsx" or "Test command failed").
  **Action:** Keep working. Fix the issues and re-run the validator (go back to Step 1). Do not notify the user until you have a PASS.

- **If `status` is `"PASS"`:**
  Your work is complete and independently verified.
  **Action:** You may now safely report to the user that the task is complete.

## Strict Rules

- Do not overwrite or modify `validator.py`.
- Do not overwrite or modify `task.json` (unless explicitly instructed to by the user).
- Your goal is to satisfy the determinable rules in `task.json`, not just your internal judgment of completion.
