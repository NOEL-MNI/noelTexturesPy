import logging
import os
from tempfile import mkdtemp

from noelTexturesPy.utils import random_case_id


def custom_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    case_id = random_case_id()
    os.environ['TEMPDIR'] = os.environ.get('TEMPDIR', mkdtemp(prefix=f'{case_id}_'))
    TEMPDIR = os.environ.get('TEMPDIR')

    log_filename = os.path.join(TEMPDIR, str(case_id) + '.log')

    # create a file handler
    try:
        # check if the log file exists, and create it if not
        if not os.path.exists(TEMPDIR):
            os.makedirs(TEMPDIR)
        if not os.path.exists(log_filename):
            with open(log_filename, 'w') as f:
                pass  # create a new empty file
    except OSError as e:
        print('error: %s - %s.' % (e.filename, e.strerror))

    handler = logging.FileHandler(log_filename)
    handler.setLevel(logging.INFO)

    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(handler)

    logger.info(f'logger has been initialized, logfile: {log_filename}')
    return logger, log_filename, case_id
