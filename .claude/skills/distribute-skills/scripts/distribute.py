#!/usr/bin/env python3
"""Open a PR on a target repo that adds the requested local skills, workflows,
and/or scaffolding bundles.

Usage:
    distribute.py <owner>/<repo>
        [--skills <name> [<name> ...]]
        [--workflows <name> [<name> ...]]
        [--bundles <name> [<name> ...]]
        [--branch <branch-name>]
        [--source-skills-dir <path>]
        [--source-workflows-dir <path>]
        [--source-repo-root <path>]
        [--dry-run]

At least one of --skills, --workflows, or --bundles must be provided.

Behavior:
  1. Clones the target repo into a temporary directory at its default branch.
  2. Creates the feature branch.
  3. Copies each requested skill from <source-skills-dir> into the clone, each
     requested workflow from <source-workflows-dir> into the clone's
     `.github/workflows/`, and each requested bundle's files/directories from
     <source-repo-root> to the same relative paths in the clone. Refuses to
     overwrite any existing target path.
  4. Commits with provenance referencing the local well-worn-tools HEAD SHA.
  5. Pushes the branch and opens a PR via `gh pr create`.

`--dry-run` performs steps 1-4 only and prints what would happen, without
pushing or opening the PR. Always dry-run the first target.

Distributable workflows and bundles are governed by the DISTRIBUTABLE_WORKFLOWS
/ DISTRIBUTABLE_BUNDLES allowlists below, not by frontmatter (workflow YAML and
plain scripts/prompts have none). Add an entry when it is generic enough to be
useful in most target repos.
"""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_SOURCE_DIR = Path(".claude/skills")
DEFAULT_WORKFLOWS_SOURCE_DIR = Path(".github/workflows")
DEFAULT_REPO_ROOT = Path(".")
DEFAULT_BRANCH_PREFIX = "add-well-worn-skills"
GH_MISSING_HINT = (
    "error: `gh` CLI not found. In Claude Code cloud environments (web / iOS), "
    "`gh` and local `git push` are not available — use the MCP-Only Flow at the "
    "bottom of SKILL.md (mcp__github__create_branch + push_files + create_pull_request)."
)

# Allowlist of workflows distribute can ship into target repos. Each entry maps
# the public name (used on the --workflows CLI) to the YAML filename inside the
# source workflows dir, plus prose used in the PR body so the maintainer knows
# what the workflow does and what setup it needs.
DISTRIBUTABLE_WORKFLOWS: dict[str, dict[str, str]] = {
    "claude-code-review": {
        "filename": "claude-code-review.yml",
        "summary": (
            "PR-review workflow that always posts, always in the same shape, and "
            "always ends with a machine-parseable verdict. Uses the action's "
            "`--json-schema` flag to force a structured `{verdict, "
            "verdict_rationale, review_markdown}` result — the review body "
            "follows a fixed template (Summary / Strengths / Security Concerns / "
            "Problems / Code Quality / CLAUDE.md Adherence / Testing / "
            "Documentation) instead of whatever shape the model felt like that "
            "run — and a deterministic 'Post review' step appends the exact "
            "`## Verdict: LGTM|CHANGES_REQUESTED|COMMENTS` line and posts it "
            "itself, so a review is never silently skipped (the classic failure "
            "mode of letting the model remember to comment). This is what "
            "`address-feedback`, `await-claude-review`, and `iteration-trigger` "
            "all parse — replaces a repo's existing Claude PR-review workflow "
            "with this one for consistent, automation-friendly verdicts."
        ),
        "requires": (
            "(a) repo secret `CLAUDE_CODE_OAUTH_TOKEN`; "
            "(b) optional repo secret `RALPH_BOT_PAT` (falls back to "
            "`GITHUB_TOKEN`/github-actions[bot]) so the verdict comment posts "
            "under a real account other automation (e.g. `iteration-trigger`) "
            "can recognize; (c) a `CLAUDE.md` at the repo root — the review is "
            "scored against it."
        ),
    },
    "claude-mention": {
        "filename": "claude.yml",
        "summary": (
            "The `@claude` mention-triggered assistant (issue/PR comments and "
            "reviews), gated so only the repo OWNER or a MEMBER can invoke it — "
            "without this gate, anyone who can comment on a public repo's issue "
            "or PR can trigger a paid Claude run."
        ),
        "requires": ("repo secret `CLAUDE_CODE_OAUTH_TOKEN`."),
    },
    "iteration-trigger": {
        "filename": "iteration-trigger.yml",
        "summary": (
            "Posts a brief CI / Claude-verdict / next-action summary comment "
            "(as the repo owner via PAT) whenever CI completes fully green and "
            "a Claude review comment exists, capped at 10 self-posts per PR. "
            "Designed to wake a Claude Code mobile session via webhook so it "
            "can keep iterating on review feedback."
        ),
        "requires": (
            "(a) a workflow named `CI` in the target repo so the "
            "`workflow_run` trigger matches; "
            "(b) repo secret `RALPH_BOT_PAT` — a PAT with "
            "`pull-requests: write` so the comment posts under the owner's "
            "identity rather than github-actions[bot]; "
            "(c) an active Claude review workflow whose comments include a "
            "`Verdict` line (see `claude-code-review.yml` upstream)."
        ),
    },
}

