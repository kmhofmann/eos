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
        res = eos.util.execute_command(eos.tools.command_patch() + " --dry-run " + arguments,
                                       print_command=print_cmd, quiet=True)

    if status != 0:
        eos.log_error("patch application failure; has this patch already been applied?")
        eos.util.execute_command(eos.tools.command_patch() + " --dry-run " + arguments, print_command=True)
        return False

    status = eos.util.execute_command(eos.tools.command_patch() + " " + arguments,
                                      print_command=print_cmd, quiet=True)
    return status == 0


def run_script(library_name, script_file):
    eos.log_verbose("Running Python script " + script_file + " as post-processing for library '"
                    + library_name + "'...")
    cmd = eos.tools.command_python() + " " + script_file
    print_cmd = eos.verbosity() > 0
    status = eos.util.execute_command(cmd, print_command=print_cmd)
    return status == 0
