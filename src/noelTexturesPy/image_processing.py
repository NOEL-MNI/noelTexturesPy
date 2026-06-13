import os

# restrict compute to CPU only
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

import multiprocessing
import sys
import tempfile
import time

import ants  # type: ignore[import-untyped]
from ants.core import ANTsImage
from brainchop import Volume
import matplotlib.pyplot as plt
import numpy as np
from antspynet.utilities import brain_extraction  # type: ignore[import-untyped]
from matplotlib.backends.backend_pdf import PdfPages

# import zipfile
from PIL import Image

from noelTexturesPy.custom_logging import custom_logger
from noelTexturesPy.utils import compute_RI
from noelTexturesPy.utils import peakfinder

# reduce tensorflow logging verbosity
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

os.environ['ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS'] = str(multiprocessing.cpu_count())
os.environ['ANTS_RANDOM_SEED'] = '666'

logger, log_filename, case_id = custom_logger()

FILE_MAPPING = {
    't1_n4': 't1_final.nii',
    't2_n4': 't2_final.nii',
    'mask': 'brainmask.nii',
    'segmentation': 'segmentation.nii',
    't1_gradient_magnitude': 't1_gradient_magnitude.nii',
    't2_gradient_magnitude': 't2_gradient_magnitude.nii',
    't1_relative_intensity': 't1_relative_intensity.nii',
    't2_relative_intensity': 't2_relative_intensity.nii',
}

