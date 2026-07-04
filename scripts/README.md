# scripts/

Quality-gate shell scripts for a `backend/` + `frontend/` monorepo layout —
drop them into any project with a Python backend and a TypeScript/JS
frontend, or use them as a template to adapt to your own stack.

## Layout

```
scripts/
├── backend/           # Python quality gates — runs against backend/
│   ├── check-all.sh   # Run lint + format + typecheck + security + complexity + tests
│   ├── fix-all.sh     # Auto-fix linting and formatting
│   ├── lint.sh        # ruff
│   ├── format.sh      # ruff format
│   ├── typecheck.sh   # mypy
│   ├── test.sh        # pytest (--unit / --integration / --e2e / --all)
│   ├── coverage.sh    # pytest with coverage (≥90%)
│   ├── security.sh    # bandit + pip-audit
│   ├── complexity.sh  # radon + xenon
│   └── pr-status.sh   # gh CLI workflow monitor for PRs
├── frontend/          # TypeScript quality gates — runs against frontend/
│   ├── check-all.sh
│   ├── fix-all.sh
│   ├── lint.sh        # eslint
│   ├── format.sh      # prettier
│   ├── typecheck.sh   # tsc --noEmit
│   ├── test.sh        # jest
│   └── pr-status.sh
├── ralph/              # Ralph tick loop: fleet management, picker, recap — see scripts/ralph/FLEET.md
├── setup-scan-labels.sh  # Bootstrap the labels the scan workflows expect
├── dev-setup.sh        # Idempotent dev env bootstrap (venv + npm install + pre-commit)
└── pre-deploy-check.sh # Deployment readiness check (tests + Docker build)
```

## Adapting to your project

- `PROJECT_ROOT` in each `backend/`/`frontend/` script resolves to that
  subdirectory (not the repo root), so invocations like `ruff check .`
  operate on the correct subtree. If your backend package isn't at
  `backend/src`, update the `mypy`/`pytest` invocations in `typecheck.sh` /
  `test.sh` / `coverage.sh` to match your package name.
- If your repo is a single language (no `backend/` + `frontend/` split),
  delete the side you don't need and flatten `PROJECT_ROOT` to the repo root.
- Frontend and backend pairs are intentionally duplicated rather than
  unified so each subsection remains independently runnable and can evolve
  separately.

## Usage

```bash
source .venv/bin/activate                  # Python scripts need the venv
scripts/backend/check-all.sh --verbose     # Run every backend gate
scripts/backend/fix-all.sh                 # Auto-fix what can be fixed
scripts/frontend/check-all.sh              # Run every frontend gate
```

See `scripts/ralph/FLEET.md` and `.claude/commands/ralph-tick.md` for the
autonomous Ralph tick loop that drives these gates end to end.