# Allowlist of multi-file/multi-directory scaffolding bundles distribute can
# ship into target repos. Unlike --skills (one self-contained directory) and
# --workflows (one YAML file), a bundle is a set of repo-relative paths
# (files or directories) that only work together — e.g. the Ralph fleet loop
# spans .claude/agents/, .claude/commands/, and scripts/ralph/ at once, so
# shipping any one piece alone would be a broken partial install.
#
# Each entry: `paths` (repo-relative, file or directory, copied recursively),
# `summary` (what it does, for the PR body), and `requires` (setup the target
# maintainer must do — secrets, sibling bundles/skills, or files to author).
DISTRIBUTABLE_BUNDLES: dict[str, dict[str, object]] = {
    "ralph-loop": {
        "paths": [
            ".claude/agents",
            ".claude/commands/ralph-tick.md",
            "scripts/ralph/FLEET.md",
            "scripts/ralph/PROMPT.md",
            "scripts/ralph/fleet.sh",
            "scripts/ralph/pick-next.sh",
            "scripts/ralph/pr-ready.sh",
            "scripts/ralph/state.json",
            "scripts/ralph/test_fleet.sh",
            "scripts/ralph/test_pick_next.sh",
            "scripts/ralph/test_pr_ready.sh",
        ],
        "summary": (
            "The Ralph fleet loop: a re-entrant orchestrator (`/ralph-tick`) that "
            "keeps up to `max_workers` git-worktree lanes moving independently "
            "through TDD -> local quality gate -> CI -> Claude review -> merge, "
            "dispatching the chief-architect + specialist subagent taxonomy in "
            "`.claude/agents/` per lane."
        ),
        "requires": (
            "(a) fill in the stack/thresholds placeholders in "
            "`.claude/agents/shared/house-rules.md` for this project; "
            "(b) `scripts/backend/check-all.sh` and/or `scripts/frontend/check-all.sh` "
            "must exist (see the `quality-gate-scripts` bundle for a starting "
            "template); (c) `gh` CLI authenticated for the picker and fleet "
            "reconciliation; (d) the `stay-green`, `ci-debugging`, and "
            "`address-feedback` skills (already in well-worn-tools) for the "
            "gate drop-back flows."
        ),
    },
    "maintenance-scans": {
        "paths": [
            ".github/workflows/_claude-scan.yml",
            ".github/workflows/scan-a11y.yml",
            ".github/workflows/scan-bugs.yml",
            ".github/workflows/scan-complexity.yml",
            ".github/workflows/scan-coverage.yml",
            ".github/workflows/scan-dead-code.yml",
            ".github/workflows/scan-deps.yml",
            ".github/workflows/scan-docs.yml",
            ".github/workflows/scan-groom.yml",
            ".github/workflows/scan-mutation.yml",
            ".github/workflows/scan-perf.yml",
            ".github/workflows/scan-security.yml",
            ".github/workflows/scan-todo.yml",
            ".github/workflows/scan-types.yml",
            ".github/workflows/deslop.yml",
            ".github/workflows/hopper.yml",
            ".github/workflows/labels-bootstrap.yml",
            ".github/deslop-areas.json",
            "prompts/scans",
            "prompts/templates/scan-issue-body.md",
            "scripts/setup-scan-labels.sh",
        ],
        "summary": (
            "Scheduled, read-only maintenance scans (todo/bugs/security/perf/"
            "coverage/dead-code/types/docs/complexity/mutation/deps/a11y/groom) "
            "that file deduplicated, agent-ready GitHub issues via the "
            "`scan-issue-writer` skill, plus a weekly de-slop code-quality audit "
            "(`de-slopify` skill) and an hourly queue-depth hopper so the backlog "
            "never starves or floods."
        ),
        "requires": (
            "(a) the `scan-issue-writer` and `de-slopify` skills "
            "(`distribute-skills ... --skills scan-issue-writer de-slopify`); "
            "(b) repo secret `CLAUDE_CODE_OAUTH_TOKEN`; "
            "(c) run `labels-bootstrap.yml` once after merge to create the "
            "P0-P3 / agent-ready / scan:<name> labels; "
            "(d) edit `.github/deslop-areas.json` to describe this project's "
            "actual product areas (it ships with two generic placeholder "
            "entries)."
        ),
    },
    "dependabot-ralph-bridge": {
        "paths": [
            ".github/workflows/dependabot-to-ralph-issue.yml",
        ],
        "summary": (
            "Bridges Dependabot's PR-only model into the Ralph loop: files a "
            "`dependencies`-labeled issue for each open Dependabot PR and links "
            "it via `Closes #N` so `pick-next.sh` and the fleet orchestrator "
            "adopt it like any other backlog item."
        ),
        "requires": (
            "(a) the `ralph-loop` bundle (this only makes sense with a Ralph "
            "loop picking up the linked issues); (b) repo secret `RALPH_BOT_PAT` "
            "recommended (falls back to `GITHUB_TOKEN` otherwise)."
        ),
    },
    "quality-gate-scripts": {
        "paths": [
            "scripts/backend",
            "scripts/frontend",
            "scripts/dev-setup.sh",
            "scripts/pre-deploy-check.sh",
        ],
        "summary": (
            "Starting-template quality-gate shell scripts for a backend/ + "
            "frontend/ monorepo layout: lint/format/typecheck/security/"
            "complexity/test/coverage for a Python backend, and lint/format/"
            "typecheck/test for a TypeScript frontend, each with a `check-all.sh` "
            "and `fix-all.sh` entry point."
        ),
        "requires": (
            "adapt tool invocations (package name, coverage threshold, linter "
            "config) to this project's actual stack — see `scripts/README.md`."
        ),
    },
}


