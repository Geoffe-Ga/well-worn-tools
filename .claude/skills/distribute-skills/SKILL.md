---
name: distribute-skills
description: >-
  Push well-worn-tools skills, workflows, and multi-directory scaffolding
  bundles (e.g. the Ralph fleet loop, maintenance scans) outward to any
  target GitHub repo, opening one PR per target. Use when the user says
  "distribute skills", "push my skills to other repos", "share
  well-worn-tools across my projects", "open PRs adding skills to <repo>",
  "set up the Ralph loop in <repo>", or "propagate my skills". Honors
  metadata.distribute false in each skill's frontmatter to skip exempt
  skills (collect-skills, distribute-skills, and any other opted out);
  workflows and bundles are opt-in via explicit allowlists in distribute.py.
  Computes the missing-skill set per target, creates a feature branch
  with the new entries, commits with provenance, and opens a PR via
  Python helpers in scripts/. The agent reviews each per-repo plan before
  any push. This skill itself is exempt (metadata.distribute false). Do
  NOT use for ingesting skills FROM other repos (use collect-skills
  skill), authoring new skills (use skill-craft skill), or routine PR
  review or feedback iteration (use comprehensive-pr-review or
  address-feedback skills).
metadata:
  author: Geoff
  version: 1.0.0
  distribute: false
---

# Distribute Skills

Propagate well-worn-tools skills to sibling GitHub repos by opening one PR per target with whatever skills that repo is missing. Run from inside the well-worn-tools checkout.

## Prerequisites

- Python 3.10+.
- Working tree clean — the skill never reads from uncommitted local changes.
- For the local path: `gh` CLI authenticated, plus `git` configured to push to the owner's repos.
- For the cloud path: GitHub MCP server tools (`mcp__github__*`) with write access to each target repo.

## Execution Environment

The Python helpers shell out to `gh` and `git push`. Pick the path before doing anything:

```bash
if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || ! command -v gh >/dev/null 2>&1; then
  echo "cloud path — see 'MCP-Only Flow' at the bottom"
else
  echo "local path — Python helpers below"
fi
```

| Environment | Path |
|-------------|------|
| Claude Code CLI (terminal) | local — Python helpers, `gh` + `git push` work |
| Claude Code desktop (Mac / Windows) | local — same |
| Claude Code on the web (claude.ai/code) | cloud — MCP-only flow |
| Claude Code on iOS / mobile | cloud — same as web |

Both paths produce identical PRs. `discover.py local` is pure Python and works in either path — the exemption logic does not depend on `gh`.

## Instructions

### Step 1: Determine the GitHub Owner

```bash
python .claude/skills/distribute-skills/scripts/discover.py owner
```

### Step 2: List Distributable Local Skills

```bash
python .claude/skills/distribute-skills/scripts/discover.py local
```

Walks `.claude/skills/`, parses each frontmatter, and excludes any with `metadata.distribute: false`. By design, this skill and `collect-skills` are exempt and never appear in the output. See `references/exemption-rules.md` for the full exemption logic.

### Step 3: List Target Repos

```bash
python .claude/skills/distribute-skills/scripts/discover.py targets <owner>
```

Returns non-archived, non-fork repos. The current repo (well-worn-tools) is excluded as a target.

### Step 4: Compute the Missing Set per Target

```bash
python .claude/skills/distribute-skills/scripts/check_target.py <owner>/<repo>
```

For the given target, prints the skill names that exist locally (and are distributable) but are absent in the target's `.claude/skills/`. Empty output means the target is fully up to date.

### Step 5: Build the Per-Repo Plan

For each target with a non-empty missing set, draft the plan:

- Target repo and default branch
- List of skills to add
- Branch name (default: `add-well-worn-skills/<YYYY-MM-DD>`)
- PR title and body (the Python helper produces a draft body — review it)

Show the plan to the user before any push. If the user wants to scope down (e.g., add only one skill to one repo), update the manifest accordingly.

### Step 6: Distribute (with Confirmation)

```bash
python .claude/skills/distribute-skills/scripts/distribute.py \
    <owner>/<repo> \
    --skills <skill-1> <skill-2> ... \
    [--workflows iteration-trigger ...] \
    [--bundles ralph-loop maintenance-scans ...] \
    --branch add-well-worn-skills/$(date +%F) \
    [--dry-run]
```

