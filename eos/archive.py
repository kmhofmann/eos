import os
import tarfile
import shutil
import zipfile
import eos.cache
import eos.log
try:
    import lzma
    lzma_available = True
except ImportError:
    lzma_available = False


def _get_cache_extract_dir(namelist, stem):
    cache_dir = eos.cache.get_cache_dir()

    # get common base directory in file paths, if one exists
    common_base_dir = os.path.commonprefix(namelist)

    # case 1: the archive files have a common base directory
    extraction_dir = cache_dir
    extracted_dir = os.path.join(extraction_dir, common_base_dir)

    # case 2: the archive files do not have a common base directory
    if common_base_dir == "":
        extraction_dir = os.path.join(cache_dir, stem)
        extracted_dir = extraction_dir

    try:
        os.makedirs(extraction_dir)
    except os.error:
        pass

    return extraction_dir, extracted_dir


def _decompress_tar_xz_file(filename_src, filename_dst):
    if not lzma_available:
        print("WARNING: Python lzma library not available; extraction of .tar.xz files may not be supported.")
        print("Installation on Ubuntu:")
        print("> apt-get install python-lzma")
        print("Installation on Mac OS X:")
        print("> brew install xz")
        print("> pip install pyliblzma")
        return False

    try:
        fs = open(filename_src, "rb")
        if not fs:
            raise RuntimeError("Opening file " + filename_src + " failed")
        fd = open(filename_dst, "wb")
        if not fd:
            raise RuntimeError("Opening file " + filename_dst + " failed")

        decompressed = lzma.decompress(fs.read())
        fd.write(decompressed)
    finally:
        fs.close()
        fd.close()

    return True


def extract_file(filename, dst_dir):
    assert not os.path.exists(dst_dir)

    eos.log_verbose("Extracting file " + filename + " to " + dst_dir)

    # get file extension to determine archive type
    stem, extension = os.path.splitext(os.path.basename(filename))

    if extension == ".zip":
        if not zipfile.is_zipfile(filename):
            eos.log_error("file '" + filename + "' is not expected zip file")
            return False

        zfile = zipfile.ZipFile(filename)
        extraction_dir, extracted_dir = _get_cache_extract_dir(zfile.namelist(), stem)
        zfile.extractall(extraction_dir)
        zfile.close()

    elif extension == ".tar" or extension == ".gz" or extension == ".bz2" or extension == ".xz":
        # special case .tar.xz format: uncompress to .tar file first
        if extension == ".xz":
            stem2, extension2 = os.path.splitext(os.path.basename(stem))
            if extension2 != ".tar":
                eos.log_error("unable to extract file " + filename)
                return False
            tar_filename = os.path.join(os.path.dirname(filename), stem)
            if not _decompress_tar_xz_file(filename, tar_filename):
                return False
            filename = tar_filename

        if not tarfile.is_tarfile(filename):
            eos.log_error("file '" + filename + "' is not expected tar file")
            return False

        tfile = tarfile.open(filename)
        extraction_dir, extracted_dir = _get_cache_extract_dir(tfile.getnames(), stem)
        tfile.extractall(extraction_dir)
        tfile.close()

    else:
        eos.log_error("unknown archive format '" + extension + "'")
        return False

    # rename extracted directory to target directory
    shutil.move(extracted_dir, dst_dir)

    if not os.path.isdir(dst_dir):
        eos.log("expected destination directory '" + dst_dir + "' does not exist; error during archive extraction")
        return False

    return True


def create_archive_from_directory(src_dir_name, archive_name, delete_existing_archive=False):
    if delete_existing_archive and os.path.exists(archive_name):
        eos.log_verbose("Removing snapshot file " + archive_name + " before creating new one")
        os.remove(archive_name)

    archive_dir = os.path.dirname(archive_name)
    if not os.path.isdir(archive_dir):
        os.mkdir(archive_dir)

    with tarfile.open(archive_name, "w:gz") as tar:
        tar.add(src_dir_name, arcname=os.path.basename(src_dir_name))
