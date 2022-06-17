import os
os.environ["CUDA_VISIBLE_DEVICES"]="-1"
import sys
import time
import logging
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import ants
from antspynet.utilities import brain_extraction
import numpy as np
import multiprocessing
# import zipfile
from PIL import Image
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


    def __register_to_MNI_space(self):
        logger.info("registration to MNI template space")
        print("registration to MNI template space")
        if self._t1file != None and self._t2file != None:
            self._t1_reg = ants.registration( fixed = self._icbm152, moving = self._t1, type_of_transform = 'Affine', aff_metric = 'GC' )
            self._t2_reg = ants.apply_transforms(fixed = self._icbm152, moving = self._t2, transformlist = self._t1_reg['fwdtransforms'])

        if self._t1file != None and self._t2file == None:
            self._t1_reg = ants.registration( fixed = self._icbm152, moving = self._t1, type_of_transform = 'Affine', aff_metric = 'GC' )

        if self._t2file != None and self._t1file == None:
            self._t2_reg = ants.registration( fixed = self._icbm152, moving = self._t2, type_of_transform = 'Affine' )


    def __bias_correction(self):
        logger.info("performing N4 bias correction")
        print("performing N4 bias correction")
        if self._t1file != None and self._t2file != None:
            self._t1_n4 = ants.iMath(self._t1_reg['warpedmovout'].abp_n4(intensity_truncation = (0.05, 0.95, 256), usen3 = self._usen3), "Normalize") * 100
            self._t2_n4 = ants.iMath(self._t2_reg.abp_n4(usen3 = self._usen3), "Normalize") * 100
            ants.image_write(self._t1_n4, os.path.join(self._outputdir, self._id+'_t1_final.nii.gz'))
            ants.image_write(self._t2_n4, os.path.join(self._outputdir, self._id+'_t2_final.nii.gz'))

        if self._t1file != None and self._t2file == None:
            self._t1_n4 = ants.iMath(self._t1_reg['warpedmovout'].abp_n4(intensity_truncation = (0.05, 0.95, 256), usen3 = self._usen3), "Normalize") * 100
            ants.image_write(self._t1_n4, os.path.join(self._outputdir, self._id+'_t1_final.nii.gz'))

        if self._t2file != None and self._t1file == None:
            self._t2_n4 = ants.iMath(self._t2_reg['warpedmovout'].abp_n4(usen3 = self._usen3), "Normalize") * 100
            ants.image_write(self._t2_n4, os.path.join(self._outputdir, self._id+'_t2_final.nii.gz'))


    def __skull_stripping(self):
        logger.info("performing brain extraction")
        print("performing brain extraction")
        if self._t1file != None and self._t2file != None:
            self._modality = "t1"
            self._mask = self.__brain_extraction()

        if self._t1file != None and self._t2file == None:
            self._modality = "t1"
            self._mask = self.__brain_extraction()

        if self._t2file != None and self._t1file == None:
            self._modality = "t2"
            self._mask = self.__brain_extraction()


    def __segmentation(self):
        logger.info("computing GM, WM, CSF segmentation")
        print("computing GM, WM, CSF segmentation")
        # https://antsx.github.io/ANTsPyNet/docs/build/html/utilities.html#applications

        priors = {
                    "csf": os.path.join('./templates', 'mni_icbm152_csf_tal_nlin_sym_09a.nii.gz'),
                    "gm" : os.path.join('./templates', 'mni_icbm152_gm_tal_nlin_sym_09a.nii.gz'),
                    "wm" : os.path.join('./templates', 'mni_icbm152_wm_tal_nlin_sym_09a.nii.gz')
                 }
        # list_of_priors = (ants.image_read(priors['csf']), ants.image_read(priors['gm']), ants.image_read(priors['wm']))
        
        if self._t1file != None and self._t2file != None:
            # segm = deep_atropos(self._t1_n4 * self._mask, do_preprocessing=False, use_spatial_priors=0, verbose=False)
            # self._segm = segm['segmentation_image']
            segm = ants.atropos(a=(self._t1_n4, self._t2_n4), i='Kmeans[3]', m='[0.2,1x1x1]', c='[3,0]', x=self._mask)
            self._segm = segm['segmentation']
            self._gm = np.where((self._segm.numpy() == 2), 1, 0).astype('float32')
            self._wm = np.where((self._segm.numpy() == 3), 1, 0).astype('float32')

        if self._t1file != None and self._t2file == None:
            # segm = deep_atropos(self._t1_n4 * self._mask, do_preprocessing=False, use_spatial_priors=0, verbose=False)
            # self._segm = segm['segmentation_image']
            segm = ants.atropos(a=self._t1_n4, i='Kmeans[3]', m='[0.2,1x1x1]', c='[3,0]', x=self._mask)
            self._segm = segm['segmentation']
            self._gm = np.where((self._segm.numpy() == 2), 1, 0).astype('float32')
            self._wm = np.where((self._segm.numpy() == 3), 1, 0).astype('float32')

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

        if self._t1file != None and self._t2file == None:
            t1_n4_gm = self._t1_n4 * self._t1_n4.new_image_like(self._gm)
            t1_n4_wm = self._t1_n4 * self._t1_n4.new_image_like(self._wm)
            bg_t1 = peakfinder(t1_n4_gm, t1_n4_wm, 1, 99.5)
            t1_ri = compute_RI(self._t1_n4.numpy(), bg_t1, self._mask.numpy())
            tmp = self._t1_n4.new_image_like(t1_ri)
            self._ri = ants.smooth_image(tmp, sigma=3, FWHM=True)
            ants.image_write( self._ri, os.path.join(self._outputdir, self._id+'_t1_relative_intensity.nii.gz'))

    def __generate_QC_maps(self):
        logger.info('generating QC report')
        if not os.path.exists('./qc'):
            os.makedirs('./qc')
        if self._t1file != None and self._t2file != None:
            self._t1_n4.plot(overlay=self._mask, overlay_alpha=0.5, axis=2, ncol=8, nslices=32, title='Brain Masking', filename='./qc/001_brain_masking.png', dpi=300)
            self._t1_n4.plot(overlay=self._segm, overlay_cmap='gist_rainbow', overlay_alpha=0.5, axis=2, ncol=8, nslices=32, title='Segmentation', filename='./qc/002_segmentation.png', dpi=300)

        if self._t1file != None and self._t2file == None:
            self._t1_n4.plot(overlay=self._mask, overlay_alpha=0.5, axis=2, ncol=8, nslices=32, title='Brain Masking', filename='./qc/001_brain_masking.png', dpi=300)
            self._t1_n4.plot(overlay=self._segm, overlay_cmap='gist_rainbow', overlay_alpha=0.5, axis=2, ncol=8, nslices=32, title='Segmentation', filename='./qc/002_segmentation.png', dpi=300)

        if self._t1file != None or self._t2file != None:
            with PdfPages(os.path.join(self._outputdir, self._id+"_QC_report.pdf")) as pdf:
                for i in sorted(os.listdir('./qc')):
                    if i.endswith(".png"):
                        plt.figure()
                        img = Image.open(os.path.join('./qc', i))
                        plt.imshow(img)
                        plt.axis('off')
                        pdf.savefig(dpi=300)
                        plt.close()
                        os.remove(os.path.join('./qc', i))


    def __brain_extraction(self):
        # https://antsx.github.io/ANTsPyNet/docs/build/html/utilities.html#applications
        if self._modality == "t1":
            image = self._t1_n4
        elif self._modality == "t2":
            image = self._t2_n4
        else:
            sys.exit("invalid contrast specified for brain extraction")

        prob = brain_extraction(image, modality=self._modality)
        # mask can be obtained as:
        mask = ants.threshold_image(prob, low_thresh=0.5, high_thresh=1.0, inval=1, outval=0, binary=True)
        return mask


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