The script:

1. Clones the target repo into a temporary directory at the default branch.
2. Creates the feature branch.
3. Copies each requested skill from this checkout into `.claude/skills/<skill-name>/` of the clone, refusing to overwrite if the target already has a directory by that name. If `--workflows` is set, also copies each named workflow YAML from `.github/workflows/` into the clone's `.github/workflows/`, with the same overwrite-refusal contract. If `--bundles` is set, also copies each named bundle's repo-relative files/directories (e.g. `.claude/agents/`, `scripts/ralph/`) to the same relative paths in the clone, same overwrite-refusal contract.
4. Commits with a message that names the source SHA in well-worn-tools.
5. Pushes the branch.
6. Opens a PR via `gh pr create` with a body that lists each skill, each workflow (with its dependency notes), each bundle (with the paths it adds and its dependency notes), and a link back to well-worn-tools.

`--dry-run` does steps 1-4 without pushing or opening the PR. Use it on the first target as a sanity check.

At least one of `--skills`, `--workflows`, or `--bundles` is required. Skills-only invocations are unchanged from before; workflows and bundles are additive opt-ins.

#### Distributable workflows

Workflows have no `metadata.distribute` frontmatter, so distribution is governed by an explicit allowlist in `distribute.py` (`DISTRIBUTABLE_WORKFLOWS`). Currently:

| Name | File | Purpose | Required setup in target |
|------|------|---------|--------------------------|
| `claude-code-review` | `claude-code-review.yml` | PR review that always posts, in a fixed template, with a deterministic `## Verdict: LGTM\|CHANGES_REQUESTED\|COMMENTS` line — forces structured `{verdict, verdict_rationale, review_markdown}` output via `--json-schema` instead of hoping the model remembers to comment. What `address-feedback`/`await-claude-review`/`iteration-trigger` all parse. | Repo secret `CLAUDE_CODE_OAUTH_TOKEN`; optional `RALPH_BOT_PAT`; a `CLAUDE.md` at the repo root. |
| `claude-mention` | `claude.yml` | The `@claude` mention-triggered assistant, gated to OWNER/MEMBER commenters so a public repo can't have its Claude runs triggered by arbitrary commenters. | Repo secret `CLAUDE_CODE_OAUTH_TOKEN`. |
| `iteration-trigger` | `iteration-trigger.yml` | Posts a CI / Verdict / next-action summary comment as the repo owner whenever CI completes green and a Claude review exists, to wake a Claude Code mobile session via webhook. Capped at 10 self-posts per PR. | A workflow named `CI` (so `workflow_run` matches), repo secret `RALPH_BOT_PAT` with `pull-requests: write`, and an active Claude review workflow producing comments with a `Verdict` line. |

Add a workflow to the allowlist when it's generic enough that most target repos would benefit and its dependencies can be stated up front in the PR body.

#### Distributable bundles

A **bundle** is a set of repo-relative paths (files or whole directories) that only work together — unlike a skill (one self-contained directory) or a workflow (one YAML file), these span multiple top-level directories (`.claude/agents/`, `scripts/ralph/`, `.github/workflows/`, `prompts/`) and would be a broken partial install if shipped piecemeal. Bundles have no frontmatter either, so distribution is governed by an explicit allowlist in `distribute.py` (`DISTRIBUTABLE_BUNDLES`). Currently:

