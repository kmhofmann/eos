import os

import eos.constants

CACHE_DIR = None
ARCHIVE_DIR = None
SNAPSHOT_DIR = None


def init_cache_dir(cache_dir):
    global CACHE_DIR
    global ARCHIVE_DIR
    global SNAPSHOT_DIR
    assert cache_dir

    CACHE_DIR = cache_dir
    if not os.path.isdir(CACHE_DIR):
        os.mkdir(CACHE_DIR)

    ARCHIVE_DIR = os.path.join(CACHE_DIR, eos.constants.ARCHIVE_SUBDIR_REL)
    if not os.path.isdir(ARCHIVE_DIR):
        os.mkdir(ARCHIVE_DIR)

    SNAPSHOT_DIR = os.path.join(CACHE_DIR, eos.constants.SNAPSHOT_SUBDIR_REL)
    if not os.path.isdir(SNAPSHOT_DIR):
        os.mkdir(SNAPSHOT_DIR)


def get_cache_dir():
    return CACHE_DIR


def get_archive_dir():
    return ARCHIVE_DIR


def get_snapshot_dir():
    return SNAPSHOT_DIR


def get_relative_archive_dir():
    return os.path.join(eos.constants.CACHE_DIR_REL, eos.constants.ARCHIVE_SUBDIR_REL)


def get_relative_snapshot_dir():
    return os.path.join(eos.constants.CACHE_DIR_REL, eos.constants.SNAPSHOT_SUBDIR_REL)