def _require_gh() -> None:
    if shutil.which("gh") is None:
        sys.exit(GH_MISSING_HINT)


def _run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)


def _local_head_sha() -> str:
    return _run(["git", "rev-parse", "HEAD"]).stdout.strip()


def _read_description(skill_md: Path) -> str:
    """Pull the `description:` field from frontmatter for the PR body."""
    text = skill_md.read_text()
    if not text.startswith("---"):
        return ""
    end = text.find("\n---\n", 3)
    if end == -1:
        return ""
    block = text[3:end]
    capturing = False
    chunks: list[str] = []
    for line in block.splitlines():
        if line.startswith("description:"):
            capturing = True
            value = line.split(":", 1)[1].strip().lstrip(">|").strip()
            if value:
                chunks.append(value)
            continue
        if capturing:
            if not line.startswith(" "):
                break
            chunks.append(line.strip())
    return " ".join(chunks).strip()


def _validate_skills(source_dir: Path, skills: list[str], target_skills_dir: Path) -> None:
    for name in skills:
        src = source_dir / name
        if not (src / "SKILL.md").is_file():
            raise SystemExit(f"error: source skill not found: {src}")
        if (target_skills_dir / name).exists():
            raise SystemExit(
                f"error: target already has .claude/skills/{name}/ — refuse to overwrite.\n"
                f"hint: use collect-skills to compare versions."
            )


