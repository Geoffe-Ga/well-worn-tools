---
name: distribute-skills
description: >-
  Push well-worn-tools skills outward to every sibling GitHub repo owned
  by the same user or org that does not already have them, opening one PR
  per target. Use when the user says "distribute skills", "push my skills
  to other repos", "share well-worn-tools across my projects", "open PRs
  adding skills to <repo>", or "propagate my skills". Honors
  metadata.distribute false in each skill's frontmatter to skip exempt
  skills (collect-skills, distribute-skills, and any other opted out).
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

- `gh` CLI authenticated for the current owner (`gh auth status`).
- `git` configured to push to the owner's repos (SSH or HTTPS with credentials).
- Python 3.10+.
- Working tree clean — the skill never reads from uncommitted local changes.

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
    --branch add-well-worn-skills/$(date +%F) \
    [--dry-run]
```

The script:

1. Clones the target repo into a temporary directory at the default branch.
2. Creates the feature branch.
3. Copies each requested skill from this checkout into `.claude/skills/<skill-name>/` of the clone, refusing to overwrite if the target already has a directory by that name.
4. Commits with a message that names the source SHA in well-worn-tools.
5. Pushes the branch.
6. Opens a PR via `gh pr create` with a body that lists each skill, its purpose (from frontmatter description), and a link back to well-worn-tools.

`--dry-run` does steps 1-4 without pushing or opening the PR. Use it on the first target as a sanity check.

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

### Example 3: Refuse to Overwrite

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

## See Also

- `references/exemption-rules.md` — full logic for which skills are excluded and why
- `.claude/skills/collect-skills/` — the inverse skill for ingesting from other repos
- `.claude/skills/skill-craft/` — quality bar each distributed skill should already meet
