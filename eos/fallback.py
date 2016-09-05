try:
    from urllib.request import urlparse
    from urllib.request import urlunparse
    from urllib.request import urlretrieve
    from urllib.request import URLopener
    from urllib.request import quote
except ImportError:
    from urlparse import urlparse
    from urlparse import urlunparse
    from urllib import urlretrieve
    from urllib import URLopener
    from urllib import quote
import os

import eos.archive
import eos.cache
import eos.constants
import eos.util


def download_and_extract_from_fallback_url(fallback_url, archive_filename, download_dir, extract_dir, sha1_hash_expected=None):
    p = urlparse(fallback_url)
    new_path = p[2] + "/" + eos.cache.get_archive_dir() + "/" + archive_filename
    fallback_download_url = urlunparse([p[0], p[1], new_path, p[3], p[4], p[5]])

    download_filename = eos.util.download_file(fallback_download_url, eos.cache.get_archive_dir(),
                                               sha1_hash_expected=sha1_hash_expected)
    if download_filename == "":
        eos.log_error("downloading of file from fallback URL " + fallback_download_url + " failed")
        return False

    if not eos.archive.extract_file(download_filename, extract_dir):
        eos.log_error("extraction of file " + download_filename + " from fallback URL " + fallback_download_url
                      + " failed")
        return False

    return True
