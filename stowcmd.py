#/usr/local/bin/python

from __future__ import print_function
import sys
import os
from errno import ENOENT

#######################################################################
# Defaults, you can override these with a ".../stow.cfg" file.
#

# Files larger than huge_size are segmented in huge_size bits
huge_size       =       1024 * 1024

# Compression level for zlib (1=worst,fast, 6=default, 9=best,slow)
zlib_level      =       6

# Maximum size of silos (XXX: approximate)
# 3 Gigabytes to leave outher rim of DVD's unused.
max_silo        =       3 * 1024 * 1024 * 1024

#######################################################################
# Read local settings, if any...

try:
	execfile("stow.cfg")
except IOError as e:
	if e.errno != ENOENT:
		raise

#######################################################################
# Find our code & classes

sys.path.insert(0, "python")

if __name__ != "__main__":
	sys.stderr.write("Sorry, wrong use\n")
	exit (2)

if len(sys.argv) == 1:
	sys.stderr.write("Needs argument\n")
	exit (2)

if sys.argv[1] == "stevedore":
	import stow_stevedore
	exit (2)

sys.stderr.write("Wrong argument\n")
exit (2)
