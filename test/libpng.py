#!/usr/bin/env python

import os
import sys
import shutil

lib_dir = sys.argv[1]
shutil.copyfile(os.path.join(lib_dir, "scripts", "pnglibconf.h.prebuilt"), os.path.join(lib_dir, "pnglibconf.h"))