def _validate_workflows(source_dir: Path, workflows: list[str], target_workflows_dir: Path) -> None:
    unknown = [name for name in workflows if name not in DISTRIBUTABLE_WORKFLOWS]
    if unknown:
        raise SystemExit(f"error: unknown workflow(s) {unknown}. Distributable: {sorted(DISTRIBUTABLE_WORKFLOWS)}")
    for name in workflows:
        filename = DISTRIBUTABLE_WORKFLOWS[name]["filename"]
        src = source_dir / filename
        if not src.is_file():
            raise SystemExit(f"error: source workflow not found: {src}")
        if (target_workflows_dir / filename).exists():
            raise SystemExit(
                f"error: target already has .github/workflows/{filename} — refuse to overwrite.\n"
                f"hint: open the existing file and reconcile by hand if changes are wanted."
            )


def _bundle_paths(name: str) -> list[str]:
    paths = DISTRIBUTABLE_BUNDLES[name]["paths"]
    assert isinstance(paths, list)
    return paths


def _validate_bundles(source_root: Path, bundles: list[str], target_root: Path) -> None:
    unknown = [name for name in bundles if name not in DISTRIBUTABLE_BUNDLES]
    if unknown:
        raise SystemExit(f"error: unknown bundle(s) {unknown}. Distributable: {sorted(DISTRIBUTABLE_BUNDLES)}")
    for name in bundles:
        for rel in _bundle_paths(name):
            src = source_root / rel
            if not src.exists():
                raise SystemExit(f"error: source path not found for bundle '{name}': {src}")
            if (target_root / rel).exists():
                raise SystemExit(
                    f"error: target already has {rel} (from bundle '{name}') — refuse to overwrite.\n"
                    f"hint: reconcile by hand, or drop that bundle from this run."
                )


def _copy_skills(source_dir: Path, skills: list[str], target_skills_dir: Path) -> None:
    target_skills_dir.mkdir(parents=True, exist_ok=True)
    for name in skills:
        shutil.copytree(source_dir / name, target_skills_dir / name)


def _copy_workflows(source_dir: Path, workflows: list[str], target_workflows_dir: Path) -> None:
    target_workflows_dir.mkdir(parents=True, exist_ok=True)
    for name in workflows:
        filename = DISTRIBUTABLE_WORKFLOWS[name]["filename"]
        shutil.copy2(source_dir / filename, target_workflows_dir / filename)


def _copy_bundles(source_root: Path, bundles: list[str], target_root: Path) -> None:
    for name in bundles:
        for rel in _bundle_paths(name):
            src = source_root / rel
            dst = target_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)


