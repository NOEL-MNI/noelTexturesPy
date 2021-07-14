import os, sys, time, logging
import matplotlib as mpl
mpl.use("Qt5Agg")
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import ants
import numpy as np
import multiprocessing
import zipfile
from PIL import Image
from skimage.filters import threshold_otsu
from utils import *


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# logfile = './logs.log'
logfile = os.path.join('.', str(random_case_id())+'.log')
# create a file handler
try:
    os.remove(logfile)
except OSError as e:
    print("Error: %s - %s." % (e.filename, e.strerror))

handler = logging.FileHandler(logfile)
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

os.environ[ "ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS" ] = str(multiprocessing.cpu_count())
os.environ[ "ANTS_RANDOM_SEED" ] = "666"


class noelTexturesPy:
    def __init__(self, id, t1=None, t2=None, output_dir=None, template=None, usen3=False):
        super(noelTexturesPy, self).__init__()
        self._id            = id
        self._t1file        = t1
        self._t2file        = t2
        self._outputdir     = output_dir
        self._template      = template
        self._usen3         = usen3

    def __load_nifti_file(self):
    	# load nifti data to memory
        logger.info("loading nifti files")
        print("loading nifti files")
        self._mni = self._template

        if self._t1file == None and self._t2file == None:
        	logger.warn("Please load the data first.", "The data is missing")
        	return

        if self._t1file != None and self._t2file != None:
            self._t1 = ants.image_read( self._t1file )
            self._t2 = ants.image_read( self._t2file )
            self._icbm152 = ants.image_read( self._mni )

        if self._t1file != None and self._t2file == None:
            self._t1 = ants.image_read( self._t1file )
            self._icbm152 = ants.image_read( self._mni )

        if self._t2file != None and self._t1file == None:
            self._t2 = ants.image_read( self._t2file )
            self._icbm152 = ants.image_read( self._mni )


    def __load_dicoms(self):
    	# load nifti data to memory
        logger.info("loading dicom files from directory")
        print("loading dicom files from directory")
        self._mni = self._template

        if self._t1file == None and self._t2file == None:
        	logger.warn("Please load the data first.", "The data is missing")
        	return

        if self._t1file != None and self._t2file != None:
            self._t1 = ants.dicom_read( self._t1file )
            self._t2 = ants.dicom_read( self._t2file )
            self._icbm152 = ants.image_read( self._mni )

        if self._t1file != None and self._t2file == None:
            self._t1 = ants.dicom_read( self._t1file )
            self._icbm152 = ants.image_read( self._mni )

        if self._t2file != None and self._t1file == None:
            self._t2 = ants.dicom_read( self._t2file )
            self._icbm152 = ants.image_read( self._mni )


    def __register_to_MNI_space(self):
        logger.info("registration to MNI template space")
        print("registration to MNI template space")
        if self._t1file != None and self._t2file != None:
            self._t1_reg = ants.registration( fixed = self._icbm152, moving = self._t1, type_of_transform = 'Affine' )
            self._t2_reg = ants.apply_transforms(fixed = self._icbm152, moving = self._t2, transformlist = self._t1_reg['fwdtransforms'])
            ants.image_write( self._t1_reg['warpedmovout'], os.path.join(self._outputdir, self._id+'_t1_final.nii.gz'))
            ants.image_write( self._t2_reg, os.path.join(self._outputdir, self._id+'_t2_final.nii.gz'))

        if self._t1file != None and self._t2file == None:
            self._t1_reg = ants.registration( fixed = self._icbm152, moving = self._t1, type_of_transform = 'Affine' )
            ants.image_write( self._t1_reg['warpedmovout'], os.path.join(self._outputdir, self._id+'_t1_final.nii.gz'))

        if self._t2file != None and self._t1file == None:
            self._t2_reg = ants.registration( fixed = self._icbm152, moving = self._t2, type_of_transform = 'Affine' )
            ants.image_write( self._t2_reg['warpedmovout'], os.path.join(self._outputdir, self._id+'_t2_final.nii.gz'))


    def __scale(X, *args):
        x_min = np.percentile(X.numpy(), lower_q)
        x_max = np.percentile(X.numpy(), upper_q)
        Y = 100*( X.numpy() - X.numpy().min(axis=0) ) / (x_max-x_min)
        return X.new_image_like(Y)


    def __bias_correction(self):
        logger.info("performing N4 bias correction")
        print("performing N4 bias correction")
        if self._t1file != None and self._t2file != None:
            # self._t1_n4 = ants.iMath(self._t1_reg['warpedmovout'].abp_n4(intensity_truncation=(0.01, 0.99, 1024), usen3 = self._usen3), "Normalize") * 100
            # self._t2_n4 = ants.iMath(self._t2_reg.abp_n4(intensity_truncation=(0.01, 0.99, 1024), usen3 = self._usen3), "Normalize") * 100
            self._t1_n4 = ants.iMath(self._t1_reg['warpedmovout'].abp_n4(usen3 = self._usen3), "Normalize") * 100
            self._t2_n4 = ants.iMath(self._t2_reg.abp_n4(usen3 = self._usen3), "Normalize") * 100

        if self._t1file != None and self._t2file == None:
            # self._t1_n4 = ants.iMath(self._t1_reg['warpedmovout'].abp_n4(intensity_truncation=(0.01, 0.99, 1024), usen3 = self._usen3), "Normalize") * 100
            # self._t1_n4 = ants.n4_bias_field_correction(self._t1_reg['warpedmovout'], shrink_factor=4, convergence={'iters': [100,100,100,100], 'tol': 1e-07})
            # self._t1_n4 = self._t1_n4.iMath_truncate_intensity(0.025, 0.975, n_bins=256).iMath_normalize() * 100
            self._t1_n4 = ants.iMath(self._t1_reg['warpedmovout'].abp_n4(usen3 = self._usen3), "Normalize") * 100
            # min, max = self._t1_n4.numpy().min(), self._t1_n4.numpy().max()
            # tmp = 100 * ( self._t1_n4.numpy() - min ) / max - min
            # self._t1_n4 = self._t1_reg['warpedmovout'].new_image_like(tmp)
            # self._t1_n4 = self.__scale(self._t1_n4, 0.01, 99.99)

        if self._t2file != None and self._t1file == None:
            self._t2_n4 = ants.iMath(self._t2_reg['warpedmovout'].abp_n4(usen3 = self._usen3), "Normalize") * 100


    def __skull_stripping(self):
        logger.info("performing brain extraction")
        print("performing brain extraction")
        if self._t1file != None and self._t2file != None:
            self._mask = ants.get_mask( self._t1_n4, cleanup = 5 ).threshold_image( 1, 2 ).iMath_fill_holes(3).iMath_fill_holes(6)

        if self._t1file != None and self._t2file == None:
            low_thresh = threshold_otsu(self._t1_n4.numpy())
            self._mask = ants.get_mask( self._t1_n4, low_thresh=low_thresh).iMath_fill_holes(6)
            # self._mask = ants.image_read('./templates/mcd_134_1_ANTsBrainExtractionMask.nii.gz')
            # self._mask = ants.get_mask( self._t1_n4, cleanup = 5 ).threshold_image( 1, 2 ).iMath_fill_holes(3)

        if self._t2file != None and self._t1file == None:
            self._mask = ants.get_mask( self._t2_n4, cleanup = 5 ).threshold_image( 1, 2 ).iMath_fill_holes(3).iMath_fill_holes(6)


    def __segmentation(self):
        logger.info("computing GM, WM, CSF segmentation")
        print("computing GM, WM, CSF segmentation")
        if self._t1file != None and self._t2file != None:
            segm = ants.atropos( a = self._t1_n4, m = '[0.2,1x1x1]', c = '[2,0]',  i = 'kmeans[3]', x = self._mask )
            self._segm = segm['segmentation']
            self._gm = np.where((self._segm.numpy() == 2), 1, 0).astype('float32')
            self._wm = np.where((self._segm.numpy() == 3), 1, 0).astype('float32')

        if self._t1file != None and self._t2file == None:
            segm = ants.atropos( a = self._t1_n4, m = '[0.2,1x1x1]', c = '[2,0]',  i = 'kmeans[3]', x = self._mask )
            self._segm = segm['segmentation']
            # self._segm = ants.image_read('./templates/mcd_134_1_ANTsBrainExtractionSegmentation.nii.gz')
            self._gm = np.where((self._segm.numpy() == 2), 1, 0).astype('float32')
            self._wm = np.where((self._segm.numpy() == 3), 1, 0).astype('float32')
            # ants.image_write( self._segm, os.path.join(self._outputdir, self._id+'_segmentation.nii.gz'))

        # if self._t2file != None and self._t1file == None:
        #     segm = ants.atropos( a = self._t2_reg['warpedmovout'], m = '[0.2,1x1x1]', c = '[2,0]',  i = 'kmeans[3]', x = self._mask )
        #     self._segm = segm['segmentation']
        #     self._gm = np.where((self._segm.numpy() == 2), 1, 0).astype('float32')
        #     self._wm = np.where((self._segm.numpy() == 3), 1, 0).astype('float32')
            # ants.image_write( self._segm, os.path.join(self._outputdir, self._id+'_segmentation.nii.gz'))


    def __gradient_magnitude(self):
        logger.info("computing gradient magnitude")
        print("computing gradient magnitude")
        if self._t1file != None and self._t2file != None:
            self._grad_t1 = ants.iMath(self._t1_n4, "Grad", 1)
            # self._grad_t2 = ants.iMath(self._t2_n4, "Grad", 1)
            ants.image_write( self._grad_t1, os.path.join(self._outputdir, self._id+'_t1_gradient_magnitude.nii.gz'))
            # ants.image_write( self._grad_t1, os.path.join(self._outputdir, self._id+'_t2_gradient_magnitude.nii.gz'))

        if self._t1file != None and self._t2file == None:
            self._grad_t1 = ants.iMath(self._t1_n4, "Grad", 1)
            ants.image_write( self._grad_t1, os.path.join(self._outputdir, self._id+'_t1_gradient_magnitude.nii.gz'))

        # if self._t2file != None and self._t1file == None:
        #     self._grad_t2 = ants.iMath(self._t2_n4, "Grad", 1)
            # ants.image_write( self._grad_t2, os.path.join(self._outputdir, self._id+'_t2_gradient_magnitude.nii.gz'))


    def __relative_intensity(self):
        logger.info('computing relative intensity')
        print('computing relative intensity')
        if self._t1file != None and self._t2file != None:
            t1_n4_gm = self._t1_n4 * self._t1_n4.new_image_like(self._gm)
            t1_n4_wm = self._t1_n4 * self._t1_n4.new_image_like(self._wm)
            bg_t1 = peakfinder(t1_n4_gm, t1_n4_wm, 1, 99.5)
            t1_ri = compute_RI(self._t1_n4.numpy(), bg_t1, self._mask.numpy())
            tmp = self._t1_n4.new_image_like(t1_ri)
            self._ri = ants.smooth_image(tmp, sigma=3, FWHM=True)
            ants.image_write( self._ri, os.path.join(self._outputdir, self._id+'_t1_relative_intensity.nii.gz'))

            # t2_n4_gm = self._t2_n4 * self._t1_n4.new_image_like(self._gm)
            # t2_n4_wm = self._t2_n4 * self._t1_n4.new_image_like(self._wm)
            # bg_t2 = peakfinder(t2_n4_gm, t2_n4_wm, 1, 99.5)
            # t2_ri = compute_RI(self._t2_n4.numpy(), bg_t2,self._mask.numpy())
            # tmp = self._t2_n4.new_image_like(t2_ri)
            # tmp = ants.smooth_image(tmp, sigma=3, FWHM=True)
            # ants.image_write( tmp, os.path.join(self._outputdir, self._id+'_t2_relative_intensity.nii.gz'))

        if self._t1file != None and self._t2file == None:
            t1_n4_gm = self._t1_n4 * self._t1_n4.new_image_like(self._gm)
            t1_n4_wm = self._t1_n4 * self._t1_n4.new_image_like(self._wm)
            bg_t1 = peakfinder(t1_n4_gm, t1_n4_wm, 1, 99.5)
            t1_ri = compute_RI(self._t1_n4.numpy(), bg_t1, self._mask.numpy())
            tmp = self._t1_n4.new_image_like(t1_ri)
            self._ri = ants.smooth_image(tmp, sigma=3, FWHM=True)
            ants.image_write( self._ri, os.path.join(self._outputdir, self._id+'_t1_relative_intensity.nii.gz'))

        # if self._t2file != None and self._t1file == None:
        #     t2_n4_gm = self._t2_n4 * self._t2_n4.new_image_like(self._gm)
        #     t2_n4_wm = self._t2_n4 * self._t2_n4.new_image_like(self._wm)
        #     bg_t2 = peakfinder(t2_n4_gm, t2_n4_wm, 1, 99.5)
        #     t2_ri = compute_RI(self._t2_n4.numpy(), bg_t2,self._mask.numpy())
        #     tmp = self._t2_n4.new_image_like(t2_ri)
        #     tmp = ants.smooth_image(tmp, sigma=3, FWHM=True)
        #     ants.image_write( tmp, os.path.join(self._outputdir, self._id+'_t2_relative_intensity.nii.gz'))

    def __generate_QC_maps(self):
        logger.info('generating QC report')
        if not os.path.exists('./qc'):
            os.makedirs('./qc')
        if self._t1file != None and self._t2file != None:
            self._icbm152.plot(overlay=self._t1, overlay_alpha=0.5, axis=2, ncol=8, nslices=32, title='T1w - Before Registration', filename='./qc/000_t1_before_registration.png', dpi=450)
            self._icbm152.plot(overlay=self._t1_reg['warpedmovout'], overlay_alpha=0.5, axis=2, ncol=8, nslices=32, title='T1w - After Registration', filename='./qc/001_t1_after_registration.png', dpi=450)
            self._icbm152.plot(overlay=self._t2, overlay_alpha=0.5, axis=2, ncol=8, nslices=32, title='T2w - Before Registration', filename='./qc/002_t2_before_registration.png', dpi=450)
            self._icbm152.plot(overlay=self._t2_reg, overlay_alpha=0.5, axis=2, ncol=8, nslices=32, title='T2w - After Registration', filename='./qc/003_t2_after_registration.png', dpi=450)

            ants.plot(self._t1_reg['warpedmovout'], axis=2, ncol=8, nslices=32, cmap='jet', title='T1w - Before Bias Correction', filename='./qc/004_t1_before_bias_correction.png', dpi=450)
            ants.plot(self._t1_n4, axis=2, ncol=8, nslices=32, cmap='jet', title='T1w - After Bias Correction', filename='./qc/005_t1_after_bias_correction.png', dpi=450)
            ants.plot(self._t2_reg, axis=2, ncol=8, nslices=32, cmap='jet', title='T2w - Before Bias Correction', filename='./qc/006_t2_before_bias_correction.png', dpi=450)
            ants.plot(self._t2_n4, axis=2, ncol=8, nslices=32, cmap='jet', title='T2w - After Bias Correction', filename='./qc/007_t2_after_bias_correction.png', dpi=450)

            self._t1_n4.plot(overlay=self._mask, overlay_alpha=0.5, axis=2, ncol=8, nslices=32, title='Brain Masking', filename='./qc/008_brain_masking.png', dpi=450)
            self._t1_n4.plot(overlay=self._segm, overlay_cmap='gist_rainbow', overlay_alpha=0.5, axis=2, ncol=8, nslices=32, title='Segmentation', filename='./qc/009_segmentation.png', dpi=450)

            # tmp = ants.iMath(self._ri.threshold_image(80,100), "Normalize") * 100
            ants.plot(self._ri, axis=2, ncol=8, nslices=32, cmap='nipy_spectral', title='Relative Intensity', filename='./qc/010_relative_intensity.png', dpi=450)
            ants.plot(self._grad_t1, axis=2, ncol=8, nslices=32, cmap='hot', title='Gradient Magnitude', filename='./qc/011_gradient_map.png', dpi=450)

        if self._t1file != None and self._t2file == None:
            self._icbm152.plot(overlay=self._t1, overlay_alpha=0.5, axis=2, ncol=8, nslices=32, title='T1w - Before Registration', filename='./qc/000_t1_before_registration.png', dpi=450)
            self._icbm152.plot(overlay=self._t1_reg['warpedmovout'], overlay_alpha=0.5, axis=2, ncol=8, nslices=32, title='T1w - After Registration', filename='./qc/001_t1_after_registration.png', dpi=450)

            ants.plot(self._t1_reg['warpedmovout'], axis=2, ncol=8, nslices=32, cmap='jet', title='T1w - Before Bias Correction', filename='./qc/002_t1_before_bias_correction.png', dpi=450)
            ants.plot(self._t1_n4, axis=2, ncol=8, nslices=32, cmap='jet', title='T1w - After Bias Correction', filename='./qc/003_t1_after_bias_correction.png', dpi=450)

            self._t1_n4.plot(overlay=self._mask, overlay_alpha=0.5, axis=2, ncol=8, nslices=32, title='Brain Masking', filename='./qc/004_brain_masking.png', dpi=450)
            self._t1_n4.plot(overlay=self._segm, overlay_cmap='gist_rainbow', overlay_alpha=0.5, axis=2, ncol=8, nslices=32, title='Segmentation', filename='./qc/005_segmentation.png', dpi=450)

            # tmp = ants.iMath(self._ri.threshold_image(80,100), "Normalize") * 100
            ants.plot(self._ri, axis=2, ncol=8, nslices=32, cmap='nipy_spectral', title='Relative Intensity', filename='./qc/006_relative_intensity.png', dpi=450)
            ants.plot(self._grad_t1, axis=2, ncol=8, nslices=32, cmap='hot', title='Gradient Magnitude', filename='./qc/007_gradient_map.png', dpi=450)

        if self._t2file != None and self._t1file == None:
            self._icbm152.plot(overlay=self._t2, overlay_alpha=0.5, axis=2, ncol=8, nslices=32, title='T2w - Before Registration', filename='./qc/000_t2_before_registration.png', dpi=450)
            self._icbm152.plot(overlay=self._t2_reg['warpedmovout'], overlay_alpha=0.5, axis=2, ncol=8, nslices=32, title='T2w - After Registration', filename='./qc/001_t2_after_registration.png', dpi=450)

            ants.plot(self._t2_reg['warpedmovout'], axis=2, ncol=8, nslices=32, cmap='jet', title='T2w - Before Bias Correction', filename='./qc/002_t2_before_bias_correction.png', dpi=450)
            ants.plot(self._t2_n4, axis=2, ncol=8, nslices=32, cmap='jet', title='T2w - After Bias Correction', filename='./qc/003_t2_after_bias_correction.png', dpi=450)


        if self._t1file != None or self._t2file != None:
            with PdfPages(os.path.join(self._outputdir, self._id+"_QC_report.pdf")) as pdf:
                for i in sorted(os.listdir('./qc')):
                    if i.endswith(".png"):
                        plt.figure()
                        img = Image.open(os.path.join('./qc', i))
                        plt.imshow(img)
                        plt.axis('off')
                        pdf.savefig(dpi=450)
                        plt.close()
                        os.remove(os.path.join('./qc', i))


    def __create_zip_archive(self):
        print('creating a zip archive')
        logger.info('creating a zip archive')
        zip_archive = zipfile.ZipFile(os.path.join(self._outputdir, self._id+"_texture_maps_archive.zip"), 'w')
        for folder, subfolders, files in os.walk(self._outputdir):
            for file in files:
                if file.endswith('.nii.gz'):
                    zip_archive.write(os.path.join(folder, file), file, compress_type = zipfile.ZIP_DEFLATED)
        zip_archive.close()

    def file_processor(self):
        start = time.time()
        self.__load_nifti_file()
        self.__register_to_MNI_space()
        self.__bias_correction()
        self.__skull_stripping()
        self.__segmentation()
        self.__gradient_magnitude()
        self.__relative_intensity()
        self.__generate_QC_maps()
        # self.__create_zip_archive()
        end = time.time()
        print("pipeline processing time elapsed: {} seconds".format(np.round(end-start, 1)))
        logger.info("pipeline processing time elapsed: {} seconds".format(np.round(end-start, 1)))
        logger.info("*********************************************")