class Brainchop:
    _TASK_MODEL = {
        'brain-extraction': 'mindgrab',
        'segmentation': 'robust_tissue',
    }
    _optimized: set[str] = set()

    def __init__(self, input_image, output_image=None, task='brain-extraction', reference_image=None):
        self.input_image = input_image
        self.output_image = output_image
        self.task = task
        self.reference_image = reference_image

    def load(self):
        from brainchop import load
        return load(self.input_image)

    def save(self, result):
        from brainchop import save
        save(result, self.output_image)

    @classmethod
    def _ensure_optimized(cls, model: str) -> None:
        """Run BEAM optimization for *model* once (cached on disk)."""
        if model in cls._optimized:
            return
        from brainchop.api import _get_best_beam
        if _get_best_beam(model, 1) is None:
            from brainchop import optimize
            optimize(model, beam=2)
        cls._optimized.add(model)

    def segment(self):
        from brainchop import segment
        model = self._TASK_MODEL.get(self.task)
        if model is None:
            sys.exit('invalid brainchop task specified')
        self._ensure_optimized(model)
        result = segment(self.load(), model)
        if self.reference_image is not None:
            return self._resample_to_reference(result, self.reference_image)
        return self.to_ants_image(result)

    def to_ants_image(self, vol: Volume) -> ANTsImage:
        """Convert a brainchop Volume to an ANTsImage.

        Parses the 352-byte NIfTI-1 header to recover spacing, origin, and
        direction, then wraps the voxel data via ants.from_numpy.

        Spatial metadata priority (mirrors nibabel/ANTs convention):
          1. sform_code > 0  -> srow_x/y/z affine rows
          2. qform_code > 0  -> quaternion + pixdim + qoffset
          3. fallback        -> identity direction, zero origin, pixdim spacing
        """
        import struct

        header = vol.header                        # 352-byte NIfTI-1 header
        arr    = vol.data.cast('float32').numpy()  # (256,256,256) ndarray, f32

        sform_code = struct.unpack_from('<h', header, 254)[0]
        qform_code = struct.unpack_from('<h', header, 252)[0]

        if sform_code > 0:
            srow_x = struct.unpack_from('4f', header, 280)
            srow_y = struct.unpack_from('4f', header, 296)
            srow_z = struct.unpack_from('4f', header, 312)
            origin    = (srow_x[3], srow_y[3], srow_z[3])
            A         = np.array([srow_x[:3], srow_y[:3], srow_z[:3]])
            spacing   = tuple(np.linalg.norm(A, axis=1).tolist())
            direction = (A / np.array(spacing)[:, None]).T
        elif qform_code > 0:
            pixdim  = struct.unpack_from('8f', header, 76)
            spacing = tuple(pixdim[1:4])
            b, c, d = (struct.unpack_from('<f', header, o)[0] for o in (256, 260, 264))
            a = np.sqrt(max(1.0 - b * b - c * c - d * d, 0.0))
            qfac = pixdim[0] if pixdim[0] in (-1.0, 1.0) else 1.0
            R = np.array([
                [a*a+b*b-c*c-d*d, 2*(b*c-a*d),       2*(b*d+a*c)      ],
                [2*(b*c+a*d),     a*a+c*c-b*b-d*d,   2*(c*d-a*b)      ],
                [2*(b*d-a*c),     2*(c*d+a*b),        a*a+d*d-b*b-c*c  ],
            ])
            R[:, 2] *= qfac
            direction = R
            qx, qy, qz = (struct.unpack_from('<f', header, o)[0] for o in (268, 272, 276))
            origin = (qx, qy, qz)
        else:
            pixdim    = struct.unpack_from('8f', header, 76)
            spacing   = tuple(pixdim[1:4])
            origin    = (0.0, 0.0, 0.0)
            direction = np.eye(3)

        print(f'Parsed NIfTI header: sform_code={sform_code}, qform_code={qform_code}')
        print(f'  origin={origin}, spacing={spacing}, direction=\n{direction}')

        return ants.from_numpy(arr, origin=origin, spacing=spacing, direction=direction)

    def _resample_to_reference(self, vol: Volume, reference: ANTsImage) -> ANTsImage:
        """Resample a brainchop Volume to match a reference image's geometry.

        Saves the brainchop output to a temporary NIfTI file, reads it back
        with ``ants.image_read`` (which handles the raw-NIfTI → RAS convention
        conversion), then computes a voxel-to-voxel mapping through physical
        space using both images' sform affines.  Nearest-neighbour sampling
        preserves integer label values.
        """
        from brainchop import save as bc_save

        # Write brainchop output to temp file and read with ANTsPy to get
        # the correct RAS-converted spatial metadata.
        tmp_path = os.path.join(tempfile.gettempdir(), '_brainchop_tmp.nii')
        bc_save(vol, tmp_path)
        bc_img = ants.image_read(tmp_path)

        arr = bc_img.numpy()
        bc_origin = np.array(bc_img.origin)
        bc_dir = np.array(bc_img.direction)
        bc_sp = np.array(bc_img.spacing)
        ref_origin = np.array(reference.origin)
        ref_dir = np.array(reference.direction)
        ref_sp = np.array(reference.spacing)

        # Build 4×4 sform affines (voxel → physical)
        bc_sform = np.eye(4)
        bc_sform[:3, :3] = bc_dir @ np.diag(bc_sp)
        bc_sform[:3, 3] = bc_origin

        ref_sform = np.eye(4)
        ref_sform[:3, :3] = ref_dir @ np.diag(ref_sp)
        ref_sform[:3, 3] = ref_origin

        # Voxel mapping: ref_voxel → physical → bc_voxel
        bc_A_inv = np.linalg.inv(bc_sform[:3, :3])
        bc_t = bc_sform[:3, 3]

        ref_shape = reference.shape
        ix, iy, iz = np.meshgrid(
            np.arange(ref_shape[0], dtype=np.float64),
            np.arange(ref_shape[1], dtype=np.float64),
            np.arange(ref_shape[2], dtype=np.float64),
            indexing='ij',
        )
        ref_voxels = np.stack([ix.ravel(), iy.ravel(), iz.ravel()], axis=1)

        physical = (ref_sform[:3, :3] @ ref_voxels.T + ref_sform[:3, 3:4]).T
        bc_voxels = (bc_A_inv @ (physical - bc_t).T).T

        bc_voxels_int = np.round(bc_voxels).astype(np.int64)
        bc_shape = arr.shape
        valid = (
            (bc_voxels_int[:, 0] >= 0) & (bc_voxels_int[:, 0] < bc_shape[0]) &
            (bc_voxels_int[:, 1] >= 0) & (bc_voxels_int[:, 1] < bc_shape[1]) &
            (bc_voxels_int[:, 2] >= 0) & (bc_voxels_int[:, 2] < bc_shape[2])
        )

        result = np.zeros(ref_voxels.shape[0], dtype=np.float32)
        result[valid] = arr[
            bc_voxels_int[valid, 0],
            bc_voxels_int[valid, 1],
            bc_voxels_int[valid, 2],
        ]

        # Clean up temp file
        try:
            os.remove(tmp_path)
        except OSError:
            pass

        return reference.new_image_like(result.reshape(ref_shape))