def _build_pr_body(
    skills: list[str],
    workflows: list[str],
    bundles: list[str],
    source_skills_dir: Path,
    source_sha: str,
) -> str:
    parts: list[str] = []
    summary_bits: list[str] = []
    if skills:
        summary_bits.append(f"{len(skills)} skill(s)")
    if workflows:
        summary_bits.append(f"{len(workflows)} workflow(s)")
    if bundles:
        summary_bits.append(f"{len(bundles)} scaffolding bundle(s)")
    parts.extend(
        [
            "## Summary",
            "",
            f"Adds {' and '.join(summary_bits)} from [`Geoffe-Ga/well-worn-tools`]"
            f"(https://github.com/Geoffe-Ga/well-worn-tools/tree/{source_sha[:7]}) "
            "to this repo.",
            "",
        ]
    )

    if skills:
        parts.extend(["## Skills", ""])
        for name in skills:
            desc = _read_description(source_skills_dir / name / "SKILL.md")
            first_sentence = desc.split(". ")[0].rstrip(".") + "." if desc else "(no description)"
            parts.append(f"- **{name}** — {first_sentence}")
        parts.append("")

    if workflows:
        parts.extend(["## Workflows", ""])
        for name in workflows:
            spec = DISTRIBUTABLE_WORKFLOWS[name]
            parts.append(f"- **{spec['filename']}** — {spec['summary']}")
            parts.append(f"  - **Requires:** {spec['requires']}")
        parts.append("")

    if bundles:
        parts.extend(["## Scaffolding bundles", ""])
        for name in bundles:
            bundle_spec = DISTRIBUTABLE_BUNDLES[name]
            paths = bundle_spec["paths"]
            assert isinstance(paths, list)
            parts.append(f"- **{name}** — {bundle_spec['summary']}")
            parts.append(f"  - **Adds:** {', '.join(f'`{p}`' for p in paths)}")
            parts.append(f"  - **Requires:** {bundle_spec['requires']}")
        parts.append("")

    parts.extend(
        [
            "## Provenance",
            "",
            f"Source SHA: `{source_sha}`",
            "Distributed via the `distribute-skills` skill (`metadata.distribute: false`, stays in well-worn-tools).",
            "",
            "## Test plan",
            "",
        ]
    )
    if skills:
        parts.extend(
            [
                "- [ ] Confirm `.claude/skills/` directory structure looks right",
                "- [ ] Spot-check one SKILL.md frontmatter for syntax",
                "- [ ] Decide whether each skill's triggers fit this repo's workflows",
            ]
        )
    if workflows:
        parts.extend(
            [
                "- [ ] Confirm each new file under `.github/workflows/` parses (actionlint)",
                "- [ ] Wire any required secrets noted under **Workflows** above",
                "- [ ] Confirm any referenced workflow names exist in this repo",
            ]
        )
    if bundles:
        parts.extend(
            [
                "- [ ] Wire any required secrets/skills/sibling bundles noted under **Scaffolding bundles** above",
                "- [ ] Fill in the stack/threshold placeholders these files ship with "
                "(e.g. `shared/house-rules.md`, `deslop-areas.json`) for this project",
                "- [ ] Confirm each new file under `.github/workflows/` parses (actionlint)",
            ]
        )
    return "\n".join(parts)


def _build_commit_message(skills: list[str], workflows: list[str], bundles: list[str], source_sha: str) -> str:
    pieces: list[str] = []
    if skills:
        pieces.append(f"skills {', '.join(skills)}")
    if workflows:
        pieces.append(f"workflows {', '.join(workflows)}")
    if bundles:
        pieces.append(f"bundles {', '.join(bundles)}")
    summary = " and ".join(pieces)
    return (
        f"feat: Add {summary} from well-worn-tools\n\n"
        f"Source: https://github.com/Geoffe-Ga/well-worn-tools/tree/{source_sha}\n"
        f"Distributed via well-worn-tools/distribute-skills."
    )


