"""Tests for the Brainchop class and volume_to_ants helper."""

import os
import struct
import sys
import types
from unittest.mock import MagicMock

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_nifti_header(
    shape=(256, 256, 256),
    spacing=(1.0, 1.0, 1.0),
    origin=(0.0, 0.0, 0.0),
    direction_cosines=None,
    sform_code=1,
    qform_code=1,
):
    """Build a minimal 352-byte NIfTI-1 header with valid sform."""
    hdr = bytearray(352)

    # sizeof_hdr (bytes 0-3)
    struct.pack_into('<i', hdr, 0, 348)

    # dim (bytes 40-55): ndim=3, then dims
    struct.pack_into('<hhhhhhhh', hdr, 40, 3, *shape, 1, 1, 1, 1)

    # datatype=FLOAT32 (bytes 70-71), bitpix=32 (bytes 72-73)
    struct.pack_into('<hh', hdr, 70, 16, 32)

    # pixdim (bytes 76-107)
    struct.pack_into('<8f', hdr, 76, 1.0, *spacing, 0.0, 0.0, 0.0, 0.0)

    # vox_offset (bytes 108-111)
    struct.pack_into('<f', hdr, 108, 352.0)

    # qform_code (bytes 252-253), sform_code (bytes 254-255)
    struct.pack_into('<hh', hdr, 252, qform_code, sform_code)

    if direction_cosines is None:
        direction_cosines = np.eye(3)

    # sform rows (bytes 280-327)
    for i, offset in enumerate((280, 296, 312)):
        row = list(direction_cosines[i] * np.array(spacing))
        row.append(origin[i])
        struct.pack_into('4f', hdr, offset, *row)

    return bytes(hdr)


def _make_volume(shape=(256, 256, 256), header=None, fill=1.0):
    """Create a fake brainchop Volume with numpy data."""
    data = MagicMock()
    data.cast.return_value.numpy.return_value = np.full(shape, fill, dtype=np.float32)
    vol = MagicMock()
    vol.data = data
    vol.header = header or _make_nifti_header(shape=shape)
    return vol


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_optimized():
    """Reset the _optimized class set between tests."""
    from noelTexturesPy.image_processing import Brainchop
    Brainchop._optimized.clear()
    yield
    Brainchop._optimized.clear()


@pytest.fixture()
def fake_brainchop_module(monkeypatch):
    """Inject a fake ``brainchop`` package into sys.modules.

    Returns a dict of mock callables so tests can configure return values.
    """
    mocks = {
        'load': MagicMock(name='brainchop.load'),
        'save': MagicMock(name='brainchop.save'),
        'segment': MagicMock(name='brainchop.segment'),
        'optimize': MagicMock(name='brainchop.optimize'),
        '_get_best_beam': MagicMock(name='brainchop.api._get_best_beam'),
    }

    # Build fake module tree
    brainchop_mod = types.ModuleType('brainchop')
    brainchop_mod.load = mocks['load']
    brainchop_mod.save = mocks['save']
    brainchop_mod.segment = mocks['segment']
    brainchop_mod.optimize = mocks['optimize']
    brainchop_mod.Volume = type('Volume', (), {})

    brainchop_api = types.ModuleType('brainchop.api')
    brainchop_api._get_best_beam = mocks['_get_best_beam']

    monkeypatch.setitem(sys.modules, 'brainchop', brainchop_mod)
    monkeypatch.setitem(sys.modules, 'brainchop.api', brainchop_api)

    return mocks


# ---------------------------------------------------------------------------
# Brainchop.__init__
# ---------------------------------------------------------------------------

