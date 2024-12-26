import logging
import os
import shutil
import unittest
from tempfile import mkdtemp

import ants
import numpy as np
import numpy.testing as nptest

from noelTexturesPy.image_processing import noelTexturesPy

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
TEMPDIR = os.environ.get('TEMPDIR', mkdtemp())


def compare_images(predicted_image, ground_truth_image, metric_type='correlation'):
    """
    Measure similarity between two images.
    NOTE: Similarity is actually returned as distance (i.e. dissimilarity)
    per ITK/ANTs convention. E.g. using Correlation metric, the similarity
    of an image with itself returns -1.
    """
    # predicted_image = ants.image_read(predicted_image)
    # ground_truth_image = ants.image_read(ground_truth_image)
    if metric_type == 'correlation':
        metric = ants.image_similarity(
            predicted_image,
            ground_truth_image,
            metric_type='Correlation',
        )
        metric = np.abs(metric)
    else:
        metric = ants.label_overlap_measures(
            predicted_image, ground_truth_image
        ).TotalOrTargetOverlap[1]

    return metric


class LoggedTestCase(unittest.TestCase):
    def setUp(self):
        logger.info(f'Starting test: {self._testMethodName}')
        super().setUp()

    def tearDown(self):
        logger.info(f'Finished test: {self._testMethodName}')
        super().tearDown()