def volume_to_ants(vol: Volume, reference_image: ANTsImage | None = None) -> ANTsImage:
    """Convert a brainchop Volume to an ANTsImage.

    Convenience wrapper around Brainchop.to_ants_image usable without
    instantiating the full Brainchop class.

    Args:
        vol: brainchop Volume (data: Tensor 256^3 uint8, header: 352-byte NIfTI-1)
        reference_image: optional ANTsImage whose geometry the output will match.
            When provided the result is resampled to this image with nearest-neighbour
            interpolation (genericLabel) so integer label maps are preserved.

    Returns:
        ANTsImage with float32 data and spatial metadata recovered from the header,
        resampled to *reference_image* when given.
    """
    return Brainchop(None, None, reference_image=reference_image).to_ants_image(vol)


class noelTexturesPy:
    def __init__(
        self,
        id,
        t1=None,
        t2=None,
        output_dir=None,
        temp_dir=None,
        template=None,
        usen3=False,
        logger=logger,
    ):
        super().__init__()
        self._id = id
        self._t1file = t1
        self._t2file = t2
        self._outputdir = output_dir
        self._tempdir = temp_dir
        self._template = template
        self._usen3 = usen3
        self._logger = logger

    def load_nifti_file(self):
        # load nifti data to memory
        self._logger.info('loading nifti files')
        print('loading nifti files')
        self._mni = self._template

        if self._t1file is None and self._t2file is None:
            self._logger.warning('Please load the data first.', 'The data is missing')

        if self._t1file is not None and self._t2file is not None:
            self._t1 = ants.image_read(self._t1file)
            self._t2 = ants.image_read(self._t2file)
            self._icbm152 = ants.image_read(self._mni)

        if self._t1file is not None and self._t2file is None:
            self._t1 = ants.image_read(self._t1file)
            self._icbm152 = ants.image_read(self._mni)

        if self._t2file is not None and self._t1file is None:
            self._t2 = ants.image_read(self._t2file)
            self._icbm152 = ants.image_read(self._mni)

    def get_image_path(self, modality):
        filename = FILE_MAPPING.get(modality)
        if filename is None:
            raise ValueError(f'Invalid modality: {modality}')
        return os.path.join(self._outputdir, self._id + '_' + filename)

    def register_to_MNI_space(self):
        self._logger.info('registration to MNI template space')
        print('registration to MNI template space')
        if self._t1file is not None and self._t2file is not None:
            self._t1_reg = ants.registration(
                fixed=self._icbm152, moving=self._t1, type_of_transform='Affine'
            )
            self._t2_reg = ants.apply_transforms(
                fixed=self._icbm152,
                moving=self._t2,
                transformlist=self._t1_reg['fwdtransforms'],
            )

        if self._t1file is not None and self._t2file is None:
            self._t1_reg = ants.registration(
                fixed=self._icbm152, moving=self._t1, type_of_transform='Affine'
            )

        if self._t2file is not None and self._t1file is None:
            self._t2_reg = ants.registration(
                fixed=self._icbm152, moving=self._t2, type_of_transform='Affine'
            )

    def bias_correction(self):
        self._logger.info('performing N4 bias correction')
        print('performing N4 bias correction')
        if self._t1file is not None and self._t2file is not None:
            self._t1_n4 = (
                ants.iMath(
                    self._t1_reg['warpedmovout'].abp_n4(
                        intensity_truncation=(0.05, 0.95, 256), usen3=self._usen3
                    ),
                    'Normalize',
                )
                * 100
            )
            self._t2_n4 = (
                ants.iMath(self._t2_reg.abp_n4(usen3=self._usen3), 'Normalize') * 100
            )
            ants.image_write(
                self._t1_n4, os.path.join(self._outputdir, self._id + '_t1_final.nii')
            )
            ants.image_write(
                self._t2_n4, os.path.join(self._outputdir, self._id + '_t2_final.nii')
            )

        if self._t1file is not None and self._t2file is None:
            self._t1_n4 = (
                ants.iMath(
                    self._t1_reg['warpedmovout'].abp_n4(
                        intensity_truncation=(0.05, 0.95, 256), usen3=self._usen3
                    ),
                    'Normalize',
                )
                * 100
            )
            ants.image_write(
                self._t1_n4, os.path.join(self._outputdir, self._id + '_t1_final.nii')
            )

        if self._t2file is not None and self._t1file is None:
            self._t2_n4 = (
                ants.iMath(
                    self._t2_reg['warpedmovout'].abp_n4(usen3=self._usen3), 'Normalize'
                )
                * 100
            )
            ants.image_write(
                self._t2_n4, self.get_image_path('t2_n4')
            )

    def skull_stripping(self, type="brainchop"):
        self._logger.info('performing brain extraction')
        print('performing brain extraction')

        brainmask_fname = self.get_image_path('mask')

        self._modality = 't1'

        if self._t1file is not None:
            self._modality = 't2' if self._t2file is not None else 't1'

        if type == 'antspynet':
            self._mask: ANTsImage = self.brain_extraction()
        elif type == "brainchop":
            self._mask: ANTsImage = Brainchop(
                input_image=self.get_image_path('t1_n4'),
                output_image=brainmask_fname,
                task='brain-extraction',
                reference_image=self._t1_n4,
                ).segment()
        else:
            sys.exit('invalid brain extraction type specified')

        ants.image_write(
                self._mask,
                brainmask_fname,
            )

        ants.image_write(
                self._mask,
                os.path.join(self._outputdir, self._id + '_brainmask.nii'),
            )

    def segmentation(self, type="atropos", dtype=np.float32):
        self._logger.info('computing GM, WM, CSF segmentation')
        print('computing GM, WM, CSF segmentation')
        # https://antsx.github.io/ANTsPyNet/docs/build/html/utilities.html#applications

        segmentation_fname = self.get_image_path('segmentation')

        if self._t1file is not None:
            if type == 'atropos':
                segm: ANTsImage = ants.atropos(
                    a=(self._t1_n4, self._t2_n4) if self._t2file is not None else self._t1_n4,
                    i='Kmeans[3]',
                    m='[0.2,1x1x1]',
                    c='[3,0]',
                    x=self._mask,
                )
                self._segm: ANTsImage = segm['segmentation']
                self._gm = np.where((self._segm.numpy() == 2), 1, 0).astype(dtype)
                self._wm = np.where((self._segm.numpy() == 3), 1, 0).astype(dtype)
            elif type == 'brainchop':
                segm: ANTsImage = Brainchop(
                    input_image=self.get_image_path('t1_n4'),
                    output_image=segmentation_fname,
                    task='segmentation',
                    reference_image=self._t1_n4,
                    ).segment()
                self._segm: ANTsImage = segm
                self._gm = np.where((self._segm.numpy() == 1), 1, 0).astype(dtype)
                self._wm = np.where((self._segm.numpy() == 2), 1, 0).astype(dtype)
            else:
                sys.exit('invalid segmentation type specified')

        ants.image_write(
                self._segm,
                self.get_image_path('segmentation'),
            )

        ants.image_write(
                self._segm,
                os.path.join(self._outputdir, self._id + '_segmentation.nii'),
            )

    def gradient_magnitude(self):
        self._logger.info('computing gradient magnitude')
        print('computing gradient magnitude')
        if self._t1file is not None and self._t2file is not None:
            self._grad_t1 = ants.iMath(self._t1_n4, 'Grad', 1)
            # self._grad_t2 = ants.iMath(self._t2_n4, "Grad", 1)
            ants.image_write(
                self._grad_t1,
                os.path.join(self._outputdir, self._id + '_t1_gradient_magnitude.nii'),
            )
            # ants.image_write( self._grad_t1, os.path.join(self._outputdir, self._id+'_t2_gradient_magnitude.nii'))

        if self._t1file is not None and self._t2file is None:
            self._grad_t1 = ants.iMath(self._t1_n4, 'Grad', 1)
            ants.image_write(
                self._grad_t1,
                os.path.join(self._outputdir, self._id + '_t1_gradient_magnitude.nii'),
            )

        # if self._t2file is not None and self._t1file is None:
        #     self._grad_t2 = ants.iMath(self._t2_n4, "Grad", 1)
        # ants.image_write( self._grad_t2, os.path.join(self._outputdir, self._id+'_t2_gradient_magnitude.nii'))

    def relative_intensity(self):
        self._logger.info('computing relative intensity')
        print('computing relative intensity')
        if self._t1file is not None and self._t2file is not None:
            t1_n4_gm = self._t1_n4 * self._t1_n4.new_image_like(self._gm)
            t1_n4_wm = self._t1_n4 * self._t1_n4.new_image_like(self._wm)
            bg_t1 = peakfinder(t1_n4_gm, t1_n4_wm, 1, 99.5)
            t1_ri = compute_RI(self._t1_n4.numpy(), bg_t1, self._mask.numpy())
            tmp = self._t1_n4.new_image_like(t1_ri)
            self._ri = ants.smooth_image(tmp, sigma=3, FWHM=True)
            ants.image_write(
                self._ri,
                os.path.join(self._outputdir, self._id + '_t1_relative_intensity.nii'),
            )

        if self._t1file is not None and self._t2file is None:
            t1_n4_gm = self._t1_n4 * self._t1_n4.new_image_like(self._gm)
            t1_n4_wm = self._t1_n4 * self._t1_n4.new_image_like(self._wm)
            bg_t1 = peakfinder(t1_n4_gm, t1_n4_wm, 1, 99.5)
            t1_ri = compute_RI(self._t1_n4.numpy(), bg_t1, self._mask.numpy())
            tmp = self._t1_n4.new_image_like(t1_ri)
            self._ri = ants.smooth_image(tmp, sigma=3, FWHM=True)
            ants.image_write(
                self._ri,
                os.path.join(self._outputdir, self._id + '_t1_relative_intensity.nii'),
            )

    def generate_QC_maps(self):
        self._logger.info('generating QC report')
        QCDIR = os.path.join(self._tempdir, 'qc')
        if not os.path.exists(QCDIR):
            os.makedirs(QCDIR)
        if self._t1file is not None and self._t2file is not None:
            self._t1_n4.plot(
                overlay=self._mask,
                overlay_alpha=0.5,
                axis=2,
                ncol=8,
                nslices=32,
                title='Brain Masking',
                filename=os.path.join(QCDIR, '001_brain_masking.png'),
                dpi=300,
            )
            self._t1_n4.plot(
                overlay=self._segm,
                overlay_cmap='gist_rainbow',
                overlay_alpha=0.5,
                axis=2,
                ncol=8,
                nslices=32,
                title='Segmentation',
                filename=os.path.join(QCDIR, '002_segmentation.png'),
                dpi=300,
            )

        if self._t1file is not None and self._t2file is None:
            self._t1_n4.plot(
                overlay=self._mask,
                overlay_alpha=0.5,
                axis=2,
                ncol=8,
                nslices=32,
                title='Brain Masking',
                filename=os.path.join(QCDIR, '001_brain_masking.png'),
                dpi=300,
            )
            self._t1_n4.plot(
                overlay=self._segm,
                overlay_cmap='gist_rainbow',
                overlay_alpha=0.5,
                axis=2,
                ncol=8,
                nslices=32,
                title='Segmentation',
                filename=os.path.join(QCDIR, '002_segmentation.png'),
                dpi=300,
            )

        if self._t1file is not None or self._t2file is not None:
            with PdfPages(
                os.path.join(self._outputdir, self._id + '_QC_report.pdf')
            ) as pdf:
                for i in sorted(os.listdir(QCDIR)):
                    if i.endswith('.png'):
                        plt.figure()
                        img = Image.open(os.path.join(QCDIR, i))
                        plt.imshow(img)
                        plt.axis('off')
                        pdf.savefig(dpi=300)
                        plt.close()
                        os.remove(os.path.join(QCDIR, i))

    def brain_extraction(self):
        # https://antsx.github.io/ANTsPyNet/docs/build/html/utilities.html#applications
        if self._modality == 't1':
            image = self._t1_n4
        elif self._modality == 't2':
            image = self._t2_n4
        else:
            sys.exit('invalid contrast specified for brain extraction')
        # modality → antspynet network ID and weights filename (cached in ~/.keras/ANTsXNet/)
        _WEIGHTS_ID = {
            't1': 'brainExtractionRobustT1',
            't2': 'brainExtractionRobustT2',
        }
        try:
            prob = brain_extraction(image, modality=self._modality)
        except OSError as exc:
            from antspynet.utilities import (
                get_antsxnet_cache_directory,  # noqa: PLC0415
            )
            from antspynet.utilities import get_pretrained_network  # noqa: PLC0415

            cache_dir = get_antsxnet_cache_directory()
            weights_id = _WEIGHTS_ID.get(self._modality, '')
            weights_path = os.path.join(cache_dir, weights_id + '.h5')
            if weights_id and os.path.isfile(weights_path):
                self._logger.warning(
                    'Corrupt brain-extraction weights detected at '
                    f'{weights_path} — deleting and re-downloading...'
                )
                print(
                    'Corrupt brain-extraction weights detected — '
                    'deleting and re-downloading from ANTsXNet cache...'
                )
                os.remove(weights_path)
                get_pretrained_network(weights_id)
                prob = brain_extraction(image, modality=self._modality)
            else:
                msg = '\n'.join(
                    [
                        f'Brain-extraction model weights could not be loaded '
                        f'(modality={self._modality!r}).',
                        f'  Expected cache file : {weights_path}',
                        f'  h5py reported       : {exc}',
                    ]
                )
                self._logger.error(msg)
                raise OSError(msg) from exc
        # mask can be obtained as:
        mask = ants.threshold_image(
            prob, low_thresh=0.5, high_thresh=1.0, inval=1, outval=0, binary=True
        )
        return mask

    def file_processor(self):
        start = time.time()
        self.load_nifti_file()
        self.register_to_MNI_space()
        self.bias_correction()
        self.skull_stripping()
        self.segmentation()
        self.gradient_magnitude()
        self.relative_intensity()
        self.generate_QC_maps()
        # self.create_zip_archive()
        end = time.time()
        print(
            'pipeline processing time elapsed: {} seconds'.format(
                np.round(end - start, 1)
            )
        )
        self._logger.info(
            'pipeline processing time elapsed: {} seconds'.format(
                np.round(end - start, 1)
            )
        )
        self._logger.info('*********************************************')
