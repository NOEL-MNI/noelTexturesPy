# AGENTS.md

## Setup

```bash
pixi install          # installs default env (ants + test features)
pixi install -e dev   # dev env also adds pre-commit, mypy, datalad
```

- Platforms: `linux-64`, `linux-aarch64`, `osx-arm64` only — no Windows, no `osx-x86_64`.
- `.envrc` uses direnv + pixi shell-hook. Run `direnv allow` once to auto-activate the pixi env.
- `conda-lock.yml` / `environment.yml` / `uv.lock` are fallback options; pixi is the CI-tested path.

---

## Running the application

```bash
pixi run app                              # start web UI on :9999
textures_app --port 9988                  # after pip/pixi install
textures_cli --t1 /path/to/t1.nii.gz      # headless pipeline (no UI)
```

**Input file naming** (enforced by `app.py`):
- T1: filename must contain `t1` or `T1`
- T2/FLAIR: filename must contain `t2`, `T2`, `flair`, or `FLAIR`
- Maximum 2 files per run

**Output files** (prefixed with a random case ID):
```
<id>_t1_final.nii
<id>_t2_final.nii              (if T2 provided)
<id>_brainmask.nii
<id>_segmentation.nii
<id>_t1_gradient_magnitude.nii
<id>_t1_relative_intensity.nii
<id>_QC_report.pdf
```

---

## Testing

```bash
pixi run test            # full suite, parallel (-n auto) — uses pyproject.toml settings
pixi run test-unit       # test_noelTexturesPy.py only — requires ANTs, takes minutes
pixi run test-webapp     # test_webapp.py only — fast, no ANTs needed
pixi run test-brainchop  # NOT a pixi task; use: pixi run python -m pytest tests/test_brainchop.py -v

# Single test
python -m pytest tests/test_webapp.py::test_app_initialization -v

# Via tox (includes coverage)
tox -e pytest
```

- `test_noelTexturesPy.py` imports `ants` and `antspynet` at **module level** — it errors in envs
  without the `ants` pixi feature. The default `pixi install` env includes ANTs.
- `test_brainchop.py` mocks all brainchop/ANTs deps via `sys.modules` injection — fast, no real models needed.
- Pipeline integration tests compare NIfTI outputs against `tests/data/ground-truth/` via
  `ants.image_similarity(metric='Correlation')` with `rtol=atol=0.1`. They are slow (~minutes each).
- Tests use `pyprojroot.here()` for paths; always run from the repo root.

---

## Code style and linting

```bash
tox -e lint               # ruff check  (what CI runs)
tox -e format             # ruff format --diff  — READ-ONLY diff, does NOT reformat
tox -e types              # mypy
pre-commit run --all-files # lint + autofix + format + pyupgrade
pre-commit install         # install hooks once locally
```

**Gotchas:**
- `pixi run lint` maps to `pylint` and `pixi run fmt` runs bare `ruff` with no subcommand —
  both are non-functional for CI checks. Always use `tox -e lint` / `tox -e format`.
- `tox -e format` shows a diff but **does not write**. To actually reformat: `ruff format src tests`
  or `pre-commit run ruff-format`.
- The pre-commit `ruff-check` hook runs with `--fix` — it modifies files on commit.
- pre-commit `pyupgrade --py312-plus` is enforced — avoid pre-3.12 patterns.

Ruff config (`pyproject.toml`): single quotes, rules B/E/F/I/W, ignore E203/E501/N813,
isort `force-single-line = true`, `preview = true`.

---

## Building

```bash
python -m build --wheel --sdist   # or: uv build --wheel --sdist
make build TAG=latest              # Docker multi-arch (pushes to registry)
docker build -f Dockerfile.pixi -t noelmni/textures-py:test .
```

Version comes from Git tags via **setuptools-scm**. Never edit `src/noelTexturesPy/_version.py`.

---

## Architecture notes

- **src layout**: package lives under `src/noelTexturesPy/` — never import from the project root.
- **Flask + Dash composition**: a bare `Flask` server is created first; `Dash(server=server, ...)`
  is mounted on it, enabling the custom `/download/<path>` route for NIfTI / PDF serving.
- **Sequential pipeline class**: `noelTexturesPy` in `image_processing.py` holds all state as
  `_`-prefixed instance attributes; `file_processor()` chains all steps in fixed order.
- **Brainchop class**: `Brainchop` in `image_processing.py` wraps brainchop library for brain
  extraction (`mindgrab`) and segmentation (`robust_tissue`). Uses `_ensure_optimized()` for
  BEAM caching and `_resample_to_reference()` for spatial alignment to the input image grid.
- **Side effect on import**: importing `image_processing` calls `custom_logger()` at module level,
  which sets `TEMPDIR` in the process environment if it is not already set.
- **CPU-only TF**: `CUDA_VISIBLE_DEVICES='-1'` and `TF_CPP_MIN_LOG_LEVEL='3'` are set at import
  time in `image_processing.py`.
- **`ANTS_RANDOM_SEED = '666'`** is hardcoded for pipeline reproducibility.
- **TEMPDIR**: `TEMPDIR` env var controls the working dir. `custom_logger()` creates one via
  `tempfile.mkdtemp()` if unset. Sub-dirs: `uploads/`, `outputs/`, `qc/`.
- **MNI template**: resolved as `./templates/mni_icbm152_t1_tal_nlin_sym_09a.nii.gz` relative to
  the working directory at startup — must exist when the app is launched.

---

## Brainchop gotchas

- `niimath -conform` reorients data to RAS; the raw NIfTI sform does NOT match the ANTsPy
  direction. Always use `ants.image_read()` to get correct RAS-converted spatial metadata.
- `ants.resample_image_to_target()` returns all-zeros when direction cosines have negative
  entries. Use direct numpy voxel mapping through physical space instead.
- `ants.apply_transforms()` requires file paths for transforms, not in-memory objects.
- `brainchop.optimize()` takes a model name (`mindgrab`, `robust_tissue`), not a task name
  (`brain-extraction`, `segmentation`).

---

## CI branches

- Tests (`build-python.yml`): push/PR to `main`, `dev`, `tests/**`, `pixi-dev`.
- Code-quality (`code-quality.yml`): `main` push/PR and daily cron — uses `tox` via `uv`.
- Release: push a `v*` tag → publish to PyPI + push multi-arch Docker image.
- Required secrets: `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `PREFIX_API_KEY`.
