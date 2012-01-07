"""Stow2 Archive class

"""

from __future__ import print_function

import os
import hashlib
import zlib

import silo
import mtree

def md5(s):
	x = hashlib.md5()
	x.update(s)
	return x.hexdigest()

class archive(object):
	"""The stow class"""

	def __init__(self, dir = "silos", debug_fd = None):
		assert type(dir) == str
		self.dir = dir
		self.debug_fd = debug_fd

		# Parameters
		# Files above this size will be split
		self.huge_size		= 1024 * 1024
		self.zlib_level		= 1
		self.max_silo		= 3 * 1024 * 1024 * 1024
		self.dbg_silo		= None

		self.dbg("New Archive")

		silos = silo.find_silos(self.dir)
		self.dbg("Silos: " + str(silos))

		if len(silos) == 0:
			silo.silo(dir, 0, self.dbg_silo, self.max_silo)
			silos.append(0)

		self.silo = dict()

		self.idx = dict()
		for s in silos:
			ss = silo.silo(self.dir, s,
			    self.dbg_silo, self.max_silo)
			self.silo[s] = ss
			self.idx.update(ss.get_idx())
			self.cur_write = ss

	def dbg(self, str):
		if self.debug_fd != None:
			self.debug_fd.write(self.dir + ": " + str)
			if str[-1] != "\n":
				self.debug_fd.write("\n")
			self.debug_fd.flush()

	###############################################################
	# General storage entries
	#

	def has_entry(self, idx):
		return idx in self.idx

	def add_entry(self, idx, method, body):
		assert idx not in self.idx
		self.dbg("  add(%s, %s, <%s>)" % (idx, method, len(body)))
		while True:
			i = self.cur_write.add(idx, method, body)
			if i != None:
				self.idx[idx] = i
				return
			i = self.cur_write.nbr + 1
			ns = silo.silo(self.dir, i, self.dbg_silo,
			    self.max_silo)
			self.silo[i] = ns
			self.cur_write = ns

	def get_entry(self, idx):
		if idx not in self.idx:
			return None
		i = self.idx[idx]
		b = i[0](i[1])
		return b

	###############################################################
	# Byte storage
	#

	def add_bytes(self, data, try_compress = True):
		idx = md5(data)
		if idx in self.idx:
			return idx

		l = len(data)

		self.dbg("  Add_bytes(<%d>, %s)" % (l, try_compress))

		if l < 8:
			pass
		elif data[0] == '\x1f' and data[1] == '\x8b':
			# GZIP file
			self.dbg(idx + " GZIP")
			try_compress = False
		elif data[0] == '\x1f' and data[1] == '\x9d':
			# COMPRESS file
			self.dbg(idx + " COMPRESS")
			try_compress = False
		elif data[0] == '\xff' and data[1] == '\xd8':
			# JPEG file
			self.dbg(idx + " JPEG")
			try_compress = False
		elif data[0] == '\x89' and data[1:4] == 'PNG':
			# PNG file
			self.dbg(idx + " PNG")
			try_compress = False

		if l <= self.huge_size:
			if try_compress:
				z = zlib.compress(data, self.zlib_level)
				if len(z) < .8 * l:
					self.add_entry(idx, "zlib", z)
					return idx
			self.add_entry(idx, "chunk", data)
			return idx

		lx = list()
		j = 0
		h = hashlib.md5()
		while j < l:
			w = l - j
			if w > self.huge_size:
				w = self.huge_size
			t = data[j:j+w]
			h.update(t)
			lx.append(self.add_bytes(t, try_compress))
			j += w

		self.add_entry(idx, "cat", "\n".join(lx))
		return idx

	def get_bytes(self, idx):
		x = self.get_entry(idx)
		if x == None:
			return x

		if x[1] == "chunk":
			return x[2]

		if x[1] == "cat":
			l = list()
			for i in x[2].splitlines():
				y = self.get_bytes(i)
				if y == None:
					return None
				l.append(y)
			return "".join(l)
	
		if x[1] == "zlib":
			return zlib.decompress(x[2])

		print(x[0], x[1], "???")
		assert x[1] == ""

	###############################################################
	# Add a mtree index

	def add_mtree(self, mtree_spec, name, timestamp, get_func):
		self.dbg("Stow(<%d>,%s)" % (len(mtree_spec), str(get_func)))

		assert type(mtree_spec) == str
		assert type(name) == str
		assert type(timestamp) == int

		mt = mtree.mtree(mtree_spec)

		mtmd5 = self.add_bytes(mtree_spec)
		self.dbg("  mtree_md5 " + mtmd5)

		self.ss = name + "\n"
		self.ss += "%d\n" % timestamp
		self.ss += mtmd5 + "\n"

		def cb(typ, obj, path, indent):
			if typ != 'f':
				return
			if 'md5digest' not in obj.a:
				return
			m = obj.a['md5digest']
			if self.has_entry(m):
				return
			body = get_func(path, obj.a['md5digest'])
			if body == None:
				self.dbg("  - " + path)
				return
			x = self.add_bytes(body)
			if x != m:
				self.ss += m + " -> " + x + "\n"
				self.dbg("  m " + path + " <%d> " % len(body) + "%s -> %s" % (m, x))
				return
			self.dbg("  + " + path + " <%d> " % len(body) + " " + x)

		mt.tree(cb)

		self.add_entry("INDEX_%d" % timestamp, "mtree", self.ss)
		return mtmd5


if __name__ == "__main__":

	import sys

	s = archive("/tmp/A", sys.stdout)
	i = s.get_entry('32abda09e3283853523758c32d421c80')
	print(type(i), len(i))
	print(str(i)[:100])
	try:
		i = s.add_bytes("01234")
		print(i)
	except:
		pass

	j = s.get_bytes('4100c4d44da9177247e44a5fc1546778')
	print(j)
