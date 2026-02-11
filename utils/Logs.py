import os
import logging

def logs_init(file_name: str):
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger('my_logger')
    logger.setLevel(logging.DEBUG)

    log_file_path = os.path.join(log_dir, file_name)
    fh = logging.FileHandler(log_file_path)
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: \n%(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    # logger.info('This is an info message')
    return logger