"""Tests for the textures_cli headless pipeline entry point."""

import logging
import os
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fixture: block ANTs/antspynet imports for every test in this module
# ---------------------------------------------------------------------------

_FIXED_CASE_ID = 'tst_0001'


@pytest.fixture(autouse=True)
def _mock_heavy_deps(monkeypatch):
    """Inject fake image_processing and utils modules so ANTs is never imported."""
    fake_pipeline_cls = MagicMock(name='PipelineCls')
    fake_pipeline_cls.return_value.file_processor.return_value = None

    fake_ip = types.ModuleType('noelTexturesPy.image_processing')
    fake_ip.noelTexturesPy = fake_pipeline_cls

    fake_utils = types.ModuleType('noelTexturesPy.utils')
    fake_utils.random_case_id = lambda: _FIXED_CASE_ID

    monkeypatch.setitem(sys.modules, 'noelTexturesPy.image_processing', fake_ip)
    monkeypatch.setitem(sys.modules, 'noelTexturesPy.utils', fake_utils)
    return fake_pipeline_cls


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_files(tmp_path, *names):
    """Create empty files under tmp_path and return their string paths."""
    paths = []
    for name in names:
        p = tmp_path / name
        p.write_text('')
        paths.append(str(p))
    return paths


# ---------------------------------------------------------------------------
# Parser tests — exercise _build_parser() directly, no sys.argv patching needed
# ---------------------------------------------------------------------------

def test_parser_defaults():
    """Parser should expose correct defaults for all optional arguments."""
    logger.info('Testing _build_parser defaults')

    from noelTexturesPy.cli import _build_parser

    args = _build_parser().parse_args(['--t1', 'dummy.nii'])

    assert args.t1 == 'dummy.nii'
    assert args.t2 is None
    assert args.case_id is None
    assert args.output_dir is None
    assert args.temp_dir is None
    assert args.template == os.path.join(
        './templates', 'mni_icbm152_t1_tal_nlin_sym_09a.nii.gz'
    )
    assert args.use_n3 is False

    logger.info('Parser defaults are correct')


def test_parser_t1_only():
    """Parser should accept --t1 and leave --t2 as None."""
    logger.info('Testing --t1 only')

    from noelTexturesPy.cli import _build_parser

    args = _build_parser().parse_args(['--t1', 'sub-01_t1.nii.gz'])
    assert args.t1 == 'sub-01_t1.nii.gz'
    assert args.t2 is None

    logger.info('--t1 only parsed correctly')


def test_parser_t2_only():
    """Parser should accept --t2 and leave --t1 as None."""
    logger.info('Testing --t2 only')

    from noelTexturesPy.cli import _build_parser

    args = _build_parser().parse_args(['--t2', 'sub-01_flair.nii.gz'])
    assert args.t2 == 'sub-01_flair.nii.gz'
    assert args.t1 is None

    logger.info('--t2 only parsed correctly')


def test_parser_all_flags():
    """Parser should correctly map all flags to their namespace attributes."""
    logger.info('Testing all flags together')

    from noelTexturesPy.cli import _build_parser

    args = _build_parser().parse_args([
        '--t1', 't1.nii',
        '--t2', 't2.nii',
        '--case-id', 'sub001',
        '--output-dir', '/out',
        '--temp-dir', '/tmp/work',
        '--template', '/tpl/mni.nii.gz',
        '--use-n3',
    ])

    assert args.t1 == 't1.nii'
    assert args.t2 == 't2.nii'
    assert args.case_id == 'sub001'
    assert args.output_dir == '/out'
    assert args.temp_dir == '/tmp/work'
    assert args.template == '/tpl/mni.nii.gz'
    assert args.use_n3 is True

    logger.info('All flags parsed correctly')


def test_parser_use_n3_flag():
    """--use-n3 flag should set use_n3 to True."""
    logger.info('Testing --use-n3 flag')

    from noelTexturesPy.cli import _build_parser

    args = _build_parser().parse_args(['--t1', 'x.nii', '--use-n3'])
    assert args.use_n3 is True

    logger.info('--use-n3 flag correctly sets use_n3=True')


