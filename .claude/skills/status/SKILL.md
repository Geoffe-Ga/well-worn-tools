---
name: status
description: >-
  Give a quick, actionable snapshot of where a local file-based roadmap
  (`prompts/github-issues/`) stands — phase completion, current branch,
  uncommitted changes, recently completed work. Use when the user says
  "status", "where are we", "what's done", "project status", or "progress" in
  a project that plans work as local phase files. Do NOT use for a project
  whose backlog lives in GitHub issues (use `gh issue list` / backlog-grooming
  instead), or for driving the next issue to a PR (use `continue-epic`).
metadata:
  author: Geoff
  version: 1.0.0
---
# Status

Give a quick, actionable snapshot of where the project stands. Designed for the
phone interface — concise output, no fluff.

---

## Trigger

Activate when the user says any of:
- "status"
- "where are we"
- "what's done"
- "project status"
- "progress"

---

## Instructions

### 1. Check Roadmap Progress

Read `prompts/github-issues/README.md` to get the full issue list.

### 2. Check Git State

```bash
git log --oneline --all -30
git branch -a
git status
```

### 3. Cross-Reference Completion

For each phase, determine how many issues are complete by checking:
- Merged branches matching issue slugs
- Commit messages referencing issues
- Codebase state (does the code exist and work?)

### 4. Report

Output a compact status table:

```
## Project Status

| Phase | Done | Total | Status |
|-------|------|-------|--------|
| 1     | 3/11 |  11   | In progress |
| 2     | 0/7  |   7   | Blocked by P1 |
| 3     | 0/14 |  14   | Blocked by P1 |
| 4     | 0/8  |   8   | Can start after P1 |

**Next up:** phase-1-04: Practice router -> DB
**Current branch:** phase-1-03-auth-router-to-db
**Uncommitted changes:** 3 files modified

**Recently completed:**
- phase-1-01: Database setup + Alembic
- phase-1-02: Habits router -> DB
- phase-1-03: Auth router -> DB + JWT
```

Keep it short. The user is on their phone — they want a glance, not a novel.
