# CLI (Headless)

Run the texture-map processing pipeline without a browser — useful for batch jobs, HPC clusters, and scripted workflows.

## Prerequisites

Same environment as the web app. ANTs (`antspyx`) and ANTsPyNet (`antspynet`) must be installed:

```bash
pixi install          # default env includes ANTs
```

The MNI152 template must exist at `./templates/mni_icbm152_t1_tal_nlin_sym_09a.nii.gz` relative to the working directory, or be supplied via `--template`.

---

## Quick start

```bash
textures_cli --t1 sub-001/t1.nii.gz
```

---

## Arguments

| Flag | Default | Description |
|------|---------|-------------|
| `--t1 FILE` | — | T1-weighted NIfTI (`.nii` or `.nii.gz`) |
| `--t2 FILE` | — | T2-weighted or FLAIR NIfTI |
| `--case-id ID` | random (e.g. `abc_1234`) | Output file prefix |
| `--output-dir DIR` | `<temp-dir>/outputs` | Output directory; created if absent |
| `--temp-dir DIR` | `$TEMPDIR` or `mkdtemp` | Working directory; overrides `TEMPDIR` env var |
| `--template FILE` | `./templates/mni_icbm152_t1_tal_nlin_sym_09a.nii.gz` | MNI152 registration template |
| `--use-n3` | off | Use N3 instead of N4 bias-field correction |

!!! warning "Required input"
    At least one of `--t1` or `--t2` must be provided. All supplied file paths are validated before the pipeline starts.

---

## Usage examples

```bash
# T1 only
textures_cli --t1 sub-001/t1.nii.gz

# T1 + FLAIR — explicit case ID and output directory
textures_cli --t1 sub-001/t1.nii.gz --t2 sub-001/flair.nii.gz \
             --case-id sub001 --output-dir ./results/sub-001

# Custom MNI template and temp directory
textures_cli --t1 sub-001/t1.nii.gz \
             --template /data/mni/mni_icbm152_t1.nii.gz \
             --temp-dir /scratch/tmp/sub-001

# N3 bias correction instead of default N4
textures_cli --t1 sub-001/t1.nii.gz --use-n3

# python -m shorthand (equivalent to textures_cli)
python -m noelTexturesPy --t1 sub-001/t1.nii.gz --output-dir ./results

# Full help
textures_cli --help
```

---

## Outputs

Written to `--output-dir` (default: `<temp-dir>/outputs`):

| File | Description |
|------|-------------|
| `<id>_t1_final.nii` | T1 registered to MNI152, N4-corrected, normalised |
| `<id>_t2_final.nii` | T2/FLAIR registered to MNI152 *(only if `--t2` supplied)* |
| `<id>_t1_gradient_magnitude.nii` | Gradient magnitude map (models FCD blurring) |
| `<id>_t1_relative_intensity.nii` | Relative intensity map (models FCD hyperintensities) |
| `<id>_QC_report.pdf` | Brain mask and segmentation QC figures |

Processing time is typically 3–10 minutes depending on CPU core count.

---

## Template path

The MNI152 template is resolved **relative to the current working directory**. Always run `textures_cli` from the repository root, or pass an absolute path:

```bash
textures_cli --t1 sub-001/t1.nii.gz \
             --template /absolute/path/to/mni_icbm152_t1_tal_nlin_sym_09a.nii.gz
```

---

## Auto-recovery for corrupt model weights

!!! info "Automatic cache repair"
    If the antspynet brain-extraction weights file (`~/.keras/ANTsXNet/brainExtractionRobustT1.h5` or `brainExtractionRobustT2.h5`) is corrupt or partially downloaded, the pipeline detects the h5py `OSError`, deletes the bad file, re-downloads it via `get_pretrained_network()`, and retries — no manual intervention required.

---

## CLI vs web UI

| | `textures_cli` | `textures_app` |
|--|--|--|
| Interface | Terminal | Browser (Dash) |
| Case ID | `--case-id` flag or random | Entered in the UI |
| Output location | `--output-dir` | Download links in browser |
| Batch / scripted use | Yes | No |
| Real-time log view | stdout | In-browser log panel |
