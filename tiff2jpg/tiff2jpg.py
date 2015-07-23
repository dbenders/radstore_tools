import requests
import simplejson
import datetime
import radstore_client
import os
import tempfile
import subprocess
import shutil

radstore_client.config.base_url = os.environ.get('RADSTORE_API_URL','http://127.0.0.1:3003/api/v1')

def process(prods, typ, forced=False):
	for prod in prods:
		print prod._id
		exists = False
		if not forced:
			try:
				q = dict(
					type='%s:jpg' % typ,
					datetime=prod.datetime,
					variable=prod.variable
				)
				if 'slice' in typ: q['slice'] = prod.slice
				outp = radstore_client.Product.query().filter(**q).first()
				print "\texists"
				exists = True
			except: pass

		if not exists:
			print prod._metadata
			fo_tiff = tempfile.NamedTemporaryFile('w', suffix='.tif')
			fo_tiff.write(prod.content)
			fo_tiff.flush()

			fname_colorized = '%s_colorized.tiff' % fo_tiff.name
			subprocess.call(['gdaldem','color-relief',fo_tiff.name,'%s.colors' % prod.variable,fname_colorized])
			subprocess.call(['gdal_translate','-of','JPEG',fname_colorized,'%s.jpg' % fname_colorized])

			outp = radstore_client.Product(prod._metadata)
			outp.type = 'vol.slice:jpg'
			outp.name = outp.name.replace('.tif','.jpg')
			outp.content = open('%s.jpg' % fname_colorized).read()
			outp.save()

			fo_tiff.close()
			os.unlink(fname_colorized)

		prod.thumbnail = outp._id
		prod.save()
		# q = dict(datetime=prod.datetime,variable=prod.variable)
		# if 'slice' in typ: q['slice'] = prod.slice
		# for prod2 in radstore_client.Product.query().filter(**q).all():
		# 	prod2.thumbnail = outp._id
		# 	prod2.save()

import sys
def main():
	args = radstore_client.parse_cmdline(sys.argv, cmd=False)
	if 'query' in args:
		q = simplejson.loads(args['query'])
		typ = q.get('type','vol.slice:geotiff').split(':')[0]
		prods = radstore_client.Product.query().filter(**q).all()
		process(prods, typ, forced='forced' in args)
		print "done."
	# if cmd == "exists":
	# 	sys.exit(1 if exists(sys.argv[2]) else 0)
	#
	# elif cmd == "upload":
	# 	print "uploading..."
	# 	upload(sys.argv[2],sys.argv[3])
	# 	print "done."

if __name__ == '__main__':
	main()
