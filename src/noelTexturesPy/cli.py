#!/usr/bin/env python
"""
textures_cli — headless command-line interface for the noelTexturesPy
MRI texture-map processing pipeline.

Usage
-----
textures_cli --t1 sub01_t1.nii.gz
textures_cli --t1 sub01_t1.nii.gz --t2 sub01_flair.nii.gz \
             --case-id sub01 --output-dir ./results
python -m noelTexturesPy --t1 sub01_t1.nii.gz --output-dir ./results
"""

import argparse
import os
import sys
import tempfile

# Default MNI template — same relative path used by the web app.
_DEFAULT_TEMPLATE = os.path.join(
    './templates', 'mni_icbm152_t1_tal_nlin_sym_09a.nii.gz'
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='textures_cli',
        description='Run the noelTexturesPy MRI texture-map processing pipeline.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # --- Input files -------------------------------------------------------
    inputs = parser.add_argument_group('input files (at least one required)')
    inputs.add_argument(
        '--t1',
        metavar='FILE',
        default=None,
        help='T1-weighted NIfTI file (.nii or .nii.gz)',
    )
    inputs.add_argument(
        '--t2',
        metavar='FILE',
        default=None,
        help='T2-weighted or FLAIR NIfTI file (.nii or .nii.gz)',
    )

    # --- Identification ----------------------------------------------------
    parser.add_argument(
        '--case-id',
        metavar='ID',
        default=None,
        help='Case identifier used as output-file prefix (random if omitted)',
    )

    # --- Paths -------------------------------------------------------------
    paths = parser.add_argument_group('paths')
    paths.add_argument(
        '--output-dir',
        metavar='DIR',
        default=None,
        help='Directory for output files; created if absent '
        '(default: <temp-dir>/outputs)',
    )
    paths.add_argument(
        '--temp-dir',
        metavar='DIR',
        default=None,
        help='Temporary working directory; overrides the TEMPDIR environment '
        'variable (default: $TEMPDIR or a new mkdtemp)',
    )
    paths.add_argument(
        '--template',
        metavar='FILE',
        default=_DEFAULT_TEMPLATE,
        help='MNI152 template NIfTI file used for registration',
    )

    # --- Processing options ------------------------------------------------
    parser.add_argument(
        '--use-n3',
        action='store_true',
        help='Use N3 instead of N4 for bias-field correction',
    )

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    if args.t1 is None and args.t2 is None:
        parser.error('At least one of --t1 or --t2 must be provided.')

    missing = [
        (flag, path)
        for flag, path in [
            ('--t1', args.t1),
            ('--t2', args.t2),
            ('--template', args.template),
        ]
        if path is not None and not os.path.isfile(path)
    ]
    if missing:
        msgs = '\n'.join(f'  {flag}: file not found: {path}' for flag, path in missing)
        parser.error(f'The following files could not be found:\n{msgs}')

    # ------------------------------------------------------------------
    # Set TEMPDIR *before* importing image_processing, because that module
    # calls custom_logger() at import time, which reads/writes TEMPDIR.
    # ------------------------------------------------------------------
    if args.temp_dir:
        os.environ['TEMPDIR'] = os.path.abspath(args.temp_dir)
    elif 'TEMPDIR' not in os.environ:
        os.environ['TEMPDIR'] = tempfile.mkdtemp(prefix='noelTexturesPy_')

    temp_dir = os.environ['TEMPDIR']
    os.makedirs(temp_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Output directory
    # ------------------------------------------------------------------
    output_dir = (
        os.path.abspath(args.output_dir)
        if args.output_dir
        else os.path.join(temp_dir, 'outputs')
    )
    os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Deferred import — must happen after TEMPDIR is set (see above).
    # ------------------------------------------------------------------
    from noelTexturesPy.image_processing import (
        noelTexturesPy as Pipeline,  # noqa: PLC0415
    )
    from noelTexturesPy.utils import random_case_id  # noqa: PLC0415

    case_id = args.case_id if args.case_id is not None else random_case_id()

    print(f'Case ID      : {case_id}')
    print(f'Output dir   : {output_dir}')
    print(f'Temp dir     : {temp_dir}')
    print(f'Template     : {args.template}')
    if args.t1:
        print(f'T1 image     : {args.t1}')
    if args.t2:
        print(f'T2/FLAIR     : {args.t2}')
    print()

    try:
        Pipeline(
            id=str(case_id),
            t1=args.t1,
            t2=args.t2,
            output_dir=output_dir,
            temp_dir=temp_dir,
            template=args.template,
            usen3=args.use_n3,
        ).file_processor()
    except OSError as exc:
        print(f'\nerror: {exc}', file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