| Name | What it adds | Requires |
|------|--------------|----------|
| `ralph-loop` | `.claude/agents/` (chief-architect + specialist taxonomy + `ralph-worker`), `.claude/commands/ralph-tick.md`, `scripts/ralph/` fleet mechanics (`fleet.sh`, `pick-next.sh`, `pr-ready.sh`, `FLEET.md`, `PROMPT.md`, `state.json`, tests) | Fill in the stack/threshold placeholders in `shared/house-rules.md`; `scripts/<side>/check-all.sh` must exist (see `quality-gate-scripts`); `gh` CLI; the `stay-green`/`ci-debugging`/`address-feedback` skills |
| `maintenance-scans` | The reusable scan core + all `scan-*.yml` wrappers, `deslop.yml`, `hopper.yml`, `labels-bootstrap.yml`, `.github/deslop-areas.json`, `prompts/scans/`, `prompts/templates/scan-issue-body.md`, `scripts/setup-scan-labels.sh` | The `scan-issue-writer` and `de-slopify` skills; secret `CLAUDE_CODE_OAUTH_TOKEN`; run `labels-bootstrap.yml` once after merge; edit `deslop-areas.json` for this project's real product areas |
| `dependabot-ralph-bridge` | `.github/workflows/dependabot-to-ralph-issue.yml` | The `ralph-loop` bundle; secret `RALPH_BOT_PAT` recommended |
| `quality-gate-scripts` | `scripts/backend/`, `scripts/frontend/`, `scripts/dev-setup.sh`, `scripts/pre-deploy-check.sh` | Adapt tool invocations to the target's actual stack — see `scripts/README.md` |

Add a bundle to the allowlist when a piece of scaffolding is generic enough to help most target repos but spans more than one top-level directory, so `--skills`/`--workflows` can't express it alone. The Discord merge recap is deliberately **not** a bundle — it's a self-contained skill (`discord-ralph-recap`), so it ships via `--skills` instead.

### Step 7: Verify the PR Looks Right

After distribute completes for a target, open the PR URL it printed and confirm:

- The branch contains only the intended skill directories
- The PR body lists each skill correctly
- No accidentally bundled changes to other files

If anything is off, close the PR and delete the branch before proceeding to the next target.

### Step 8: Iterate Across Targets

Repeat Steps 4-7 for each target. Do not parallelize without supervision — one PR-storm with bad metadata is worse than ten thoughtful PRs.

## Examples

### Example 1: Distribute One New Skill to All Targets

After importing `cve-remediation`, propagate it everywhere:

```bash
$ python .claude/skills/distribute-skills/scripts/discover.py targets Geoffe-Ga
Geoffe-Ga/another-tool
Geoffe-Ga/some-service
$ for target in Geoffe-Ga/another-tool Geoffe-Ga/some-service; do
    missing=$(python .claude/skills/distribute-skills/scripts/check_target.py "$target")
    if echo "$missing" | grep -q '^cve-remediation$'; then
      python .claude/skills/distribute-skills/scripts/distribute.py \
          "$target" --skills cve-remediation --dry-run
    fi
  done
$ # Review dry-run output, then re-run without --dry-run for each target.
```

### Example 2: Bring a Single Cold Repo Up to Date

```bash
$ python .claude/skills/distribute-skills/scripts/check_target.py Geoffe-Ga/some-service
ci-debugging
cve-remediation
security
stay-green
testing
$ python .claude/skills/distribute-skills/scripts/distribute.py \
      Geoffe-Ga/some-service \
      --skills ci-debugging cve-remediation security stay-green testing \
      --branch bootstrap-well-worn-skills
```

One PR introducing five skills is fine if the target is empty. Split across PRs if a single PR would obscure review.

### Example 3: Distribute the iteration-trigger Workflow

Pair the workflow with the address-feedback skill so the target repo has both halves of the loop (the nudge that wakes the session and the playbook the session follows):

```bash
$ python .claude/skills/distribute-skills/scripts/distribute.py \
      Geoffe-Ga/some-service \
      --skills address-feedback \
      --workflows iteration-trigger \
      --branch add-iteration-trigger/$(date +%F) \
      --dry-run
```

The dry-run prints the planned commit; remove `--dry-run` once the PR plan looks right. The PR body lists the workflow's required secret (`RALPH_BOT_PAT`) and the dependency on a `CI` workflow as a checklist item for the maintainer.

### Example 4: Upgrade a Repo's Claude Review to the Deterministic Version

A target repo that already has *some* Claude PR-review workflow (e.g. the default plugin-based one) is exactly the "target already has the file" case — `distribute` refuses to overwrite it, so the maintainer replaces it by hand:

```bash
$ python .claude/skills/distribute-skills/scripts/distribute.py \
      Geoffe-Ga/some-service \
      --workflows claude-code-review claude-mention \
      --branch upgrade-claude-review/$(date +%F) \
      --dry-run
ERROR: target already has .github/workflows/claude-code-review.yml — refuse to overwrite.
```

