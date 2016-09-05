#!/usr/bin/env python

import os
import sys
import shutil

lib_dir = sys.argv[1]
shutil.copyfile(os.path.join(lib_dir, "jconfig.txt"), os.path.join(lib_dir, "jconfig.h"))
