"""Stow2 mtree(8) parsing class

Mtree(8) is a FreeBSD program which can build and check a textual
specification for a filesystem tree.

The format is defined in the mtree(8) manual page.
"""

from __future__ import print_function

class file(object):
	def __init__(self, parent, name):
		self.parent = parent
		self.name = name
		self.a = dict()


class dir(object):
	def __init__(self, parent, path):
		self.parent = parent
		self.parent = parent
		self.path = list(path)
		self.files = dict()
		self.dirs = dict()
		self.a = dict()

class mtree(object):
	def __init__(self, spec):
		self.dirs = dict()
	
		l = list()
		d = None
		set = list()
		spec = spec.replace("\\\n", "").splitlines()
		for i in spec:
			j = i.split()
			if len(j) == 0:
				# Blank line
				continue
			elif j[0][0] == "#":
				# Comment line
				continue
			elif j[0] == "/set":
				# Default line
				set = j[1:]
				continue
			elif j[0] == "..":
				# End of directory
				l.pop()
				d = d.parent
				continue
			elif j[1] == "type=dir":
				l.append(j[0])
				dn = dir(d, l)
				if d != None:
					d.dirs[j[0]] = dn
				else:
					self.root = dn
				self.dirs["/".join(dn.path)] = dn
				d = dn
				t = d
			else:
				e = file(d, j[0])
				d.files[j[0]] = e
				t = e
			for k in set:
				x = k.split("=", 1)
				t.a[x[0]] = x[1]
			for k in j[1:]:
				x = k.split("=", 1)
				t.a[x[0]] = x[1]

	def default_cb(self, typ, obj, path, indent):
		if typ == 'd':
			print(indent , path + "/", "(" + ",".join(obj.a) + ")")
		else:
			print(indent, path, "(" + ",".join(obj.a) + ")")
			
	def tree(self, cb = None, d=None, indent=""):
		if cb == None:
			cb=self.default_cb
		if d == None:
			d = self.root
		for i in d.dirs:
			cb('d', d.dirs[i], "/".join(d.dirs[i].path), indent)
			self.tree(cb, d.dirs[i], indent + "  ")
		pp = "/".join(d.path)
		for i in d.files:
			cb('f', d.files[i], pp + "/" + i, indent + "  ")
		

if __name__ == "__main__":
	f = open("/tmp/___")
	x = f.read()
	m = mtree(x)
	if False:
		print(m)
		print(m.root)
		m.tree()
		exit(0)

	def mycb(typ, obj, path, indent):
		m.default_cb(typ, obj, path, indent)
		for i in obj.a:
			print(indent + "  :: ", i, obj.a[i])

	m.tree(cb = mycb)
	exit (0)