Have the maintainer delete (or rename) their existing `claude-code-review.yml` first, then re-run without `--dry-run`. The new one posts a fixed-template review and a deterministic `## Verdict:` line every time — the thing `address-feedback` and `await-claude-review` are built to parse — instead of whatever shape a plugin-based review happens to produce.

### Example 5: Refuse to Overwrite

```bash
$ python .claude/skills/distribute-skills/scripts/distribute.py \
      Geoffe-Ga/some-service --skills security --dry-run
ERROR: target already has .claude/skills/security/ — refuse to overwrite.
Hint: use collect-skills to compare versions, or pick a different skill.
```

If the target has its own version of a skill, the right path is `collect-skills` (pull theirs in, diff, decide), not blind overwrite.

## Troubleshooting

### Error: gh CLI not authenticated
Run `gh auth login` and re-run. Pushing branches and opening PRs both need an authenticated session.

### Error: Target already has the skill
Distribute refuses to overwrite. Use `collect-skills` to ingest the target's version, diff, decide, and only then propagate the agreed-on canonical version. Distribute is for additive PRs only.

### Error: Skill marked distributable that should be exempt
Add `metadata.distribute: false` to the skill's frontmatter. The exemption is per-skill in source, not a separate config file, so it travels with the skill if it's ever moved.

### Error: PR body is too generic
The default body lists each skill's name and description. Edit the PR after creation if the target audience needs more context — but improving the source skill's description usually helps every future PR.

### Error: A target needs additional setup files (e.g. CI hooks)
Distribute deliberately ships only `.claude/skills/<name>/`. If the skills depend on a missing harness, add a checklist to the PR body so the target maintainer knows. Do not silently bundle unrelated config.

## MCP-Only Flow (Cloud Environments)

When `gh` and local `git push` are unavailable, drive the same workflow through GitHub MCP tools. The agent does the orchestration; no clone is needed because `mcp__github__push_files` writes directly to a remote branch in one commit.

| Step | Local helper | MCP equivalent |
|------|--------------|----------------|
| 1. Owner | `discover.py owner` | Read `git remote get-url origin` via Bash; parse owner. (No GitHub call needed.) |
| 2. Local skills | `discover.py local` | Same — pure Python, no `gh`. |
| 3. Targets | `discover.py targets <owner>` | `mcp__github__search_repositories` with query `user:<owner>` (or `org:<owner>`); filter archived, forks, and well-worn-tools in the agent. |
| 4. Diff target | `check_target.py <owner>/<repo>` | `mcp__github__get_file_contents` on the target's `.claude/skills` path; intersect with the local list to compute missing names. |
| 5. Plan | (agent builds in-context) | Same — pure context work. |
| 6. Distribute | `distribute.py ... [--dry-run]` | (a) `mcp__github__create_branch` on the target. (b) Read each local skill's files with the `Read` tool, plus `.github/workflows/<file>.yml` for any selected workflow, plus every path listed in `DISTRIBUTABLE_BUNDLES[<name>]` (recursing into directories) for any selected bundle. (c) `mcp__github__push_files` once per target with all files for all selected skills, workflows, and bundles, including a commit message that names the source SHA. (d) `mcp__github__create_pull_request` with title and body — include the workflow/bundle dependency checklist (PAT, `CI` workflow name, required skills/secrets) in the body. |
| 7. Verify | Open PR URL | Same — open the URL the MCP call returns. |

The `--dry-run` semantics in cloud are: stop after step (b), report the file list and intended commit/PR text, and do not call `create_branch` or `push_files`. Implement this in the agent's plan, not in code.

`push_files` refuses to overwrite if the path already exists in the target. That preserves the same overwrite-refusal contract `distribute.py` enforces — if a target already has the skill, fall back to `collect-skills`.

## See Also

- `references/exemption-rules.md` — full logic for which skills are excluded and why
- `.claude/skills/collect-skills/` — the inverse skill for ingesting from other repos
- `.claude/skills/skill-craft/` — quality bar each distributed skill should already meet
