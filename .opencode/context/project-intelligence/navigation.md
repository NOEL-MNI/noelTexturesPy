<!-- Context: project-intelligence/navigation | Priority: high | Version: 1.1 | Updated: 2026-06-12 -->

# Project Intelligence — Navigation

**Purpose**: Quick-access index for all context files in this project.
**Last Updated**: 2026-06-12

---

## Quick Routes

| Need | Go to |
|------|-------|
| Tech stack, patterns, naming, security | `technical-domain.md` |
| Brainchop integration, spatial resampling | `technical-domain.md` → Brainchop Integration |
| Project overview, setup, CI/CD | `../../AGENTS.md` (project root) |
| Running the app | `pixi run app` or `textures_app` |
| Running tests | `pixi run test` |
| Linting / formatting | `tox -e lint` / `tox -e format` |

---

## Deep Dives

| File | Description | Priority | Version |
|------|-------------|----------|---------|
| `technical-domain.md` | Tech stack, code patterns, naming, standards, security | critical | 1.1 |

---

## Key Commands

```bash
pixi install               # install all deps
pixi run app               # start web UI on :9999
pixi run test              # run full test suite
pixi run test-brainchop    # brainchop unit tests only
tox -e lint                # ruff lint check
tox -e format              # ruff format check (read-only diff)
tox -e types               # mypy type check
pre-commit run --all-files # run all pre-commit hooks
```