class TestBrainchopInit:
    def test_stores_all_args(self):
        from noelTexturesPy.image_processing import Brainchop

        ref = MagicMock()
        bc = Brainchop('in.nii', 'out.nii', task='segmentation', reference_image=ref)

        assert bc.input_image == 'in.nii'
        assert bc.output_image == 'out.nii'
        assert bc.task == 'segmentation'
        assert bc.reference_image is ref

    def test_defaults(self):
        from noelTexturesPy.image_processing import Brainchop

        bc = Brainchop('in.nii')
        assert bc.output_image is None
        assert bc.task == 'brain-extraction'
        assert bc.reference_image is None


# ---------------------------------------------------------------------------
# Brainchop._TASK_MODEL
# ---------------------------------------------------------------------------

class TestTaskModel:
    def test_known_tasks(self):
        from noelTexturesPy.image_processing import Brainchop

        assert Brainchop._TASK_MODEL['brain-extraction'] == 'mindgrab'
        assert Brainchop._TASK_MODEL['segmentation'] == 'robust_tissue'

    def test_only_two_tasks(self):
        from noelTexturesPy.image_processing import Brainchop

        assert len(Brainchop._TASK_MODEL) == 2


# ---------------------------------------------------------------------------
# Brainchop._ensure_optimized
# ---------------------------------------------------------------------------

class TestEnsureOptimized:
    def test_skips_when_already_optimized(self, fake_brainchop_module):
        from noelTexturesPy.image_processing import Brainchop

        Brainchop._optimized.add('mindgrab')
        Brainchop._ensure_optimized('mindgrab')

        fake_brainchop_module['optimize'].assert_not_called()
        fake_brainchop_module['_get_best_beam'].assert_not_called()

    def test_skips_when_cache_exists(self, fake_brainchop_module):
        from noelTexturesPy.image_processing import Brainchop

        fake_brainchop_module['_get_best_beam'].return_value = 2

        Brainchop._ensure_optimized('mindgrab')

        fake_brainchop_module['_get_best_beam'].assert_called_once_with('mindgrab', 1)
        fake_brainchop_module['optimize'].assert_not_called()
        assert 'mindgrab' in Brainchop._optimized

    def test_optimizes_when_no_cache(self, fake_brainchop_module):
        from noelTexturesPy.image_processing import Brainchop

        fake_brainchop_module['_get_best_beam'].return_value = None

        Brainchop._ensure_optimized('robust_tissue')

        fake_brainchop_module['_get_best_beam'].assert_called_once_with('robust_tissue', 1)
        fake_brainchop_module['optimize'].assert_called_once_with('robust_tissue', beam=2)
        assert 'robust_tissue' in Brainchop._optimized

    def test_does_not_optimize_twice_in_session(self, fake_brainchop_module):
        from noelTexturesPy.image_processing import Brainchop

        fake_brainchop_module['_get_best_beam'].return_value = None

        Brainchop._ensure_optimized('mindgrab')
        Brainchop._ensure_optimized('mindgrab')

        assert fake_brainchop_module['optimize'].call_count == 1


# ---------------------------------------------------------------------------
# Brainchop.segment
# ---------------------------------------------------------------------------

