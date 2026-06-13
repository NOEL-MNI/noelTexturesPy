<!-- Context: project-intelligence/technical | Priority: critical | Version: 1.1 | Updated: 2026-06-12 -->

# Technical Domain

**Purpose**: Tech stack, architecture, development patterns for noelTexturesPy.
**Last Updated**: 2026-06-12
**Update Triggers**: Tech stack changes | New patterns | Architecture decisions
**Audience**: Developers, AI coding agents

---

## Primary Stack

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Language | Python | ≥ 3.12 | Platforms: linux-64, linux-aarch64, osx-arm64 |
| Web UI | Plotly Dash + Flask | dash ≥ 3.3, flask ≥ 3.0.3 | Flask server first; Dash mounted on it |
| UI Components | dash-bootstrap-components | ≥ 2.0.4 | Bootstrap theme |
| MRI Processing | ANTsPy + ANTsPyNet | ≥ 0.6.2 / ≥ 0.3.1 | Custom conda channel: prefix.dev/noel-forge |
| Brain Extraction | brainchop | ≥ 0.2.3 | niimath-based; models: mindgrab, robust_tissue |
| Numerics | NumPy + SciPy + Pandas | ≥ 2.4.6 / ≥ 1.15.2 / ≥ 3.0.3 | |
| Visualization | Matplotlib | ≥ 3.10.9 | QC PDF generation |
| Package manager | Pixi (recommended) | — | `pixi install` / `pixi run <task>` |
| Build | setuptools-scm | version from git tags | Never edit `_version.py` |

---

## Code Patterns

### Brainchop Integration (Brain Extraction + Segmentation)

```python
# Brainchop class: wraps brainchop library with spatial resampling
class Brainchop:
    _TASK_MODEL = {
        'brain-extraction': 'mindgrab',
        'segmentation': 'robust_tissue',
    }
    _optimized: set[str] = set()  # session-level BEAM cache

    def segment(self):
        from brainchop import segment
        model = self._TASK_MODEL.get(self.task)
        self._ensure_optimized(model)          # auto-BEAM on first run
        result = segment(self.load(), model)
        if self.reference_image is not None:
            return self._resample_to_reference(result, self.reference_image)
        return self.to_ants_image(result)
```

### NIfTI Spatial Resampling (brainchop → ANTsPy)

```python
# brainchop niimath -conform reorients to RAS; raw sform ≠ ANTsPy direction.
# Fix: save to temp NIfTI → read with ants.image_read (handles RAS conversion)
# → compute voxel mapping through physical space → nearest-neighbour sampling
def _resample_to_reference(self, vol, reference):
    tmp_path = os.path.join(tempfile.gettempdir(), '_brainchop_tmp.nii')
    bc_save(vol, tmp_path)
    bc_img = ants.image_read(tmp_path)  # RAS-converted sform
    # Build sforms, map ref_voxel → physical → bc_voxel, sample with NN
```

### BEAM Optimization Caching

```python
@classmethod
def _ensure_optimized(cls, model: str) -> None:
    """Run BEAM optimization once (cached on disk in ~/.cache/brainchop/)."""
    if model in cls._optimized:
        return
    from brainchop.api import _get_best_beam
    if _get_best_beam(model, 1) is None:
        from brainchop import optimize
        optimize(model, beam=2)
    cls._optimized.add(model)
```

### Flask + Dash Server Composition

```python
server = Flask(__name__)
app = Dash(server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config['suppress_callback_exceptions'] = True

@server.route('/download/<path:path>')
def download(path):
    return send_from_directory(output_dir, path, as_attachment=True)
```

### Pipeline Class Pattern

```python
class noelTexturesPy:
    def __init__(self, id, t1, t2, output_dir, temp_dir, template, usen3=False):
        self._id = id  # all state as _-prefixed instance attrs

    def file_processor(self):
        self.load_nifti_file()
        self.register_to_MNI_space()
        self.bias_correction()
        self.skull_stripping()      # brainchop or antspynet
        self.segmentation()         # brainchop or atropos
        self.gradient_magnitude()
        self.relative_intensity()
        self.generate_QC_maps()
```

