"""Stow2 Silo management class

Stow2 silos are indexed append only files with a simple and fully
recoverable format.

Each entry consists of an index, a method and a body.

The index will typically be the MD5 hash which this entry can
produce, the method how it produces it ("plain", "zlib", "cat" etc)
and the body the necessary data to produce this MD5 hash.

Duplicate indicies are not allowed, but will not be detected at .add() time

Silos are identified by directory and number.

The index for the silo is cached in a separate file, but can be rebuilt
by skipping through the file.

The silo2 class does not keep a copy of its index, but instead relies
on the class-user to keep a joint index for all silos.
"""

from __future__ import print_function

import os
import sys
import glob
from errno import ENOENT

def find_silos(dir):
	s = os.path.join(dir, "STOW????.???")
	l = glob.glob(s)
	x = dict()
	for i in l:
		x[int(i[-8:-4], 10)] = True
	l = x.keys()
	l.sort()
	return l

class silo(object):
	"""The silo class"""

	def __init__(self, dir, nbr,
	   debug_fd = None,
	   maxsize = 3 * 1024 * 1024 * 1024,
	):
		assert type(dir) == str
		assert type(nbr) == int
		assert type(maxsize) == int

		self.nbr = nbr
		self.maxsize = maxsize
		self.debug_fd = debug_fd
		self.fdw = None
		self.fdi = None
		self.fdr = None

		self.pfx = "STOW%04d" % nbr
		if dir != None:
			self.pfx = os.path.join(dir, self.pfx)

		self.dbg("New Silo")

		try:
			self.fdr = open(self.pfx + ".SLO", "rb")
		except IOError as e:
			if e.errno != ENOENT:
				raise
			self.fdr = None
		if self.fdr == None:
			self.dbg("Creating Silo")
			self.fdw = open(self.pfx + ".SLO", "wb")
			self.fdw.write("STOW_20\nIDX\n")
			self.fdw.close()
			self.fdw = None
			self.fdr = open(self.pfx + ".SLO", "rb")

	def __del__(self):
		self.dbg("Del Silo")
		if self.fdw != None:
			self.fdw.close()
		if self.fdi != None:
			self.fdi.close()
		if self.fdr != None:
			self.fdr.close()

	def dbg(self, str):
		if self.debug_fd != None:
			self.debug_fd.write(self.pfx + ": " + str)
			if str[-1] != "\n":
				self.debug_fd.write("\n")
			self.debug_fd.flush()

	def chk_token(self, tok):
		assert type(tok) == str
		assert tok == tok.strip()
		assert -1 == tok.find("\n")

	def add(self, idx, method, arg):
		self.chk_token(idx)
		self.chk_token(method)
		l = len(arg)
		if self.fdw == None:
			self.dbg("Open for write")
			self.fdw = open(self.pfx + ".SLO", "ab")
			self.fdi = open(self.pfx + ".IDX", "ab")
		pos = self.fdw.tell() - 4
		self.fdr.seek(pos, os.SEEK_SET)
		a = self.fdr.read(4)
		assert a == "IDX\n"
		if pos + l > self.maxsize:
			return None
		self.fdw.write(idx + "\n")
		self.fdw.write(method + "\n%d\n" % l)
		self.fdw.write(arg)
		self.fdw.write("\nIDX\n")
		self.fdw.flush();
		self.fdi.write(idx + " %d\n" % pos)
		self.fdi.flush();
		return (self.get, pos)

	def get(self, off):
		self.dbg("Get %d" % off)
		self.fdr.seek(off, os.SEEK_SET)
		b = self.fdr.read(4)
		assert b == "IDX\n"
		idx = self.fdr.readline().strip("\n")
		assert len(idx) > 0
		self.chk_token(idx)
		method = self.fdr.readline().strip("\n")
		self.chk_token(method)
		l = int(self.fdr.readline())
		body = self.fdr.read(l)
		c = self.fdr.read(5)
		assert c == "\nIDX\n"
		return (idx, method, body)

	def get_idx(self):
		self.dbg("Get_idx")
		try:
			fdi = open(self.pfx + ".IDX")
		except:
			fdi = None
			idx = None
		if fdi != None:
			try:
				idx = dict()
				lo = None
				for i in fdi.readlines():
					i = i.split()
					assert len(i) == 2
					o = int(i[1])
					if lo == None:
						assert o == 8
					else:
						assert o > lo
					lo = o
					assert i[0] not in idx
					idx[i[0]] = (self.get, o)
			except:
				idx = None
			fdi.close()
		if idx != None:
			# XXX: Do cheap first/last test ?
			return idx

		return self.build_idx()

	def verify_idx(self, idx):
		self.dbg("Verify_idx")
		l = list()
		for i in idx:
			assert idx[i][0] == self.get
			l.append((idx[i][1], i))
		l.sort()
		no = 8
		for i,j in l:
			assert i == no
			self.fdr.seek(i - 1, os.SEEK_SET)
			b = self.fdr.read(5)
			assert b == "\nIDX\n"
			idx = self.fdr.readline().strip("\n")
			assert len(idx) > 0
			self.chk_token(idx)
			method = self.fdr.readline().strip("\n")
			self.chk_token(method)
			l = int(self.fdr.readline())
			no = self.fdr.tell() + l + 1
		self.fdr.seek(no - 1, os.SEEK_SET)
		b = self.fdr.read(5)
		assert b == "\nIDX\n"
		pos = self.fdr.tell()
		self.fdr.seek(0, os.SEEK_END)
		pos1 = self.fdr.tell()
		assert pos == self.fdr.tell()
		self.dbg("Verify_idx: OK")

	def build_idx(self):
		self.dbg("Build_idx")
		nidx = dict()
		self.fdr.seek(0, os.SEEK_SET)
		a = self.fdr.read(7)
		assert a == "STOW_20"
		fdi = open(self.pfx + ".ID_", "w")
		while True:
			b = self.fdr.read(5)
			assert b == "\nIDX\n"
			pos = self.fdr.tell() - 4
			idx = self.fdr.readline().strip("\n")
			if len(idx) == 0:
				break
			self.chk_token(idx)
			method = self.fdr.readline().strip("\n")
			self.chk_token(method)
			l = int(self.fdr.readline())
			assert idx not in nidx
			nidx[idx] = (self.get, pos)
			fdi.write(idx + " %d\n" % pos)
			self.fdr.seek(l, os.SEEK_CUR)
		fdi.close()
		os.rename(self.pfx + ".ID_", self.pfx + ".IDX")
		return nidx

if __name__ == "__main__":

	import time

	s = silo("/tmp", 8, sys.stdout)
	i = s.get_idx()
	s.verify_idx(i)
	for j in i:
		print(j, i[j][0](i[j][1]))
	#s.add("BAR", "bar", "barfoo")
	#s.add("FOO", "foo", "foobar")
	j = s.add("%d" % time.time(), "test", "foobar")
	print(j)
	del s

	print("SILOS: ", find_silos("/tmp/"))

	try:
		s = silo("/tmp", 9, sys.stdout)
	except IOError as e:
		print(e)