class TestSegment:
    def test_maps_brain_extraction_to_mindgrab(self, fake_brainchop_module, monkeypatch):
        from noelTexturesPy.image_processing import Brainchop

        fake_vol = _make_volume()
        fake_brainchop_module['load'].return_value = fake_vol
        fake_brainchop_module['_get_best_beam'].return_value = 2
        fake_result = _make_volume()
        fake_brainchop_module['segment'].return_value = fake_result

        # Mock to_ants_image to avoid real ANTs
        monkeypatch.setattr(Brainchop, 'to_ants_image', lambda self, v: MagicMock())

        bc = Brainchop('in.nii')
        bc.segment()

        fake_brainchop_module['segment'].assert_called_once_with(fake_vol, 'mindgrab')

    def test_maps_segmentation_to_robust_tissue(self, fake_brainchop_module, monkeypatch):
        from noelTexturesPy.image_processing import Brainchop

        fake_vol = _make_volume()
        fake_brainchop_module['load'].return_value = fake_vol
        fake_brainchop_module['_get_best_beam'].return_value = 2
        fake_result = _make_volume()
        fake_brainchop_module['segment'].return_value = fake_result

        monkeypatch.setattr(Brainchop, 'to_ants_image', lambda self, v: MagicMock())

        bc = Brainchop('in.nii', task='segmentation')
        bc.segment()

        fake_brainchop_module['segment'].assert_called_once_with(fake_vol, 'robust_tissue')

    def test_exits_on_invalid_task(self, fake_brainchop_module):
        from noelTexturesPy.image_processing import Brainchop

        bc = Brainchop('in.nii', task='nonexistent')

        with pytest.raises(SystemExit):
            bc.segment()

    def test_calls_ensure_optimized(self, fake_brainchop_module, monkeypatch):
        from noelTexturesPy.image_processing import Brainchop

        fake_brainchop_module['load'].return_value = _make_volume()
        fake_brainchop_module['_get_best_beam'].return_value = 2
        fake_brainchop_module['segment'].return_value = _make_volume()

        monkeypatch.setattr(Brainchop, 'to_ants_image', lambda self, v: MagicMock())
        called_with = []
        monkeypatch.setattr(
            Brainchop, '_ensure_optimized',
            classmethod(lambda cls, m: called_with.append(m)),
        )

        bc = Brainchop('in.nii')
        bc.segment()

        assert called_with == ['mindgrab']

    def test_resamples_when_reference_given(self, fake_brainchop_module, monkeypatch):
        from noelTexturesPy.image_processing import Brainchop

        fake_brainchop_module['load'].return_value = _make_volume()
        fake_brainchop_module['_get_best_beam'].return_value = 2
        fake_result = _make_volume()
        fake_brainchop_module['segment'].return_value = fake_result

        ref_img = MagicMock()
        resample_mock = MagicMock()
        monkeypatch.setattr(Brainchop, '_resample_to_reference', resample_mock)

        bc = Brainchop('in.nii', reference_image=ref_img)
        bc.segment()

        resample_mock.assert_called_once_with(fake_result, ref_img)

    def test_to_ants_image_when_no_reference(self, fake_brainchop_module, monkeypatch):
        from noelTexturesPy.image_processing import Brainchop

        fake_brainchop_module['load'].return_value = _make_volume()
        fake_brainchop_module['_get_best_beam'].return_value = 2
        fake_result = _make_volume()
        fake_brainchop_module['segment'].return_value = fake_result

        ants_mock = MagicMock()
        monkeypatch.setattr(Brainchop, 'to_ants_image', lambda self, v: ants_mock)

        bc = Brainchop('in.nii', reference_image=None)
        result = bc.segment()

        assert result is ants_mock


# ---------------------------------------------------------------------------
# Brainchop.load / save
# ---------------------------------------------------------------------------

class TestLoadSave:
    def test_load_delegates(self, fake_brainchop_module):
        from noelTexturesPy.image_processing import Brainchop

        expected = MagicMock()
        fake_brainchop_module['load'].return_value = expected

        bc = Brainchop('input.nii')
        result = bc.load()

        fake_brainchop_module['load'].assert_called_once_with('input.nii')
        assert result is expected

    def test_save_delegates(self, fake_brainchop_module):
        from noelTexturesPy.image_processing import Brainchop

        result_vol = MagicMock()
        bc = Brainchop('in.nii', output_image='out.nii')
        bc.save(result_vol)

        fake_brainchop_module['save'].assert_called_once_with(result_vol, 'out.nii')


# ---------------------------------------------------------------------------
# Brainchop.to_ants_image
# ---------------------------------------------------------------------------

