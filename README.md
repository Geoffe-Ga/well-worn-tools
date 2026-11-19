# Well-Worn Tools

A curated collection of Claude Code skills for software engineering excellence, plus project scaffolding for an autonomous, quality-gated development loop (the "Ralph" fleet loop, scheduled maintenance scans, and quality-gate scripts). Each skill follows Anthropic's production skill format with YAML frontmatter, progressive disclosure, and optimized triggering.

## Skills

| Skill | Description |
|-------|-------------|
| **address-feedback** | Act on the latest Claude review `Verdict:` for the current HEAD (trusted only from allowlisted, unedited comments): `LGTM` merges on green CI, `COMMENTS` files each finding as a P0–P3 follow-up issue then merges (never iterates), `CHANGES_REQUESTED` loops through TDD fixes |
| **architectural-decisions** | Structured trade-off analysis for choosing between libraries, patterns, and technologies |
| **await-claude-review** | Subscribe to PR activity and wait — without polling — for the Claude reviewer's verdict comment on the current HEAD |
| **backlog-grooming** | Systematic GitHub backlog maintenance: review PRs, close issues, identify gaps |
| **bug-squashing-methodology** | 6-step bug fix process — reproduce first, then root cause analysis and TDD |
| **ci-debugging** | Debug CI test failures with structured protocol |
| **collect-skills** | Discover and ingest skills from sibling GitHub repos owned by the same user/org, with adaptation pass to fit well-worn-tools (`metadata.distribute: false`) |
| **comprehensive-pr-review** | 10-section PR review covering security, quality, testing, and docs |
| **concurrency** | Safe concurrent code patterns across Python, TypeScript, Go, and Rust |
| **continue-epic** | Pick up the next incomplete issue from a local file-based roadmap (`prompts/github-issues/`) and drive it to a merge-ready PR via TDD — a lighter-weight alternative to the Ralph loop for projects without a GitHub-issue backlog |
| **cve-remediation** | Remediate dependency vulnerability scanner failures by verifying live registry data and upgrading; suppression is a documented last resort |
| **de-slopify** | Audit the codebase for sloppy, amateurish, or AI-generated low-quality code and file corroborated findings as Ralph-ready GitHub issues |
| **decide** | Turn a prompt into an interactive HTML decision sheet — options, trade-off matrix, costs, risks, examples — whose answers hand back to Claude in one paste |
| **discord-ralph-recap** | Post a beautifully formatted Ralph tick-loop recap to Discord on every merged PR — merge rate, review iterations to LGTM, backlog ETA, and a ten-word "what this unlocked" headline |
| **distribute-skills** | Push well-worn-tools skills, workflows, and multi-directory scaffolding bundles (e.g. the Ralph loop) outward to any target repo via per-target PRs (`metadata.distribute: false`) |
| **documentation** | Language-specific documentation patterns for docstrings, module docs, and API references |
| **error-handling** | Robust error handling that fails fast with clear diagnostics |
| **file-naming-conventions** | ISO 8601 date-prefix naming for documents and plans |
| **flare** | One-shot bug/feature reporting: research the repo, write a code-grounded, agent-ready ticket, dedupe, and file it in a single turn |
| **frontend-aesthetics** | Polished, accessible frontend UI with design tokens and semantic HTML |
| **graph** | Answer codebase questions from a `graphify` knowledge graph (query, path, explain, affected) before sweeping files by hand |
| **max-quality-no-shortcuts** | Anti-bypass philosophy: fix root causes instead of adding `noqa` / `type: ignore` |
| **mutation-testing** | Write high-value tests that kill mutants through logic validation |
| **preflight** | Run the full pre-commit suite, diagnose every failure, and iterate until all hooks pass green |
| **prompt-engineering** | Transform vague requests into effective 6-component prompts |
| **quick-test** | Run only the test suite relevant to what changed, for rapid local iteration |
| **review-diff** | Thorough self-review of the current branch's changes against its issue/spec before opening a PR |
| **scan-issue-writer** | Run a named codebase maintenance scan and convert findings into 6-component, agent-ready GitHub issues, with dedupe and priority labeling |
| **security** | Secure coding practices against OWASP top 10 across four languages |
| **skill-craft** | Meta-skill for building and validating production-quality skills |
| **spec-decomposition** | Decompose a SPEC / PRD / RFC into sequenced GitHub epics and prompt-shaped child issues, written to `git-issues/` and filed with `gh issue create --body-file` |
| **status** | Quick, actionable snapshot of where a local file-based roadmap stands |
| **stay-green** | Graduated local quality ladder: targeted tests on every Red-Green-Refactor cycle, then `./scripts/check-all.sh` (or `pre-commit run --all-files`) once before pushing |
| **testing** | Comprehensive test writing with TDD, AAA pattern, and language-specific frameworks |
| **tracer-code** | Incremental system building: wire the skeleton first, then replace stubs |
| **triage-and-plan** | Deep multi-dimensional codebase analysis that generates a structured epic of local issue files |
| **ultracode** | Autonomous multi-agent backlog drain that works the whole open backlog in priority waves and re-arms its own wake every turn |
| **user-facing-error-messages** | Audit and rewrite user-facing error messages so users can self-serve instead of emailing support |
| **vibe** | Code style, naming conventions, and structural patterns for consistent codebases |
| **walkthrough** | Hand-hold the user through a human-only ops/console ticket one verified, gated block at a time |

