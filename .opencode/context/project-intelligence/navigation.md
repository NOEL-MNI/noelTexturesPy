<!-- Context: project-intelligence/navigation | Priority: high | Version: 1.1 | Updated: 2026-06-13 -->

# Project Intelligence — Navigation

**Purpose**: Quick-access index for all context files in this project.
**Last Updated**: 2026-06-13

---

## Quick Routes

| Need | Go to |
|------|-------|
| Tech stack, patterns, naming, security | `technical-domain.md` |
| Project overview, setup, CI/CD | `../../AGENTS.md` (project root) |
| Running the app | `pixi run app` or `textures_app` |
| Running tests | `pixi run test` |
| Linting / formatting | `tox -e lint` / `tox -e format` |

---

## Deep Dives

| File | Description | Priority | Version |
|------|-------------|----------|---------|
| `technical-domain.md` | Tech stack, code patterns, naming, standards, security | critical | 1.0 |

---

## Key Commands

```bash
pixi install               # install all deps
pixi run app               # start web UI on :9999
pixi run test              # run full test suite
tox -e lint                # ruff lint check
tox -e format              # ruff format check
tox -e types               # mypy type check
pre-commit run --all-files # run all pre-commit hooks
```
