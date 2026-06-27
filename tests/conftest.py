"""Test configuration: load skill scripts as importable modules.

The two `discover.py` files (one in distribute-skills/scripts/, one in
collect-skills/scripts/) share a basename, so we can't just put both
directories on sys.path - the second import would shadow the first.
Load each one explicitly under a distinct module name via importlib.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[1]
DISTRIBUTE_DIR = REPO_ROOT / ".claude/skills/distribute-skills/scripts"
COLLECT_DIR = REPO_ROOT / ".claude/skills/collect-skills/scripts"
RALPH_RECAP_DIR = REPO_ROOT / ".claude/skills/discord-ralph-recap/scripts"


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not build import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Eagerly load so test files can `from conftest import distribute, ...`
distribute = _load("ww_distribute", DISTRIBUTE_DIR / "distribute.py")
distribute_discover = _load("ww_distribute_discover", DISTRIBUTE_DIR / "discover.py")
collect_adapt = _load("ww_collect_adapt", COLLECT_DIR / "adapt.py")
ralph_stats = _load("ww_ralph_stats", RALPH_RECAP_DIR / "stats.py")