## Project scaffolding

Beyond skills, this repo ships an opinionated, drop-in scaffold for an autonomous, quality-gated development loop — distributed to other repos via `distribute-skills`' `--bundles` flag (see that skill for the full bundle list and setup requirements).

| Bundle | Adds | What it's for |
|--------|------|----------------|
| `ralph-loop` | `.claude/agents/` (chief-architect + 6 specialists + `ralph-worker`), `.claude/commands/ralph-tick.md`, `scripts/ralph/` fleet mechanics | A re-entrant orchestrator that keeps up to `max_workers` git-worktree lanes moving independently through TDD → local quality gate → CI → Claude review → merge |
| `maintenance-scans` | `.github/workflows/scan-*.yml` + `deslop.yml` + `hopper.yml` + `prompts/scans/` | Scheduled read-only scans (bugs, security, perf, coverage, dead code, types, docs, complexity, mutation, deps, a11y, groom) and a weekly de-slop code-quality audit, filing agent-ready issues so the Ralph backlog never starves or floods |
| `dependabot-ralph-bridge` | `.github/workflows/dependabot-to-ralph-issue.yml` | Bridges Dependabot's PR-only model into the Ralph loop's issue-first picker |
| `quality-gate-scripts` | `scripts/backend/`, `scripts/frontend/`, `dev-setup.sh`, `pre-deploy-check.sh` | Starting-template lint/format/typecheck/security/test/coverage scripts for a Python backend + TypeScript frontend monorepo |

For the Discord merge recap itself, use the **`discord-ralph-recap` skill** directly (`--skills discord-ralph-recap` in `distribute-skills`) rather than a bundle — it's already a self-contained skill.

Every bundle ships with generic placeholders (a stack description in `.claude/agents/shared/house-rules.md`, example product areas in `.github/deslop-areas.json`) that a target project fills in with its own conventions — see each bundle's `Requires` notes.

## Installation

### Claude Code

Copy the `.claude/skills/` directory into your project:

```bash
cp -r .claude/skills/ /path/to/your/project/.claude/skills/
```

Or symlink individual skills:

```bash
ln -s /path/to/well-worn-tools/.claude/skills/stay-green /path/to/your/project/.claude/skills/stay-green
```

### Claude.ai

Zip any skill folder and upload via **Settings > Capabilities > Skills**.

## Structure

Each skill follows the standard directory format:

```
skill-name/
├── SKILL.md          # Core instructions (always loaded when relevant)
├── references/       # Detailed docs loaded on demand (optional)
├── scripts/          # Executable tooling (optional)
└── assets/           # Templates, fonts, icons (optional)
```

Skills use three levels of progressive disclosure:

1. **YAML frontmatter** — always in system prompt; tells Claude *when* to use the skill
2. **SKILL.md body** — loaded when relevant; contains full instructions
3. **references/** — loaded on demand; detailed patterns, examples, templates

## License

MIT