class TestToAntsImage:
    def test_sform_code_path(self, monkeypatch):
        """sform_code > 0 should parse srow_x/y/z and build correct metadata."""
        from noelTexturesPy.image_processing import Brainchop

        dc = np.eye(3)
        origin = (10.0, 20.0, 30.0)
        spacing = (2.0, 2.0, 2.0)
        hdr = _make_nifti_header(
            spacing=spacing, origin=origin,
            direction_cosines=dc, sform_code=1, qform_code=0,
        )
        vol = _make_volume(header=hdr, fill=42.0)

        captured = {}

        def fake_from_numpy(arr, origin=None, spacing=None, direction=None):
            captured['origin'] = origin
            captured['spacing'] = spacing
            captured['direction'] = direction
            captured['arr'] = arr
            return MagicMock()

        monkeypatch.setattr('ants.from_numpy', fake_from_numpy)

        bc = Brainchop('in.nii')
        bc.to_ants_image(vol)

        assert captured['origin'] == origin
        assert np.allclose(captured['spacing'], spacing)
        assert captured['arr'].shape == (256, 256, 256)

    def test_qform_only_path(self, monkeypatch):
        """qform_code > 0, sform_code == 0 should use quaternion math."""
        from noelTexturesPy.image_processing import Brainchop

        hdr = _make_nifti_header(
            sform_code=0, qform_code=1,
            spacing=(1.0, 1.0, 1.0), origin=(0, 0, 0),
        )
        vol = _make_volume(header=hdr)

        captured = {}

        def fake_from_numpy(arr, origin=None, spacing=None, direction=None):
            captured['origin'] = origin
            captured['spacing'] = spacing
            captured['direction'] = direction
            return MagicMock()

        monkeypatch.setattr('ants.from_numpy', fake_from_numpy)

        bc = Brainchop('in.nii')
        bc.to_ants_image(vol)

        assert captured['spacing'] == (1.0, 1.0, 1.0)
        assert captured['direction'].shape == (3, 3)

    def test_fallback_path(self, monkeypatch):
        """Both sform_code and qform_code == 0 should use identity direction."""
        from noelTexturesPy.image_processing import Brainchop

        hdr = _make_nifti_header(sform_code=0, qform_code=0)
        vol = _make_volume(header=hdr)

        captured = {}

        def fake_from_numpy(arr, origin=None, spacing=None, direction=None):
            captured['origin'] = origin
            captured['direction'] = direction
            return MagicMock()

        monkeypatch.setattr('ants.from_numpy', fake_from_numpy)

        bc = Brainchop('in.nii')
        bc.to_ants_image(vol)

        assert captured['origin'] == (0.0, 0.0, 0.0)
        assert np.allclose(captured['direction'], np.eye(3))


# ---------------------------------------------------------------------------
# Brainchop._resample_to_reference
# ---------------------------------------------------------------------------

