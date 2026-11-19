"""Tests for scan-issue-writer/scripts/verify_scan_citations.py."""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path

import pytest
from conftest import scan_citations as vsc

PY_SOURCE = """\
import os


def generate_filename(stem):
    return os.path.join("out", stem)


class Ledger:
    def verify(self):
        return generate_filename("x")
"""


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    """A one-commit git repo; returns (path, scan SHA) with cwd set to it."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "mod.py").write_text(PY_SOURCE)
    (tmp_path / "pkg" / "util.ts").write_text(
        "export function parseConfig(raw: string) {\n  return raw;\n}\nexport const DEFAULT_TIMEOUT = 30;\n"
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "init")
    monkeypatch.chdir(tmp_path)
    return tmp_path, _git(tmp_path, "rev-parse", "HEAD")


def _run(monkeypatch: pytest.MonkeyPatch, sha: str, findings: list[object]) -> tuple[int, str]:
    stdin = "\n".join(json.dumps(f) for f in findings) + "\n"
    monkeypatch.setenv("SCAN_SHA", sha)
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    return vsc.main(), out.getvalue()


@pytest.mark.parametrize(
    ("path", "symbol"),
    [
        ("pkg/mod.py", "generate_filename"),
        ("pkg/mod.py", "Ledger"),
        ("pkg/mod.py", "Ledger.verify"),
        ("pkg/util.ts", "parseConfig"),
        ("pkg/util.ts", "DEFAULT_TIMEOUT"),
    ],
)
def test_check_accepts_real_definitions(repo: tuple[Path, str], path: str, symbol: str) -> None:
    _, sha = repo
    verdict, _ = vsc._check(sha, path, symbol, "")
    assert verdict == "OK"


def test_check_flags_phantom_and_suggests_nearest_definition(repo: tuple[Path, str]) -> None:
    _, sha = repo
    verdict, message = vsc._check(sha, "pkg/mod.py", "_unique_filename", "5-5")
    assert verdict == "PHANTOM"
    assert "def generate_filename" in message


def test_check_warns_on_bare_mention(repo: tuple[Path, str]) -> None:
    _, sha = repo
    verdict, _ = vsc._check(sha, "pkg/mod.py", "join", "")
    assert verdict == "WARN"


def test_check_reads_scan_sha_not_working_tree(repo: tuple[Path, str]) -> None:
    root, sha = repo
    (root / "pkg" / "mod.py").write_text("def brand_new():\n    pass\n")
    assert vsc._check(sha, "pkg/mod.py", "brand_new", "")[0] == "PHANTOM"
    assert vsc._check(sha, "pkg/mod.py", "generate_filename", "")[0] == "OK"


def test_check_errors_on_unreadable_file(repo: tuple[Path, str]) -> None:
    _, sha = repo
    assert vsc._check(sha, "pkg/missing.py", "anything", "")[0] == "ERROR"
    assert vsc._check(sha, "", "anything", "")[0] == "ERROR"


def test_citations_accepts_string_list_and_absent_symbol() -> None:
    assert vsc._citations('{"file": "a.py", "symbol": "f"}') == [("a.py", "f", "")]
    assert vsc._citations('{"file": "a.py", "symbols": ["f", "g"], "lines": "1-2"}') == [
        ("a.py", "f", "1-2"),
        ("a.py", "g", "1-2"),
    ]
    assert vsc._citations('{"file": "a.py"}') == []


def test_citations_rejects_non_object() -> None:
    with pytest.raises(TypeError, match="expected an object"):
        vsc._citations("[1, 2]")


def test_main_passes_when_every_citation_resolves(repo: tuple[Path, str], monkeypatch: pytest.MonkeyPatch) -> None:
    _, sha = repo
    code, out = _run(monkeypatch, sha, [{"file": "pkg/mod.py", "symbol": "generate_filename"}])
    assert code == 0
    assert "1 symbol citation(s) verified" in out


def test_main_fails_on_phantom(repo: tuple[Path, str], monkeypatch: pytest.MonkeyPatch) -> None:
    _, sha = repo
    code, out = _run(
        monkeypatch,
        sha,
        [{"file": "pkg/mod.py", "symbol": "generate_filename"}, {"file": "pkg/mod.py", "symbol": "verify_chain"}],
    )
    assert code == 1
    assert "PHANTOM" in out
    assert "refusing to file" in out


def test_main_fails_on_malformed_json(repo: tuple[Path, str], monkeypatch: pytest.MonkeyPatch) -> None:
    _, sha = repo
    monkeypatch.setenv("SCAN_SHA", sha)
    monkeypatch.setattr("sys.stdin", io.StringIO("not json\n"))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    assert vsc.main() == 1
    assert "malformed finding JSON" in out.getvalue()


def test_main_warns_when_nothing_was_checked(repo: tuple[Path, str], monkeypatch: pytest.MonkeyPatch) -> None:
    _, sha = repo
    code, out = _run(monkeypatch, sha, [{"file": "pkg/mod.py", "lines": "1-3"}])
    assert code == 0
    assert "checked 0 symbols" in out
