"""Tests for decide/scripts/build.py: sheet validation, theming and rendering."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from conftest import decide_build as db


def _sheet() -> dict[str, Any]:
    return {
        "id": "2026-11-19-session-store",
        "title": "Session Store Choice",
        "decisions": [
            {
                "id": "store",
                "title": "Where sessions live",
                "summary": "Pick a backing store.",
                "options": [
                    {"id": "redis", "label": "Redis", "pros": ["fast"], "cons": ["ops"]},
                    {"id": "pg", "label": "Postgres", "pros": ["one db"], "cons": []},
                ],
                "recommended": "pg",
                "recommendation_reason": "Fewer moving parts.",
                "tradeoffs": [{"dimension": "Speed", "values": {"redis": "high", "pg": "ok"}}],
                "costs": [{"item": "Hosting", "values": {"redis": "$15", "pg": "$0"}}],
                "risks": [{"risk": "Lock contention", "severity": "low", "options": ["pg"]}],
                "examples": [{"title": "Rails defaults", "url": "https://example.com"}],
            }
        ],
    }


def _problems(sheet: object) -> list[str]:
    with pytest.raises(db.SheetError) as exc:
        db.validate(sheet)
    problems: list[str] = exc.value.problems
    return problems


def test_valid_sheet_passes() -> None:
    db.validate(_sheet())


def test_top_level_must_be_object() -> None:
    assert _problems([]) == ["sheet: top level must be a JSON object"]


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (lambda s: s.update(id="Bad ID"), "'id' must be lowercase"),
        (lambda s: s.update(decisions=[]), "'decisions' must be a non-empty list"),
        (lambda s: s["decisions"][0]["options"].pop(), "needs at least two choices"),
        (lambda s: s["decisions"][0].update(recommended="nope"), "not one of its option ids"),
        (lambda s: s["decisions"][0].pop("recommendation_reason"), "needs a 'recommendation_reason'"),
        (lambda s: s["decisions"][0]["tradeoffs"][0]["values"].update(x="?"), "unknown option id(s) ['x']"),
        (lambda s: s["decisions"][0]["risks"][0].update(severity="extreme"), "'severity' must be one of"),
        (lambda s: s["decisions"][0]["examples"][0].update(url="http://x"), "must start with https://"),
        (lambda s: s["decisions"][0].update(examples=[]), "'examples' is empty"),
        (lambda s: s["decisions"].append(copy.deepcopy(s["decisions"][0])), "duplicate decision id 'store'"),
    ],
)
def test_validation_problems(mutate: Any, expected: str) -> None:
    sheet = _sheet()
    mutate(sheet)
    assert any(expected in p for p in _problems(sheet)), _problems(sheet)


@pytest.mark.parametrize(
    ("theme", "expected"),
    [
        ("dark", "theme: must be an object"),
        ({"bogus": 1}, "theme: unknown key 'bogus'"),
        ({"light": []}, "theme.light: must be an object"),
        ({"light": {"nope": "#fff"}}, "theme.light: unknown token 'nope'"),
        ({"dark": {"bg": "red;}body{x:y"}}, "theme.dark.bg: 'red;}body{x:y' is not a plain CSS color"),
        ({"fonts": []}, "theme.fonts: must be an object"),
        ({"fonts": {"hand": "Comic"}}, "theme.fonts: unknown role 'hand'"),
        ({"fonts": {"body": "x;}</style>"}}, "theme.fonts.body: not a plain font stack"),
        ({"fontsUrl": "https://evil.example/x.css"}, "theme.fontsUrl: must be a"),
        ({"radius": "8vw"}, "theme.radius: must be a length"),
    ],
)
def test_theme_rejects_unsafe_or_unknown_values(theme: object, expected: str) -> None:
    sheet = _sheet()
    sheet["theme"] = theme
    assert any(p.startswith(expected) for p in _problems(sheet)), _problems(sheet)


def test_theme_css_emits_light_dark_fonts_and_radius() -> None:
    css = db.theme_css(
        {
            "light": {"bg": "#ffffff"},
            "dark": {"bg": "#000000"},
            "fonts": {"body": "Inter, sans-serif"},
            "radius": "8px",
        }
    )
    assert ":root { --bg: #ffffff; --font-body: Inter, sans-serif; --radius: 8px; }" in css
    assert (
        '@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #000000; color-scheme: dark; } }'
    ) in css
    assert ':root[data-theme="dark"] { --bg: #000000; color-scheme: dark; }' in css
    assert db.theme_css(None) == ""


def test_main_writes_page_and_escapes_data(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    sheet = _sheet()
    sheet["title"] = "A </script><b>title"
    src = tmp_path / "sheet.json"
    src.write_text(json.dumps(sheet), encoding="utf-8")
    assert db.main([str(src)]) == 0
    page = (tmp_path / "sheet.html").read_text(encoding="utf-8")
    assert "A &lt;/script&gt;&lt;b&gt;title" in page
    assert "</script><b>" not in page
    assert capsys.readouterr().out.strip() == str(tmp_path / "sheet.html")


def test_main_reports_invalid_sheet(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = tmp_path / "sheet.json"
    src.write_text(json.dumps({"id": "x"}), encoding="utf-8")
    assert db.main([str(src), "--out", str(tmp_path / "o.html")]) == 1
    assert "problem(s):" in capsys.readouterr().err
    assert not (tmp_path / "o.html").exists()


def test_main_reports_unreadable_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = tmp_path / "sheet.json"
    src.write_text("{not json", encoding="utf-8")
    assert db.main([str(src)]) == 1
    assert "Could not read" in capsys.readouterr().err
