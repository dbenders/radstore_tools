# -*-encoding: utf8
import radstore_client
import os
import re
import sys
import datetime

class FileDef(object):
	def __init__(self, fname):
		self.path = fname
		self.type = None
		self.fname = os.path.split(fname)[-1]
		self.ext = self.fname.lower().split('.')[-1]

	def __str__(self):
		s = "%s\t\ttipo: %s" % (self.fname, self.type)
		s += "\tfecha/hora: %s\t" % self.datetime.strftime('%d/%m/%Y %H:%M:%S')
		if hasattr(self, 'variable'): s += "\tvar: %s" % self.variable
		if hasattr(self, 'slice'): s += "\tslice: %d" % self.slice
		return s

def usage():
	print "uso: upload <api_url> [fname1] [fname2] ..."
	print "\tapi_url: url del servidor RadStore. Ejemplo: http://protopalenque.agrodatos.info:3003/api/v1"
	print "\tfname.: path del archivo a subir"
	print ""


def build_def(fname):
	ans = FileDef(fname)
	if ans.ext in ['tiff','tif']:
		typ = 'geotiff.original'
		m = re.match('(?P<ts>.{14})00(?P<var>.+)_(?P<slice>[0-9]+)\.tif',ans.fname)
		if m is None:
			print "No puedo interpretar el archivo %s" % ans.fname
			print "Formato: yyyymmddhhMMssss<var>_<slice>.tif"
			sys.exit(-1)
	elif ans.ext == 'vol':
		typ = 'vol'
		m = re.match('(?P<ts>.{14})00(?P<var>.+)\.vol',ans.fname)
		if m is None:
			print "No puedo interpretar el archivo %s" % ans.fname
			print "Formato: yyyymmddhhMMssss<var>.vol"
			sys.exit(-1)
	elif ans.ext == 'txt':
		typ = 'csv.latlon'
		m = re.match('(?P<ts>.{14})00(?P<var>.+)\.vol_(?P<slice>[0-9]+)\.txt',ans.fname)
		if m is None:
			print "No puedo interpretar el archivo %s" % ans.fname
			print "Formato: yyyymmddhhMMssss<var>.vol_<slice>.txt"
			sys.exit(-1)

	else:
		print "Formato invalido: %s" % ans.fname
		sys.exit(-1)

	p = m.groupdict()
	if 'ts' in p: ans.datetime = datetime.datetime.strptime(p['ts'],'%Y%m%d%H%M%S')
	if 'slice' in p: ans.slice = int(p['slice'])
	if 'var'in p: ans.variable = p['var']
	ans.type = typ
	return ans


def upload_files(*fnames):
	filedefs = []
	for fname in fnames:
		if not os.path.exists(fname):
			print "No existe el archivo %s" % fname
			os.exit(-1)
		filedefs.append(build_def(fname))

	print "\nSe subirán los siguientes archivos:"
	for fdef in filedefs:
		print '%s' % fdef

	print "\nConfirma? [s/N]: "
	if sys.stdin.readline().strip().lower() != 's':
		return

	for fdef in filedefs:
		print fdef.fname
		if radstore_client.Product.query().filter(name=fdef.fname).count() > 0:
			print "\tYA EXISTE"
			continue

		prod = radstore_client.Product()
		prod.name = fdef.fname
		prod.type = fdef.type
		prod.datetime = fdef.datetime
		prod.variable = fdef.variable
		if hasattr(fdef,'slice'): prod.slice = fdef.slice
		# try:
		prod.content = open(fdef.path).read()
		prod.save()
		print "\tOK"
		# except:
		# 	print "\tERROR"

	print "\nListo!\n"

def main():
	if len(sys.argv) < 2:
		usage()
		sys.exit(1)

	radstore_client.config.base_url = sys.argv[1]
	upload_files(*sys.argv[2:])


if __name__ == '__main__':
	main()
