import hashlib
import os
import subprocess
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

import eos.log
import shlex


def execute_command(command, print_command=False, quiet=False):
    if print_command:
        eos.log("> " + command)

    out = None
    err = None
    if quiet:
        out = open(os.devnull, 'w')
        err = open(os.devnull, 'w')

    return subprocess.call(command, shell=True, stdout=out, stderr=err)


def execute_command_capture_output(command, print_command=False):
    # https://pythonadventures.wordpress.com/2014/01/08/capture-the-exit-code-the-stdout-and-the-stderr-of-an-external-command/
    if print_command:
        eos.log("> " + command)

    args = shlex.split(command)

    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    exit_code = proc.returncode

    return exit_code, out, err


# http://stackoverflow.com/questions/22058048/hashing-a-file-in-python
def _compute_sha1_hash(filename):
    buf_size = 128 * 1024  # 128 kB chunks
    sha1 = hashlib.sha1()

    with open(filename, 'rb') as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            sha1.update(data)

    return sha1.hexdigest()


# http://stackoverflow.com/a/32234251
def is_sha1(maybe_sha):
    if len(maybe_sha) != 40:
        return False
    try:
        sha_int = int(maybe_sha, 16)
    except ValueError:
        return False
    return True


class _MyURLOpener(URLopener):
    pass


def download_file(url, dst_dir, sha1_hash_expected=None, user_agent=None):
    assert(os.path.isdir(dst_dir))

    # sanitize the URL before calling urlretrieve() below
    p = urlparse(url)
    url = urlunparse([p[0], p[1], quote(p[2]), p[3], p[4], p[5]])  # quote special characters in the path

    # get the download filename
    url_filename = os.path.split(p.path)[1]  # get the last element of the path, i.e. the filename
    download_filename = os.path.join(dst_dir, url_filename)

    # in case file already exists, try to check hash
    if os.path.exists(download_filename):
        if not sha1_hash_expected or sha1_hash_expected == "":
            eos.log_verbose("File " + download_filename + " already downloaded")
            return download_filename  # file exists, but we have no SHA1 hash to check, so just return successfully

        hash_current = _compute_sha1_hash(download_filename)
        if hash_current == sha1_hash_expected:
            eos.log_verbose("File " + download_filename + " already downloaded")
            return download_filename  # everything matches; return successfully
        eos.log_warning("hash mismatch: " + hash_current + " (current) vs. " + sha1_hash_expected + " (expected)")

    # download file
    eos.log_verbose("Downloading " + url + " to " + download_filename)

    try:
        if user_agent:
            _MyURLOpener.version = user_agent
            _MyURLOpener().retrieve(url, download_filename)
        else:
            urlretrieve(url, download_filename)
    except IOError:
        eos.log_error("retrieving file from " + url + " as '" + download_filename + "' failed")
        return ""

    # check SHA1 hash
    if sha1_hash_expected and sha1_hash_expected != "":
        hash_current = _compute_sha1_hash(download_filename)
        if hash_current != sha1_hash_expected:
            eos.log_error("hash mismatch: " + hash_current + " (current) vs. " + sha1_hash_expected + " (expected)")
            return ""

    return download_filename
