#!/usr/bin/env python

import os
import subprocess
import urllib.request

cache = os.path.join(os.path.expanduser('~'), '.antstorch')
os.makedirs(cache, exist_ok=True)
files = [
    (
        'S_template3.nii.gz',
        'https://ndownloader.figshare.com/files/22597175',
        'bfaec60f931141f983f39c450d7b3059286809148ba3c5a744add755756958cd',
    ),
    (
        'brainExtractionRobustT1_pytorch.pt',
        'https://ndownloader.figshare.com/files/58439353',
        'ca9fc9b73080656c1302dabd1f4b028e4753514088634c76d0e6253efacb614f',
    ),
    (
        'brainExtractionRobustT2_pytorch.pt',
        'https://ndownloader.figshare.com/files/58439389',
        '65b10e40ab0b6f56e12434b78761fd4d8e240822316b28a7ea0032066ff37c63',
    ),
]
print('Downloading the following files:')
for fname, url, sha256 in files:
    print(f' {fname} from {url} with expected sha256 {sha256}')
    urllib.request.urlretrieve(url, os.path.join(cache, fname))
    result = subprocess.run(
        ['sha256sum', os.path.join(cache, fname)], capture_output=True, text=True
    )
    if sha256 not in result.stdout:
        raise ValueError(f'File {fname} did not match expected sha256 hash')
