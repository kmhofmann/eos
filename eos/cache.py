import os

import eos.constants

CACHE_DIR = None
ARCHIVE_DIR = None


def init_cache_dir(cache_dir):
    global CACHE_DIR
    global ARCHIVE_DIR
    assert cache_dir

    CACHE_DIR = cache_dir
    if not os.path.isdir(CACHE_DIR):
        os.mkdir(CACHE_DIR)

    ARCHIVE_DIR = os.path.join(CACHE_DIR, eos.constants.ARCHIVES_SUBDIR_REL)
    if not os.path.isdir(ARCHIVE_DIR):
        os.mkdir(ARCHIVE_DIR)


def get_cache_dir():
    return CACHE_DIR


def get_archive_dir():
    return ARCHIVE_DIR