# ---------------------------------------------------------------------------
# Validation tests — main() must reject invalid argument combinations
# ---------------------------------------------------------------------------

def test_main_requires_t1_or_t2():
    """main() should exit with code 2 when neither --t1 nor --t2 is provided."""
    logger.info('Testing that main() rejects missing --t1 and --t2')

    from noelTexturesPy.cli import main

    with patch('sys.argv', ['textures_cli']):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 2

    logger.info('main() correctly rejects missing inputs')


def test_main_missing_t1_file():
    """main() should exit with code 2 when --t1 path does not exist."""
    logger.info('Testing that main() rejects non-existent --t1 file')

    from noelTexturesPy.cli import main

    with patch('sys.argv', ['textures_cli', '--t1', '/nonexistent/t1.nii.gz']):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 2

    logger.info('main() correctly rejects missing --t1 file')


def test_main_missing_t2_file():
    """main() should exit with code 2 when --t2 path does not exist."""
    logger.info('Testing that main() rejects non-existent --t2 file')

    from noelTexturesPy.cli import main

    with patch('sys.argv', ['textures_cli', '--t2', '/nonexistent/flair.nii.gz']):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 2

    logger.info('main() correctly rejects missing --t2 file')


def test_main_missing_template_file(tmp_path):
    """main() should exit with code 2 when --template path does not exist."""
    logger.info('Testing that main() rejects non-existent --template file')

    (t1,) = _make_files(tmp_path, 't1.nii')
    from noelTexturesPy.cli import main

    with patch('sys.argv', [
        'textures_cli',
        '--t1', t1,
        '--template', '/nonexistent/mni.nii.gz',
    ]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 2

    logger.info('main() correctly rejects missing --template file')


# ---------------------------------------------------------------------------
# Happy-path tests — Pipeline is called with correct arguments
# ---------------------------------------------------------------------------

def test_main_t1_only(_mock_heavy_deps, tmp_path):
    """main() should call Pipeline with t1 set and t2=None."""
    logger.info('Testing main() with --t1 only')

    t1, tpl = _make_files(tmp_path, 't1.nii', 'template.nii.gz')
    fake_pipeline_cls = _mock_heavy_deps

    with patch('sys.argv', ['textures_cli', '--t1', t1, '--template', tpl]):
        with pytest.raises(SystemExit) as exc_info:
            from noelTexturesPy.cli import main
            main()

    assert exc_info.value.code == 0
    call_kwargs = fake_pipeline_cls.call_args.kwargs
    assert call_kwargs['t1'] == t1
    assert call_kwargs['t2'] is None
    assert call_kwargs['usen3'] is False
    fake_pipeline_cls.return_value.file_processor.assert_called_once()

    logger.info('Pipeline called correctly for T1-only run')


def test_main_t1_and_t2(_mock_heavy_deps, tmp_path):
    """main() should call Pipeline with both t1 and t2 when both flags are given."""
    logger.info('Testing main() with --t1 and --t2')

    t1, t2, tpl = _make_files(tmp_path, 't1.nii', 'flair.nii.gz', 'template.nii.gz')
    fake_pipeline_cls = _mock_heavy_deps

    with patch('sys.argv', [
        'textures_cli', '--t1', t1, '--t2', t2, '--template', tpl,
    ]):
        with pytest.raises(SystemExit) as exc_info:
            from noelTexturesPy.cli import main
            main()

    assert exc_info.value.code == 0
    call_kwargs = fake_pipeline_cls.call_args.kwargs
    assert call_kwargs['t1'] == t1
    assert call_kwargs['t2'] == t2

    logger.info('Pipeline called correctly for T1+T2 run')


def test_main_explicit_case_id(_mock_heavy_deps, tmp_path):
    """main() should pass --case-id value directly to Pipeline id argument."""
    logger.info('Testing main() with explicit --case-id')

    t1, tpl = _make_files(tmp_path, 't1.nii', 'template.nii.gz')
    fake_pipeline_cls = _mock_heavy_deps

    with patch('sys.argv', [
        'textures_cli', '--t1', t1, '--template', tpl, '--case-id', 'mycase',
    ]):
        with pytest.raises(SystemExit):
            from noelTexturesPy.cli import main
            main()

    assert fake_pipeline_cls.call_args.kwargs['id'] == 'mycase'

    logger.info('Explicit case ID forwarded to Pipeline correctly')


def test_main_random_case_id_used(_mock_heavy_deps, tmp_path):
    """main() should use random_case_id() when --case-id is not provided."""
    logger.info('Testing main() uses random case ID when --case-id omitted')

    t1, tpl = _make_files(tmp_path, 't1.nii', 'template.nii.gz')
    fake_pipeline_cls = _mock_heavy_deps

    with patch('sys.argv', ['textures_cli', '--t1', t1, '--template', tpl]):
        with pytest.raises(SystemExit):
            from noelTexturesPy.cli import main
            main()

    assert fake_pipeline_cls.call_args.kwargs['id'] == _FIXED_CASE_ID

    logger.info(f'Random case ID "{_FIXED_CASE_ID}" used when --case-id omitted')


def test_main_output_dir_created(_mock_heavy_deps, tmp_path):
    """main() should create --output-dir if it does not yet exist."""
    logger.info('Testing that main() creates --output-dir')

    t1, tpl = _make_files(tmp_path, 't1.nii', 'template.nii.gz')
    out_dir = str(tmp_path / 'new_output_dir')
    assert not os.path.exists(out_dir)

    with patch('sys.argv', [
        'textures_cli', '--t1', t1, '--template', tpl, '--output-dir', out_dir,
    ]):
        with pytest.raises(SystemExit):
            from noelTexturesPy.cli import main
            main()

    assert os.path.isdir(out_dir), f'Expected output dir to be created: {out_dir}'

    logger.info('Output directory created by main()')


def test_main_temp_dir_sets_env(_mock_heavy_deps, tmp_path):
    """--temp-dir should be written into os.environ['TEMPDIR'] before pipeline runs."""
    logger.info('Testing that --temp-dir sets TEMPDIR env var')

    t1, tpl = _make_files(tmp_path, 't1.nii', 'template.nii.gz')
    temp_dir = str(tmp_path / 'mywork')
    os.makedirs(temp_dir)

    original_tempdir = os.environ.get('TEMPDIR')
    try:
        with patch('sys.argv', [
            'textures_cli', '--t1', t1, '--template', tpl, '--temp-dir', temp_dir,
        ]):
            with pytest.raises(SystemExit):
                from noelTexturesPy.cli import main
                main()

        assert os.environ.get('TEMPDIR') == os.path.abspath(temp_dir)
    finally:
        if original_tempdir is None:
            os.environ.pop('TEMPDIR', None)
        else:
            os.environ['TEMPDIR'] = original_tempdir

    logger.info('TEMPDIR env var set correctly by --temp-dir')


def test_main_use_n3_forwarded(_mock_heavy_deps, tmp_path):
    """--use-n3 flag should reach Pipeline as usen3=True."""
    logger.info('Testing that --use-n3 is forwarded to Pipeline')

    t1, tpl = _make_files(tmp_path, 't1.nii', 'template.nii.gz')
    fake_pipeline_cls = _mock_heavy_deps

    with patch('sys.argv', [
        'textures_cli', '--t1', t1, '--template', tpl, '--use-n3',
    ]):
        with pytest.raises(SystemExit):
            from noelTexturesPy.cli import main
            main()

    assert fake_pipeline_cls.call_args.kwargs['usen3'] is True

    logger.info('usen3=True forwarded to Pipeline correctly')


def test_main_exits_zero_on_success(_mock_heavy_deps, tmp_path):
    """main() should exit with code 0 when the pipeline completes without error."""
    logger.info('Testing that main() exits with code 0 on success')

    t1, tpl = _make_files(tmp_path, 't1.nii', 'template.nii.gz')

    with patch('sys.argv', ['textures_cli', '--t1', t1, '--template', tpl]):
        with pytest.raises(SystemExit) as exc_info:
            from noelTexturesPy.cli import main
            main()

    assert exc_info.value.code == 0

    logger.info('main() exits 0 on success')


def test_main_output_dir_forwarded_to_pipeline(_mock_heavy_deps, tmp_path):
    """Pipeline should receive the resolved --output-dir path."""
    logger.info('Testing that --output-dir is forwarded to Pipeline')

    t1, tpl = _make_files(tmp_path, 't1.nii', 'template.nii.gz')
    out_dir = str(tmp_path / 'outputs')
    fake_pipeline_cls = _mock_heavy_deps

    with patch('sys.argv', [
        'textures_cli', '--t1', t1, '--template', tpl, '--output-dir', out_dir,
    ]):
        with pytest.raises(SystemExit):
            from noelTexturesPy.cli import main
            main()

    assert fake_pipeline_cls.call_args.kwargs['output_dir'] == os.path.abspath(out_dir)

    logger.info('output_dir forwarded to Pipeline correctly')


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------

def test_main_oserror_exits_one(_mock_heavy_deps, tmp_path, capsys):
    """OSError from file_processor should cause main() to exit with code 1."""
    logger.info('Testing that OSError in file_processor causes exit(1)')

    t1, tpl = _make_files(tmp_path, 't1.nii', 'template.nii.gz')
    fake_pipeline_cls = _mock_heavy_deps
    fake_pipeline_cls.return_value.file_processor.side_effect = OSError('corrupt weights')

    with patch('sys.argv', ['textures_cli', '--t1', t1, '--template', tpl]):
        with pytest.raises(SystemExit) as exc_info:
            from noelTexturesPy.cli import main
            main()

    assert exc_info.value.code == 1

    logger.info('OSError from pipeline causes exit(1) as expected')


def test_main_oserror_message_on_stderr(_mock_heavy_deps, tmp_path, capsys):
    """OSError message should appear on stderr, not stdout."""
    logger.info('Testing that OSError message is printed to stderr')

    t1, tpl = _make_files(tmp_path, 't1.nii', 'template.nii.gz')
    fake_pipeline_cls = _mock_heavy_deps
    fake_pipeline_cls.return_value.file_processor.side_effect = OSError('corrupt weights')

    with patch('sys.argv', ['textures_cli', '--t1', t1, '--template', tpl]):
        with pytest.raises(SystemExit):
            from noelTexturesPy.cli import main
            main()

    captured = capsys.readouterr()
    assert 'corrupt weights' in captured.err, (
        f'Error message should be on stderr; got: {captured.err!r}'
    )
    assert 'corrupt weights' not in captured.out, (
        'Error message should NOT be on stdout'
    )

    logger.info('OSError message correctly written to stderr')


# ---------------------------------------------------------------------------
# Module-level / structural tests
# ---------------------------------------------------------------------------

def test_module_main_is_callable():
    """noelTexturesPy.cli.main should be a callable."""
    logger.info('Testing that cli.main is callable')

    from noelTexturesPy import cli

    assert callable(cli.main), 'cli.main should be callable'
    assert callable(cli._build_parser), 'cli._build_parser should be callable'

    logger.info('cli.main and cli._build_parser are callable')


def test_dunder_main_routes_to_cli():
    """__main__.py should import and call cli.main (source inspection)."""
    logger.info('Testing __main__.py routes to cli.main')

    import pathlib

    root = pathlib.Path(__file__).parent.parent
    dunder_main = (root / 'src' / 'noelTexturesPy' / '__main__.py').read_text()

    assert 'from noelTexturesPy.cli import main' in dunder_main, (
        '__main__.py should import main from noelTexturesPy.cli'
    )
    assert 'main()' in dunder_main, '__main__.py should call main()'

    logger.info('__main__.py correctly routes to cli.main')
