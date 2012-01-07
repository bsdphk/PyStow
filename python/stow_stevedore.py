#!/usr/local/bin/python
"""The stow::stevedore protocol slave
"""

from __future__ import print_function

import sys
import time

import archive

def tx(s):
	sys.stdout.write(s + "\n")
	sys.stdout.flush()

def rx():
	a = sys.stdin.readline()
	if a[-1] == "\n":
		a = a[:-1]
	return a

tx("HELLO STOW 1.0 SERVER")

cl = rx()
assert cl == "HELLO STOW 1.0 CLIENT"

tx("WELCOME PYSTOW")

nm = rx()
assert nm[:5] == "NAME "
nm = nm.split()[1]

tx("OK")

this = archive.archive()

mt = ""
while True:
	i = rx()
	j = i.split()
	assert j[0] == "MTREE"
	l = int(j[1])
	if l == 0:
		break;
	x = 0
	while x < l:
		y = sys.stdin.read(l - x)
		mt += y
		x += len(y)
		a = rx()
		assert a == ""

a = rx()
assert a == ""

tx("THANKS")

o = rx()
assert o == "OVER"


def cb_getf(path, md5):

	tx("SEND %s 0 %s" % (path, md5))
	fl = ""
	while True:
		a = rx()
		if a[:4] == "FAIL":
			return None
		assert a[:4] == "FILE"
		b = a.split()
		l = int(b[1])
		if l == 0:
			break
		x = 0
		while x < l:
			y = sys.stdin.read(l - x)
			fl += y
			x += len(y)
			a = rx()
			assert a == ""
	a = rx()
	assert a == ""
	return fl

this.add_mtree(mt, nm, int(time.time()), cb_getf)

		
tx("DONE")
a = rx()
