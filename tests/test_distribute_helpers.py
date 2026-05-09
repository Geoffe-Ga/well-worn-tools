"""Tests for pure helpers in distribute-skills/scripts/distribute.py."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import distribute as d

# ---------- _read_description ----------


def _write_skill_md(tmp_path: Path, body: str) -> Path:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(body)
    return skill_md


def test_read_description_inline(tmp_path: Path) -> None:
    skill_md = _write_skill_md(
        tmp_path,
        "---\nname: foo\ndescription: A simple skill.\n---\n\n# Foo\n",
    )
    assert d._read_description(skill_md) == "A simple skill."


def test_read_description_block_scalar(tmp_path: Path) -> None:
    skill_md = _write_skill_md(
        tmp_path,
        "---\nname: foo\ndescription: >-\n  Line one of the description.\n"
        "  Line two of the description.\nmetadata:\n  author: Geoff\n---\n",
    )
    desc = d._read_description(skill_md)
    assert "Line one" in desc
    assert "Line two" in desc


def test_read_description_no_frontmatter(tmp_path: Path) -> None:
    skill_md = _write_skill_md(tmp_path, "# Just a heading, no frontmatter\n")
    assert d._read_description(skill_md) == ""


def test_read_description_unclosed_frontmatter(tmp_path: Path) -> None:
    skill_md = _write_skill_md(tmp_path, "---\nname: foo\ndescription: x\n# never closed")
    assert d._read_description(skill_md) == ""


# ---------- _validate_skills ----------


def test_validate_skills_missing_source_raises(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    target = tmp_path / "tgt"
    with pytest.raises(SystemExit, match="source skill not found"):
        d._validate_skills(source, ["ghost"], target)


def test_validate_skills_existing_target_raises(tmp_path: Path) -> None:
    source = tmp_path / "src"
    (source / "foo").mkdir(parents=True)
    (source / "foo" / "SKILL.md").write_text("---\nname: foo\ndescription: x\n---\n")
    target = tmp_path / "tgt"
    (target / "foo").mkdir(parents=True)
    with pytest.raises(SystemExit, match="refuse to overwrite"):
        d._validate_skills(source, ["foo"], target)


def test_validate_skills_clean_passes(tmp_path: Path) -> None:
    source = tmp_path / "src"
    (source / "foo").mkdir(parents=True)
    (source / "foo" / "SKILL.md").write_text("---\nname: foo\ndescription: x\n---\n")
    target = tmp_path / "tgt"
    d._validate_skills(source, ["foo"], target)  # must not raise


# ---------- _validate_workflows ----------


def test_validate_workflows_unknown_name_raises(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="unknown workflow"):
        d._validate_workflows(tmp_path, ["does-not-exist"], tmp_path)


def test_validate_workflows_missing_source_raises(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    target = tmp_path / "tgt"
    with pytest.raises(SystemExit, match="source workflow not found"):
        d._validate_workflows(source, ["iteration-trigger"], target)


def test_validate_workflows_existing_target_raises(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "iteration-trigger.yml").write_text("name: x\n")
    target = tmp_path / "tgt"
    target.mkdir()
    (target / "iteration-trigger.yml").write_text("name: existing\n")
    with pytest.raises(SystemExit, match="refuse to overwrite"):
        d._validate_workflows(source, ["iteration-trigger"], target)


def test_validate_workflows_clean_passes(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "iteration-trigger.yml").write_text("name: x\n")
    target = tmp_path / "tgt"
    d._validate_workflows(source, ["iteration-trigger"], target)


# ---------- _build_pr_title ----------


def test_pr_title_skills_only() -> None:
    assert d._build_pr_title(["security"], []) == "Add security from well-worn-tools"


def test_pr_title_workflows_only() -> None:
    assert d._build_pr_title([], ["iteration-trigger"]) == ("Add iteration-trigger workflow(s) from well-worn-tools")


def test_pr_title_combined() -> None:
    assert d._build_pr_title(["security"], ["iteration-trigger"]) == "Add skills and workflows from well-worn-tools"


# ---------- _build_commit_message ----------


def test_commit_message_skills_only() -> None:
    msg = d._build_commit_message(["security", "testing"], [], "abc1234")
    assert msg.startswith("feat: Add skills security, testing from well-worn-tools")
    assert "abc1234" in msg


def test_commit_message_workflows_only() -> None:
    msg = d._build_commit_message([], ["iteration-trigger"], "abc1234")
    assert msg.startswith("feat: Add workflows iteration-trigger from well-worn-tools")


def test_commit_message_combined() -> None:
    msg = d._build_commit_message(["security"], ["iteration-trigger"], "abc1234")
    assert "skills security and workflows iteration-trigger" in msg


# ---------- _build_pr_body ----------


def test_pr_body_includes_workflow_requirements(tmp_path: Path) -> None:
    body = d._build_pr_body(
        skills=[],
        workflows=["iteration-trigger"],
        source_skills_dir=tmp_path,
        source_sha="0" * 40,
    )
    assert "## Workflows" in body
    assert "GEOFFE_GA_PAT" in body  # secret name surfaced
    assert "## Skills" not in body  # no skills section when none requested
    assert "actionlint" in body  # workflow-specific test plan items


def test_pr_body_includes_skill_descriptions(tmp_path: Path) -> None:
    skill_root = tmp_path / "demo"
    skill_root.mkdir()
    (skill_root / "SKILL.md").write_text(
        "---\nname: demo\ndescription: A demo skill for tests.\n---\n",
    )
    body = d._build_pr_body(
        skills=["demo"],
        workflows=[],
        source_skills_dir=tmp_path,
        source_sha="0" * 40,
    )
    assert "## Skills" in body
    assert "demo" in body
    assert "A demo skill for tests" in body
    assert "## Workflows" not in body


def test_pr_body_combined_has_both_sections(tmp_path: Path) -> None:
    skill_root = tmp_path / "demo"
    skill_root.mkdir()
    (skill_root / "SKILL.md").write_text(
        "---\nname: demo\ndescription: A demo skill.\n---\n",
    )
    body = d._build_pr_body(
        skills=["demo"],
        workflows=["iteration-trigger"],
        source_skills_dir=tmp_path,
        source_sha="0" * 40,
    )
    assert "## Skills" in body
    assert "## Workflows" in body
    assert "## Provenance" in body
    assert "## Test plan" in body