class TestNoelTexturesPy(LoggedTestCase):
    def setUp(self):
        self._id = 'test_case'
        self._t1file = './data/inputs/sub-00055/t1.nii.gz'
        self._t2file = './data/inputs/sub-00055/flair.nii.gz'
        self._outputdir = TEMPDIR
        self._template = '../templates/mni_icbm152_t1_tal_nlin_sym_09a.nii.gz'
        self._usen3 = False
        self.noelTexturesPy = noelTexturesPy(
            id=self._id,
            t1=None,
            t2=None,
            output_dir=self._outputdir,
            temp_dir=self._outputdir,
            template=self._template,
            usen3=self._usen3,
        )

        # load predictions from a previous validated run (known as ground-truth labels in this context)
        self.gt_t1_reg = ants.image_read('./data/ground-truth/t1_final.nii.gz').clone(
            'float'
        )
        self.gt_t2_reg = ants.image_read('./data/ground-truth/t2_final.nii.gz').clone(
            'float'
        )
        self.gt_gm = ants.image_read(
            './data/ground-truth/t1_gradient_magnitude.nii.gz'
        ).clone('float')
        self.gt_ri = ants.image_read(
            './data/ground-truth/t1_relative_intensity.nii.gz'
        ).clone('float')

        try:
            os.mkdir(self._outputdir)
            print(f"Directory '{self._outputdir}' created successfully.")
        except FileExistsError:
            pass

    def test_load_nifti_file(self):
        logger.debug('testing loading nifti files')
        self.noelTexturesPy._t1file = self._t1file
        self.noelTexturesPy._t2file = self._t2file
        self.noelTexturesPy.load_nifti_file()
        self.assertIsInstance(self.noelTexturesPy._t1, ants.core.ants_image.ANTsImage)
        self.assertIsInstance(self.noelTexturesPy._t2, ants.core.ants_image.ANTsImage)
        self.assertIsInstance(
            self.noelTexturesPy._icbm152, ants.core.ants_image.ANTsImage
        )

    def test_register_to_MNI_space(self):
        logger.debug('testing co-registration of t1 and t2 to MNI space')
        self.noelTexturesPy._t1file = self._t1file
        self.noelTexturesPy._t2file = self._t2file
        self.noelTexturesPy.load_nifti_file()
        self.noelTexturesPy.register_to_MNI_space()
        self.assertIsInstance(
            self.noelTexturesPy._t1_reg['warpedmovout'], ants.core.ants_image.ANTsImage
        )
        self.assertIsInstance(
            self.noelTexturesPy._t2_reg, ants.core.ants_image.ANTsImage
        )

    def test_bias_correction(self):
        logger.debug('testing N4 bias correction')
        self.noelTexturesPy._t1file = self._t1file
        self.noelTexturesPy._t2file = self._t2file
        self.noelTexturesPy.load_nifti_file()
        self.noelTexturesPy.register_to_MNI_space()
        self.noelTexturesPy.bias_correction()
        self.assertIsInstance(
            self.noelTexturesPy._t1_n4, ants.core.ants_image.ANTsImage
        )
        self.assertIsInstance(
            self.noelTexturesPy._t2_n4, ants.core.ants_image.ANTsImage
        )

        self.assertTrue(
            os.path.exists(os.path.join(self._outputdir, f'{self._id}_t1_final.nii'))
        )
        self.assertTrue(
            os.path.exists(os.path.join(self._outputdir, f'{self._id}_t2_final.nii'))
        )

        metric = compare_images(
            self.noelTexturesPy._t1_n4,
            self.gt_t1_reg,
            metric_type='correlation',
        )
        print('correlation of the current t1 with the ground truth: {}'.format(metric))
        # set relative tolerance to 0.1
        # predicted image is expected to have overlap within 0.1
        nptest.assert_allclose(1.0, metric, rtol=0.1, atol=0.1)

        metric = compare_images(
            self.noelTexturesPy._t2_n4,
            self.gt_t2_reg,
            metric_type='correlation',
        )
        print('correlation of the current t2 with the ground truth: {}'.format(metric))
        # set relative tolerance to 0.1
        # predicted image is expected to have overlap within 0.1
        nptest.assert_allclose(1.0, metric, rtol=0.1, atol=0.1)

    def test_skull_stripping(self):
        logger.debug('testing skull stripping')
        self.noelTexturesPy._t1file = self._t1file
        self.noelTexturesPy._t2file = self._t2file
        self.noelTexturesPy.load_nifti_file()
        self.noelTexturesPy.register_to_MNI_space()
        self.noelTexturesPy.bias_correction()
        self.noelTexturesPy.skull_stripping()
        self.assertIsInstance(self.noelTexturesPy._mask, ants.core.ants_image.ANTsImage)

    def test_segmentation(self):
        logger.debug('testing tissue segmentation')
        self.noelTexturesPy._t1file = self._t1file
        self.noelTexturesPy._t2file = self._t2file
        self.noelTexturesPy.load_nifti_file()
        self.noelTexturesPy.register_to_MNI_space()
        self.noelTexturesPy.bias_correction()
        self.noelTexturesPy.skull_stripping()
        self.noelTexturesPy.segmentation()
        self.assertIsInstance(self.noelTexturesPy._segm, ants.core.ants_image.ANTsImage)
        self.assertIsInstance(self.noelTexturesPy._gm, np.ndarray)
        self.assertIsInstance(self.noelTexturesPy._wm, np.ndarray)

    def test_gradient_magnitude(self):
        logger.debug('testing gradient magnitude')
        self.noelTexturesPy._t1file = self._t1file
        self.noelTexturesPy._t2file = self._t2file
        self.noelTexturesPy.load_nifti_file()
        self.noelTexturesPy.register_to_MNI_space()
        self.noelTexturesPy.bias_correction()
        self.noelTexturesPy.gradient_magnitude()
        self.assertIsInstance(
            self.noelTexturesPy._grad_t1, ants.core.ants_image.ANTsImage
        )
        self.assertTrue(
            os.path.exists(
                os.path.join(
                    os.path.join(
                        self._outputdir, f'{self._id}_t1_gradient_magnitude.nii'
                    )
                )
            )
        )

        metric = compare_images(
            self.noelTexturesPy._grad_t1,
            self.gt_gm,
            metric_type='correlation',
        )
        print(
            'correlation of the current t1 gradient magnitude with the ground truth: {}'.format(
                metric
            )
        )
        # set relative tolerance to 0.1
        # predicted image is expected to have overlap within 0.1
        nptest.assert_allclose(1.0, metric, rtol=0.1, atol=0.1)

    def test_relative_intensity(self):
        logger.debug('testing relative intensity')
        self.noelTexturesPy._t1file = self._t1file
        self.noelTexturesPy._t2file = self._t2file
        self.noelTexturesPy.load_nifti_file()
        self.noelTexturesPy.register_to_MNI_space()
        self.noelTexturesPy.bias_correction()
        self.noelTexturesPy.skull_stripping()
        self.noelTexturesPy.segmentation()
        self.noelTexturesPy.relative_intensity()
        self.assertIsInstance(self.noelTexturesPy._ri, ants.core.ants_image.ANTsImage)
        self.assertTrue(
            os.path.exists(
                os.path.join(
                    os.path.join(
                        self._outputdir, f'{self._id}_t1_relative_intensity.nii'
                    )
                )
            )
        )

        metric = compare_images(
            self.noelTexturesPy._ri,
            self.gt_ri,
            metric_type='correlation',
        )
        print(
            'correlation of the current t1 relative intensity with the ground truth: {}'.format(
                metric
            )
        )
        # set relative tolerance to 0.1
        # predicted image is expected to have overlap within 0.1
        nptest.assert_allclose(1.0, metric, rtol=0.1, atol=0.1)

    def test_generate_QC_maps(self):
        logger.debug('testing generation of QC maps')
        self.noelTexturesPy._t1file = self._t1file
        self.noelTexturesPy._t2file = self._t2file
        self.noelTexturesPy.load_nifti_file()
        self.noelTexturesPy.register_to_MNI_space()
        self.noelTexturesPy.bias_correction()
        self.noelTexturesPy.skull_stripping()
        self.noelTexturesPy.segmentation()
        self.noelTexturesPy.generate_QC_maps()
        self.assertTrue(
            os.path.exists(os.path.join(self._outputdir, f'{self._id}_QC_report.pdf'))
        )

    def tearDown(self):
        try:
            shutil.rmtree(self._outputdir)
        except OSError as e:
            print(f'Error deleting directory: {e}')
            pass
        else:
            pass


if __name__ == '__main__':
    unittest.main()
