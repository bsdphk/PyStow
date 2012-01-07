"""List archive index
"""

from __future__ import print_function

import sys
import time

import archive

this = archive.archive()

for i in this.idx:
	if i[:5] != "INDEX":
		continue
	i,m,o = this.get_entry(i)
	assert m == "mtree"
	o = o.splitlines()
	print(i, time.ctime(int(o[1])), o[0])
