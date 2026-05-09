"""Tests for pure helpers in collect-skills/scripts/adapt.py."""

from __future__ import annotations

from pathlib import Path

from conftest import collect_adapt as ca

# ---------- _parse_frontmatter ----------


def test_parse_frontmatter_returns_none_when_missing() -> None:
    parsed, end = ca._parse_frontmatter("# just a heading\n")
    assert parsed is None
    assert end == 0


def test_parse_frontmatter_extracts_top_level_scalars() -> None:
    text = "---\nname: foo\ndescription: a thing\n---\n\n# Body\n"
    parsed, end = ca._parse_frontmatter(text)
    assert parsed is not None
    assert parsed["name"] == "foo"
    assert parsed["description"] == "a thing"
    assert end > 0


def test_parse_frontmatter_extracts_metadata_subkeys() -> None:
    text = "---\nname: foo\ndescription: a thing\nmetadata:\n  author: Geoff\n  version: 1.0.0\n---\n"
    parsed, _ = ca._parse_frontmatter(text)
    assert parsed is not None
    metadata = parsed["metadata"]
    assert metadata == {"author": "Geoff", "version": "1.0.0"}


def test_parse_frontmatter_strips_chevron_block_scalar_marker() -> None:
    """`description: > value` form has the `>` stripped by the parser."""
    text = "---\nname: foo\ndescription: > raw value\n---\n"
    parsed, _ = ca._parse_frontmatter(text)
    assert parsed is not None
    assert parsed["description"] == "raw value"


def test_parse_frontmatter_known_quirk_with_dash_block_scalar() -> None:
    """`>-` form: parser strips `>` and `|` but leaves the trailing `-`.

    Documents existing behavior so a future fix shows up here as a
    deliberate test update rather than a silent drift.
    """
    text = "---\nname: foo\ndescription: >- raw value\n---\n"
    parsed, _ = ca._parse_frontmatter(text)
    assert parsed is not None
    assert parsed["description"] == "- raw value"


# ---------- scan_skill ----------


def _make_skill(root: Path, name: str, body: str) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(body)
    return skill_dir


def test_scan_skill_flags_missing_skill_md(tmp_path: Path) -> None:
    skill_dir = tmp_path / "ghost"
    skill_dir.mkdir()
    findings = ca.scan_skill(skill_dir)
    assert any(f.code == "MISSING_SKILL_MD" for f in findings)


def test_scan_skill_flags_missing_required_frontmatter(tmp_path: Path) -> None:
    skill_dir = _make_skill(tmp_path, "no-fm", "# just a body, no frontmatter\n")
    findings = ca.scan_skill(skill_dir)
    codes = {f.code for f in findings}
    assert "FRONTMATTER_MISSING" in codes


def test_scan_skill_flags_author_drift(tmp_path: Path) -> None:
    skill_dir = _make_skill(
        tmp_path,
        "wrong-author",
        "---\nname: wrong-author\ndescription: x\nmetadata:\n  author: Someone Else\n  version: 1.0.0\n---\n",
    )
    findings = ca.scan_skill(skill_dir)
    assert any(f.code == "FRONTMATTER_DRIFT" and "Someone Else" in f.detail for f in findings)


def test_scan_skill_clean_returns_no_findings(tmp_path: Path) -> None:
    skill_dir = _make_skill(
        tmp_path,
        "clean",
        "---\nname: clean\ndescription: A clean skill.\nmetadata:\n  author: Geoff\n  version: 1.0.0\n---\n\n# Clean\n",
    )
    findings = ca.scan_skill(skill_dir)
    assert findings == []


def test_scan_skill_flags_absolute_path_in_body(tmp_path: Path) -> None:
    skill_dir = _make_skill(
        tmp_path,
        "leaky",
        "---\nname: leaky\ndescription: x\nmetadata:\n"
        "  author: Geoff\n  version: 1.0.0\n---\n\n"
        "Run /home/geoff/private/script.sh to start.\n",
    )
    findings = ca.scan_skill(skill_dir)
    assert any(f.code == "ABSOLUTE_PATH" for f in findings)


def test_scan_skill_flags_external_repo_reference(tmp_path: Path) -> None:
    skill_dir = _make_skill(
        tmp_path,
        "external",
        "---\nname: external\ndescription: x\nmetadata:\n"
        "  author: Geoff\n  version: 1.0.0\n---\n\n"
        "See https://github.com/some-other/repo for details.\n",
    )
    findings = ca.scan_skill(skill_dir)
    assert any(f.code == "EXTERNAL_REPO_REF" for f in findings)
