#!/usr/bin/env python3
"""Open a PR on a target repo that adds the requested local skills.

Usage:
    distribute.py <owner>/<repo>
        --skills <name> [<name> ...]
        [--branch <branch-name>]
        [--source-skills-dir <path>]
        [--dry-run]

Behavior:
  1. Clones the target repo into a temporary directory at its default branch.
  2. Creates the feature branch.
  3. Copies each requested skill from <source-skills-dir> (default:
     `.claude/skills/` of the cwd) into the clone, refusing to overwrite.
  4. Commits with provenance referencing the local well-worn-tools HEAD SHA.
  5. Pushes the branch and opens a PR via `gh pr create`.

`--dry-run` performs steps 1-4 only and prints what would happen, without
pushing or opening the PR. Always dry-run the first target.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_SOURCE_DIR = Path(".claude/skills")
DEFAULT_BRANCH_PREFIX = "add-well-worn-skills"


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


def _validate_request(source_dir: Path, skills: list[str], target_skills_dir: Path) -> None:
    for name in skills:
        src = source_dir / name
        if not (src / "SKILL.md").is_file():
            raise SystemExit(f"error: source skill not found: {src}")
        if (target_skills_dir / name).exists():
            raise SystemExit(
                f"error: target already has .claude/skills/{name}/ — refuse to overwrite.\n"
                f"hint: use collect-skills to compare versions."
            )


def _copy_skills(source_dir: Path, skills: list[str], target_skills_dir: Path) -> None:
    target_skills_dir.mkdir(parents=True, exist_ok=True)
    for name in skills:
        shutil.copytree(source_dir / name, target_skills_dir / name)


def _build_pr_body(owner_repo: str, skills: list[str], source_dir: Path, source_sha: str) -> str:
    lines = [
        "## Summary",
        "",
        f"Adds {len(skills)} skill(s) from [`Geoffe-Ga/well-worn-tools`]"
        f"(https://github.com/Geoffe-Ga/well-worn-tools/tree/{source_sha[:7]}/.claude/skills) "
        "to this repo's `.claude/skills/` tree.",
        "",
        "## Skills",
        "",
    ]
    for name in skills:
        desc = _read_description(source_dir / name / "SKILL.md")
        # Trim long descriptions to first sentence for the PR body.
        first_sentence = desc.split(". ")[0].rstrip(".") + "." if desc else "(no description)"
        lines.append(f"- **{name}** — {first_sentence}")
    lines.extend([
        "",
        "## Provenance",
        "",
        f"Source SHA: `{source_sha}`",
        f"Distributed via the `distribute-skills` skill (`metadata.distribute: false`, "
        "stays in well-worn-tools).",
        "",
        "## Test plan",
        "",
        "- [ ] Confirm `.claude/skills/` directory structure looks right",
        "- [ ] Spot-check one SKILL.md frontmatter for syntax",
        "- [ ] Decide whether each skill's triggers fit this repo's workflows",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("owner_repo", help="<owner>/<repo>")
    parser.add_argument("--skills", nargs="+", required=True, help="skill names to add")
    parser.add_argument("--branch", default=None, help="feature branch name")
    parser.add_argument("--source-skills-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    source_dir = args.source_skills_dir.resolve()
    if not source_dir.is_dir():
        print(f"error: source skills dir not found: {source_dir}", file=sys.stderr)
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
        print(f"[3/6] Validating no overwrite for {len(args.skills)} skill(s) ...")
        _validate_request(source_dir, args.skills, target_skills_dir)

        print(f"[4/6] Copying skills into clone ...")
        _copy_skills(source_dir, args.skills, target_skills_dir)
        _run(["git", "add", ".claude/skills"], cwd=clone_root)
        commit_message = (
            f"feat(skills): Add {', '.join(args.skills)} from well-worn-tools\n\n"
            f"Source: https://github.com/Geoffe-Ga/well-worn-tools/tree/{source_sha}\n"
            f"Distributed via well-worn-tools/distribute-skills."
        )
        _run(["git", "commit", "-m", commit_message], cwd=clone_root)

        if args.dry_run:
            print("[dry-run] Would push and open PR. Stopping here.")
            print(f"  Branch: {branch}")
            print(f"  Skills: {' '.join(args.skills)}")
            return 0

        print(f"[5/6] Pushing branch {branch} ...")
        _run(["git", "push", "-u", "origin", branch], cwd=clone_root)

        print(f"[6/6] Opening PR ...")
        title = f"Add {', '.join(args.skills)} from well-worn-tools"
        body = _build_pr_body(args.owner_repo, args.skills, source_dir, source_sha)
        pr = _run(
            ["gh", "pr", "create", "--repo", args.owner_repo,
             "--head", branch, "--title", title, "--body", body],
            cwd=clone_root,
        )
        print(pr.stdout.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
