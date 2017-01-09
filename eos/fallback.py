try:
    from urllib.request import urlparse
    from urllib.request import urlunparse
except ImportError:
    from urlparse import urlparse
    from urlparse import urlunparse
import os
import shutil

import eos.archive
import eos.cache
import eos.constants
import eos.util


def download_from_fallback_url(fallback_url, filename, relative_src_dir, download_dir, extract_dir,
                               sha1_hash_expected=None):
    p = urlparse(fallback_url)
    new_path = p[2] + "/" + relative_src_dir + "/" + filename
    fallback_download_url = urlunparse([p[0], p[1], new_path, p[3], p[4], p[5]])

    download_filename = eos.util.download_file(fallback_download_url, download_dir,
                                               sha1_hash_expected=sha1_hash_expected)
    if download_filename == "":
        eos.log_error("downloading of file from fallback URL " + fallback_download_url + " failed")
        return False

    if extract_dir is not None:
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)

        if not eos.archive.extract_file(download_filename, extract_dir):
            eos.log_error("extraction of file " + download_filename + " from fallback URL " + fallback_download_url
                          + " failed")
            return False

    return True