def _build_pr_title(skills: list[str], workflows: list[str], bundles: list[str]) -> str:
    kinds = [k for k, v in (("skills", skills), ("workflows", workflows), ("bundles", bundles)) if v]
    if len(kinds) > 1:
        return "Add skills, workflows, and/or bundles from well-worn-tools"
    if skills:
        return f"Add {', '.join(skills)} from well-worn-tools"
    if workflows:
        return f"Add {', '.join(workflows)} workflow(s) from well-worn-tools"
    return f"Add {', '.join(bundles)} bundle(s) from well-worn-tools"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("owner_repo", help="<owner>/<repo>")
    parser.add_argument("--skills", nargs="+", default=[], help="skill names to add")
    parser.add_argument(
        "--workflows",
        nargs="+",
        default=[],
        help=f"workflow names to add. Distributable: {sorted(DISTRIBUTABLE_WORKFLOWS)}",
    )
    parser.add_argument(
        "--bundles",
        nargs="+",
        default=[],
        help=f"scaffolding bundle names to add. Distributable: {sorted(DISTRIBUTABLE_BUNDLES)}",
    )
    parser.add_argument("--branch", default=None, help="feature branch name")
    parser.add_argument("--source-skills-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument(
        "--source-workflows-dir",
        type=Path,
        default=DEFAULT_WORKFLOWS_SOURCE_DIR,
        help="directory containing distributable workflow YAMLs (default: .github/workflows)",
    )
    parser.add_argument(
        "--source-repo-root",
        type=Path,
        default=DEFAULT_REPO_ROOT,
        help="well-worn-tools checkout root, for resolving bundle paths (default: .)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if not args.skills and not args.workflows and not args.bundles:
        parser.error("provide at least one of --skills, --workflows, or --bundles")

    _require_gh()
    source_skills = args.source_skills_dir.resolve() if args.skills else None
    if source_skills is not None and not source_skills.is_dir():
        print(f"error: source skills dir not found: {source_skills}", file=sys.stderr)
        return 2
    source_workflows = args.source_workflows_dir.resolve() if args.workflows else None
    if source_workflows is not None and not source_workflows.is_dir():
        print(f"error: source workflows dir not found: {source_workflows}", file=sys.stderr)
        return 2
    source_repo_root = args.source_repo_root.resolve() if args.bundles else None
    if source_repo_root is not None and not source_repo_root.is_dir():
        print(f"error: source repo root not found: {source_repo_root}", file=sys.stderr)
        return 2

    branch = args.branch or f"{DEFAULT_BRANCH_PREFIX}/{dt.date.today().isoformat()}"
    source_sha = _local_head_sha()

    with tempfile.TemporaryDirectory(prefix="distribute-skills-") as tmp:
        clone_root = Path(tmp) / "clone"
        clone_url = f"https://github.com/{args.owner_repo}.git"
        print(f"[1/6] Cloning {clone_url} ...")
        _run(["git", "clone", "--depth", "1", clone_url, str(clone_root)])

        print(f"[2/6] Creating branch {branch} ...")
        _run(["git", "checkout", "-b", branch], cwd=clone_root)

        target_skills_dir = clone_root / ".claude" / "skills"
        target_workflows_dir = clone_root / ".github" / "workflows"
        print(
            f"[3/6] Validating no overwrite for {len(args.skills)} skill(s), "
            f"{len(args.workflows)} workflow(s), {len(args.bundles)} bundle(s) ..."
        )
        if args.skills:
            assert source_skills is not None
            _validate_skills(source_skills, args.skills, target_skills_dir)
        if args.workflows:
            assert source_workflows is not None
            _validate_workflows(source_workflows, args.workflows, target_workflows_dir)
        if args.bundles:
            assert source_repo_root is not None
            _validate_bundles(source_repo_root, args.bundles, clone_root)

        print("[4/6] Copying into clone ...")
        if args.skills:
            assert source_skills is not None
            _copy_skills(source_skills, args.skills, target_skills_dir)
            _run(["git", "add", ".claude/skills"], cwd=clone_root)
        if args.workflows:
            assert source_workflows is not None
            _copy_workflows(source_workflows, args.workflows, target_workflows_dir)
            _run(["git", "add", ".github/workflows"], cwd=clone_root)
        if args.bundles:
            assert source_repo_root is not None
            _copy_bundles(source_repo_root, args.bundles, clone_root)
            for name in args.bundles:
                for rel in _bundle_paths(name):
                    _run(["git", "add", rel], cwd=clone_root)

        commit_message = _build_commit_message(args.skills, args.workflows, args.bundles, source_sha)
        _run(["git", "commit", "-m", commit_message], cwd=clone_root)

        if args.dry_run:
            print("[dry-run] Would push and open PR. Stopping here.")
            print(f"  Branch:    {branch}")
            if args.skills:
                print(f"  Skills:    {' '.join(args.skills)}")
            if args.workflows:
                print(f"  Workflows: {' '.join(args.workflows)}")
            if args.bundles:
                print(f"  Bundles:   {' '.join(args.bundles)}")
            return 0

        print(f"[5/6] Pushing branch {branch} ...")
        _run(["git", "push", "-u", "origin", branch], cwd=clone_root)

        print("[6/6] Opening PR ...")
        title = _build_pr_title(args.skills, args.workflows, args.bundles)
        body = _build_pr_body(
            args.skills,
            args.workflows,
            args.bundles,
            source_skills if source_skills is not None else Path("."),
            source_sha,
        )
        pr = _run(
            ["gh", "pr", "create", "--repo", args.owner_repo, "--head", branch, "--title", title, "--body", body],
            cwd=clone_root,
        )
        print(pr.stdout.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