class TestResampleToReference:
    def test_writes_temp_file_and_cleans_up(self, fake_brainchop_module, monkeypatch):
        """Should save to temp, read with ants.image_read, then remove temp file."""
        from noelTexturesPy.image_processing import Brainchop

        vol = _make_volume(fill=1.0)

        # Track temp file creation and deletion
        created_files = []
        removed_files = []

        def track_save(v, path):
            with open(path, 'wb') as f:
                f.write(b'\x00' * 100)
            created_files.append(path)

        fake_brainchop_module['save'].side_effect = track_save

        # Mock ants.image_read to return a small image
        fake_bc_img = MagicMock()
        fake_bc_img.numpy.return_value = np.ones((4, 4, 4), dtype=np.float32)
        fake_bc_img.origin = (0.0, 0.0, 0.0)
        fake_bc_img.direction = np.eye(3)
        fake_bc_img.spacing = (1.0, 1.0, 1.0)
        monkeypatch.setattr('ants.image_read', lambda p: fake_bc_img)

        # Mock reference image
        ref = MagicMock()
        ref.shape = (4, 4, 4)
        ref.origin = (0.0, 0.0, 0.0)
        ref.direction = np.eye(3)
        ref.spacing = (1.0, 1.0, 1.0)
        ref.new_image_like = lambda arr: arr

        # Track os.remove
        original_remove = os.remove

        def track_remove(path):
            removed_files.append(path)
            if os.path.exists(path):
                original_remove(path)

        monkeypatch.setattr('os.remove', track_remove)

        bc = Brainchop('in.nii', task='brain-extraction')
        bc._resample_to_reference(vol, ref)

        assert len(created_files) == 1
        assert created_files[0] == removed_files[0]

    def test_nearest_neighbour_preserves_labels(self, fake_brainchop_module, monkeypatch):
        """Integer label values should survive resampling."""
        from noelTexturesPy.image_processing import Brainchop

        # Create a 4x4x4 source with distinct labels
        src_arr = np.zeros((4, 4, 4), dtype=np.float32)
        src_arr[1:3, 1:3, 1:3] = 2.0  # label 2 in center

        vol = _make_volume(fill=0.0)
        fake_brainchop_module['save'].return_value = None

        fake_bc_img = MagicMock()
        fake_bc_img.numpy.return_value = src_arr
        fake_bc_img.origin = (0.0, 0.0, 0.0)
        fake_bc_img.direction = np.eye(3)
        fake_bc_img.spacing = (1.0, 1.0, 1.0)
        monkeypatch.setattr('ants.image_read', lambda p: fake_bc_img)

        # Reference has same geometry
        ref = MagicMock()
        ref.shape = (4, 4, 4)
        ref.origin = (0.0, 0.0, 0.0)
        ref.direction = np.eye(3)
        ref.spacing = (1.0, 1.0, 1.0)
        ref.new_image_like = lambda arr: arr

        monkeypatch.setattr('os.remove', lambda p: None)

        bc = Brainchop('in.nii')
        result = bc._resample_to_reference(vol, ref)

        assert np.allclose(result[1:3, 1:3, 1:3], 2.0)
        assert result[0, 0, 0] == 0.0

    def test_remaps_voxels_with_shifted_origin(self, fake_brainchop_module, monkeypatch):
        """Voxels must map correctly when source and reference have different origins."""
        from noelTexturesPy.image_processing import Brainchop

        # Source: 8x8x8 at origin (0,0,0), identity direction, spacing 1
        src_arr = np.arange(8 * 8 * 8, dtype=np.float32).reshape(8, 8, 8)
        vol = _make_volume(fill=0.0)
        fake_brainchop_module['save'].return_value = None

        fake_bc_img = MagicMock()
        fake_bc_img.numpy.return_value = src_arr
        fake_bc_img.origin = (0.0, 0.0, 0.0)
        fake_bc_img.direction = np.eye(3)
        fake_bc_img.spacing = (1.0, 1.0, 1.0)
        monkeypatch.setattr('ants.image_read', lambda p: fake_bc_img)

        # Reference: 4x4x4 at origin (2,2,2) — occupies physical [2,6)^3
        ref = MagicMock()
        ref.shape = (4, 4, 4)
        ref.origin = (2.0, 2.0, 2.0)
        ref.direction = np.eye(3)
        ref.spacing = (1.0, 1.0, 1.0)
        ref.new_image_like = lambda arr: arr

        monkeypatch.setattr('os.remove', lambda p: None)

        bc = Brainchop('in.nii')
        result = bc._resample_to_reference(vol, ref)

        # ref[0,0,0] -> physical (2,2,2) -> src[2,2,2]
        assert result[0, 0, 0] == src_arr[2, 2, 2]
        # ref[1,1,1] -> physical (3,3,3) -> src[3,3,3]
        assert result[1, 1, 1] == src_arr[3, 3, 3]
        # ref[3,3,3] -> physical (5,5,5) -> src[5,5,5]
        assert result[3, 3, 3] == src_arr[5, 5, 5]
        # Entire result should equal src[2:6, 2:6, 2:6]
        assert np.allclose(result, src_arr[2:6, 2:6, 2:6])

    def test_remaps_with_swapped_axes(self, fake_brainchop_module, monkeypatch):
        """Voxels must remap correctly when direction matrices differ (axis swap)."""
        from noelTexturesPy.image_processing import Brainchop

        # Source: 4x4x4 at origin (0,0,0), identity direction
        src_arr = np.zeros((4, 4, 4), dtype=np.float32)
        src_arr[3, 0, 0] = 99.0  # mark a specific voxel

        vol = _make_volume(fill=0.0)
        fake_brainchop_module['save'].return_value = None

        fake_bc_img = MagicMock()
        fake_bc_img.numpy.return_value = src_arr
        fake_bc_img.origin = (0.0, 0.0, 0.0)
        fake_bc_img.direction = np.eye(3)
        fake_bc_img.spacing = (1.0, 1.0, 1.0)
        monkeypatch.setattr('ants.image_read', lambda p: fake_bc_img)

        # Reference: 4x4x4 at origin (0,0,0) but axes swapped: x->y, y->x
        ref = MagicMock()
        ref.shape = (4, 4, 4)
        ref.origin = (0.0, 0.0, 0.0)
        ref.direction = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 1]], dtype=float)
        ref.spacing = (1.0, 1.0, 1.0)
        ref.new_image_like = lambda arr: arr

        monkeypatch.setattr('os.remove', lambda p: None)

        bc = Brainchop('in.nii')
        result = bc._resample_to_reference(vol, ref)

        # ref[0,3,0] -> physical (3,0,0) -> src[3,0,0] = 99.0
        assert result[0, 3, 0] == 99.0

    def test_out_of_bounds_maps_to_zero(self, fake_brainchop_module, monkeypatch):
        """Reference voxels outside the source extent should map to zero."""
        from noelTexturesPy.image_processing import Brainchop

        src_arr = np.ones((4, 4, 4), dtype=np.float32) * 42.0
        vol = _make_volume(fill=0.0)
        fake_brainchop_module['save'].return_value = None

        fake_bc_img = MagicMock()
        fake_bc_img.numpy.return_value = src_arr
        fake_bc_img.origin = (0.0, 0.0, 0.0)
        fake_bc_img.direction = np.eye(3)
        fake_bc_img.spacing = (1.0, 1.0, 1.0)
        monkeypatch.setattr('ants.image_read', lambda p: fake_bc_img)

        # Reference at origin (10,10,10) — completely outside source
        ref = MagicMock()
        ref.shape = (4, 4, 4)
        ref.origin = (10.0, 10.0, 10.0)
        ref.direction = np.eye(3)
        ref.spacing = (1.0, 1.0, 1.0)
        ref.new_image_like = lambda arr: arr

        monkeypatch.setattr('os.remove', lambda p: None)

        bc = Brainchop('in.nii')
        result = bc._resample_to_reference(vol, ref)

        assert np.all(result == 0.0)


# ---------------------------------------------------------------------------
# volume_to_ants
# ---------------------------------------------------------------------------

class TestVolumeToAnts:
    def test_delegates_to_to_ants_image(self, monkeypatch):
        from noelTexturesPy.image_processing import Brainchop
        from noelTexturesPy.image_processing import volume_to_ants

        vol = _make_volume()
        expected = MagicMock()

        monkeypatch.setattr(Brainchop, 'to_ants_image', lambda self, v: expected)

        result = volume_to_ants(vol)
        assert result is expected

    def test_passes_reference_image(self, monkeypatch):
        from noelTexturesPy.image_processing import Brainchop
        from noelTexturesPy.image_processing import volume_to_ants

        vol = _make_volume()
        ref = MagicMock()
        expected = MagicMock()

        def fake_to_ants(self, v):
            return expected

        monkeypatch.setattr(Brainchop, 'to_ants_image', fake_to_ants)

        result = volume_to_ants(vol, reference_image=ref)
        assert result is expected
