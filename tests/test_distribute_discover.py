"""Tests for the exemption parser in distribute-skills/scripts/discover.py."""

from __future__ import annotations

from pathlib import Path

from conftest import distribute_discover as dd


def _write(tmp_path: Path, body: str) -> Path:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(body)
    return skill_md


def test_distributable_when_no_metadata_block(tmp_path: Path) -> None:
    skill_md = _write(tmp_path, "---\nname: x\ndescription: y\n---\n")
    assert dd._is_distributable(skill_md) is True


def test_distributable_when_distribute_unset(tmp_path: Path) -> None:
    skill_md = _write(
        tmp_path,
        "---\nname: x\ndescription: y\nmetadata:\n  author: Geoff\n---\n",
    )
    assert dd._is_distributable(skill_md) is True


def test_exempt_when_distribute_false(tmp_path: Path) -> None:
    skill_md = _write(
        tmp_path,
        "---\nname: x\ndescription: y\nmetadata:\n  author: Geoff\n  distribute: false\n---\n",
    )
    assert dd._is_distributable(skill_md) is False


def test_exempt_when_distribute_quoted_false(tmp_path: Path) -> None:
    skill_md = _write(
        tmp_path,
        "---\nname: x\ndescription: y\nmetadata:\n  distribute: 'false'\n---\n",
    )
    assert dd._is_distributable(skill_md) is False


def test_distributable_when_distribute_true(tmp_path: Path) -> None:
    skill_md = _write(
        tmp_path,
        "---\nname: x\ndescription: y\nmetadata:\n  distribute: true\n---\n",
    )
    assert dd._is_distributable(skill_md) is True


def test_distributable_when_metadata_block_ends_before_distribute_key(tmp_path: Path) -> None:
    """A top-level key after metadata: must not be misread as nested metadata."""
    skill_md = _write(
        tmp_path,
        "---\nname: x\ndescription: y\nmetadata:\n  author: Geoff\nother: top-level\n---\n",
    )
    assert dd._is_distributable(skill_md) is True


def test_missing_file_is_not_distributable(tmp_path: Path) -> None:
    assert dd._is_distributable(tmp_path / "does-not-exist.md") is False


def test_real_distribute_skills_skill_is_exempt() -> None:
    """Smoke check against the actual repo: distribute-skills self-exempts."""
    skill_md = Path(__file__).resolve().parents[1] / ".claude/skills/distribute-skills/SKILL.md"
    assert dd._is_distributable(skill_md) is False
