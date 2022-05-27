import os, random, string
import numpy as np
import ants
from collections import Counter

def write_nifti(input, id, output_dir, type):
    output_fname = os.path.join(output_dir, id + '_' + type + '.nii.gz')
    ants.image_write( input, output_fname)

def compute_RI(image, bg, mask):
    ri = np.zeros_like(image)
    bgm = np.stack(np.where(np.logical_and(image < bg, mask == 1)), axis=1)
    bgm_ind = bgm[:,0], bgm[:,1], bgm[:,2]
    bgp = np.stack(np.where(np.logical_and(image > bg, mask == 1)), axis=1)
    bgp_ind = bgp[:,0], bgp[:,1], bgp[:,2]

    ri[bgm_ind] = 100 * (1 - (bg - image[bgm_ind]) / bg )
    ri[bgp_ind] = 100 * (1 + (bg - image[bgp_ind]) / bg )
    return ri

def peakfinder(gm, wm, lower_q, upper_q):
    gm_peak = Counter(threshold_percentile(gm, lower_q, upper_q)).most_common(1)[0][0]
    wm_peak = Counter(threshold_percentile(wm, lower_q, upper_q)).most_common(1)[0][0]
    bg = 0.5 * (gm_peak + wm_peak)
    return bg, gm_peak, wm_peak

def threshold_percentile(x, lower_q, upper_q):
    x = x.numpy()
    lq = np.percentile(x, lower_q)
    uq = np.percentile(x, upper_q)
    x = x[np.logical_and(x>lq, x<=uq)]
    return x.flatten().round()

def find_logger_basefilename(logger):
    """Finds the logger base filename(s) currently there is only one
    """
    log_file = None
    handler = logger.handlers[0]
    log_file = handler.baseFilename
    return log_file

def random_case_id():
    letters = ''.join(random.choices(string.ascii_letters, k=16))
    digits  = ''.join(random.choices(string.digits, k=16))
    x = letters[:3].lower() + '_' + digits[:4]
    return x
