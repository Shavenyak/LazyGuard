# LazyGuard: The Agent Gatekeeper 🛡️

**LazyGuard** is a deterministic validator and gatekeeper for AI worker agents. It ensures that an agent cannot mark a task as "complete" based on its own judgment alone. Instead, completion is only granted once the agent provides verifiable evidence (files, content, and passing tests) that satisfy the rules you define.

---

## 🚀 What is the use of LazyGuard?

AI agents are sometimes "lazy" or prone to hallucinations—they might claim a task is done when they've actually missed a file, forgotten a specific requirement, or didn't actually run the tests.

**LazyGuard** solves this by:

1.  **Enforcing Evidence:** The agent _must_ run the validator script to finish.
2.  **Deterministic Checking:** No LLM "vibes" here. We check if the file exists, if the exact string is there, and if the test command exited with `0`.
3.  **Self-Correction Loop:** If the agent fails, it reads a structured `report.json` and fixes its own mistakes before ever bothering the user.

---

## 🛠️ The Three Stages of a LazyGuard Task

### 1. Definition (The User)

You define exactly what success looks like in `task.json`.

```json
{
  "task_id": "002",
  "project_path": "./my_app",
  "required_files": ["src/App.js"],
  "must_contain_checks": [{ "file": "src/App.js", "text": "Welcome" }],
  "test_command": "npm test"
}
```

### 2. Execution (The Agent)

The worker agent performs the coding work. Crucially, the agent follows the `lazyguard-skill.md`, which defines its internal rules:

- "I am not done until LazyGuard says I am."
- "If I fail, I must read the `reasons` and fix them."

### 3. Verification (The Gatekeeper)

The agent runs `python validator.py task.json`.

- **FAIL:** Agent stays in the loop.
- **PASS:** Agent is released from the task and reports victory to the user.

---

## 📂 Project Structure

- `validator.py`: The core logic that performs file, content, and test checks.
- `lazyguard-skill.md`: The instruction set (Skill) you give to your AI agent.
- `task.json`: Your requirement specification.
- `report.json`: The generated "proof of work" containing logs and exit codes.

---

## 🛸 Future Road Map

- [ ] **MCP Integration:** Wrap this in a Model Context Protocol tool for native agent support.
- [ ] **LLM Judge Option:** Add an optional branch for "Quality" checks using a cheaper LLM.
- [ ] **Dashboard:** A simple UI to see a history of agent "Lazy" attempts vs successful passes.

---

### How to Run

```bash
python validator.py task.json
```

Check the output in `report.json` to see the results.
