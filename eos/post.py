import os

import eos.log
import eos.tools
import eos.util


def apply_patch(library_name, library_dir, patch_file, pnum):
    # We're assuming the patch was applied like in this example:
    # diff --exclude=".git" --exclude=".hg" -rupN ./LIBNAME ./LIBNAME_patched > libname.patch
    # where the first given location is the unpatched directory, and the second location is the patched directory.
    eos.log_verbose("Applying patch file " + patch_file + " to library '" + library_name + "'...")

    arguments = "-d " + library_dir + " -p" + str(pnum) + " < " + patch_file
    arguments_binary = "-d " + library_dir + " -p" + str(pnum) + " --binary < " + patch_file

    print_cmd = eos.verbosity() > 0

    status = eos.util.execute_command(eos.tools.command_patch() + " --dry-run " + arguments,
                                      print_command=print_cmd, quiet=True)

    if status != 0:
        # try again in binary mode
        arguments = arguments_binary
        status = eos.util.execute_command(eos.tools.command_patch() + " --dry-run " + arguments,
                                       print_command=print_cmd, quiet=True)

    if status != 0:
        eos.log_error("patch application failure; has this patch already been applied?")
        eos.util.execute_command(eos.tools.command_patch() + " --dry-run " + arguments, print_command=True)
        return False

    status = eos.util.execute_command(eos.tools.command_patch() + " " + arguments,
                                      print_command=print_cmd, quiet=True)
    return status == 0


def run_script(library_name, script_command):
    eos.log_verbose("Running script '" + script_command + "' as post-processing for library '"
                    + library_name + "'...")
    _, ext = os.path.splitext(script_command.split(' ')[0])
    cmd = script_command
    if ext == '.py':
        cmd = eos.tools.command_python() + " " + script_command
    print_cmd = eos.verbosity() > 0
    status = eos.util.execute_command(cmd, print_command=print_cmd)
    return status == 0
