# *-*encoding:utf8
import radstore_client
import os

def usage():
	print "uso: upload <api_url> [fname1] [fname2] ..."
	print "\tapi_url: url del servidor RadStore. Ejemplo: http://protopalenque.agrodatos.info:3003/api/v1"
	print "\tfname.: path del archivo a subir"
	print ""

def build_def(fname):
	ans = {}
	ans['path'] = fname
	ans['fname'] = os.path.split(fname)[-1]
	if fname.endswith('tiff') or fname.endswith('tif'):
		ans['datetime'] = datetime.datetime.strptime(fname[:16],'YYYYmm')


	#2011110900000400dBZ_1.tif


def upload_files(*fnames):
	filedefs = []
	for fname in fnames:
		if not os.path.exists(fname):
			print "No existe el archivo %s" % fname
			os.exit(-1)
		fileders.append(build_def(fname))

	print "Se subirán los siguientes archivos:"

import sys
def main():
	if len(sys.argv) < 2: 
		usage()
		sys.exit(1)

	radstore_client.config.base_url = sys.argv[1]
	upload_files(sys.argv[2:])


if __name__ == '__main__':
	main()