---

## Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Module files | `snake_case.py` | `image_processing.py`, `custom_logging.py` |
| Classes | `PascalCase` | `Brainchop`, `noelTexturesPy` (exception: matches project) |
| Functions / methods | `snake_case` | `file_processor()`, `_ensure_optimized()` |
| Instance attributes | `_snake_case` (leading `_`) | `self._t1`, `self._reference_image` |
| Class attributes | `_UPPER_SNAKE` | `_TASK_MODEL`, `_optimized` |
| Constants | `UPPER_SNAKE` | `TEMPDIR`, `ANTS_RANDOM_SEED` |
| NIfTI outputs | `<id>_<modality>_<suffix>` | `abc_1234_t1_gradient_magnitude.nii` |

---

## Code Standards

- **Ruff** for lint + format: `tox -e lint` / `tox -e format`; single quotes enforced
- **isort** via Ruff: `force-single-line = true`; rules B, E, F, I, W; ignore E203, E501, N813
- **mypy** type checking: `tox -e types`; `ignore_missing_imports` for ants/dash stubs
- **pre-commit** hooks: `pre-commit install` once, then automatic
- **src layout**: source under `src/noelTexturesPy/` — never import from project root
- **CPU-only TF**: `CUDA_VISIBLE_DEVICES='-1'` at module import
- **TEMPDIR**: respect `os.environ.get('TEMPDIR')`; fall back to `tempfile.mkdtemp()`
- **pyproject.toml** is single source of truth — no `setup.cfg`
- **`_version.py`** is auto-generated by setuptools-scm — never edit

---

## Security Requirements

- Validate uploaded filenames: must contain `t1`/`T1` or `t2`/`T2`/`flair`/`FLAIR`
- Reject runs with >2 uploaded files
- Processing isolated in per-session TEMPDIR (`uploads/`, `outputs/`, `qc/`)
- No secrets in source; use environment variables
- Uploaded files cleaned up after processing

---

## 📂 Codebase References

| Pattern | File | Notes |
|---------|------|-------|
| Brainchop class | `src/noelTexturesPy/image_processing.py:45-212` | `_TASK_MODEL`, `_ensure_optimized`, `segment`, `_resample_to_reference` |
| Pipeline class | `src/noelTexturesPy/image_processing.py:233-620` | Sequential `file_processor()`, skull_stripping, segmentation |
| Flask+Dash setup | `src/noelTexturesPy/app.py:44-57` | Server composition, routes |
| Dash callbacks | `src/noelTexturesPy/app.py:103-180` | `@callback` decorators |
| UI layout | `src/noelTexturesPy/layout.py` | `dbc.Container`, `dcc.Upload` |
| Utilities | `src/noelTexturesPy/utils.py` | `compute_RI()`, `peakfinder()` |
| Logger factory | `src/noelTexturesPy/custom_logging.py` | TEMPDIR setup + rotating log |
| Brainchop tests | `tests/test_brainchop.py` | 26 tests: init, segment, optimize, resample |
| CLI tests | `tests/test_cli.py` | Parser, validation, happy-path, error handling |
| Tool config | `pyproject.toml` | Ruff, mypy, pytest, setuptools-scm |
| Tasks | `pixi.toml` | `app`, `test`, `test-unit`, `test-webapp` |

---

## Known Gotchas

- `brainchop niimath -conform` reorients data; raw NIfTI sform ≠ ANTsPy direction. Use `ants.image_read()` for correct RAS conversion.
- `ants.resample_image_to_target()` returns all-zeros with negative direction cosines. Use direct numpy voxel mapping instead.
- `ants.apply_transforms()` needs file paths, not in-memory ANTsTransform objects.
- brainchop `optimize()` takes model name (`mindgrab`), not task name (`brain-extraction`).
- `tox -e format` shows diff but does NOT write. Use `ruff format src tests` to reformat.

## Related Context Files

- `navigation.md` — quick overview of all context files
