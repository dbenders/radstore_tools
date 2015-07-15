import requests
import simplejson
import datetime
import radstore_client
import os
import tempfile
import subprocess
import shutil

radstore_client.config.base_url = os.environ.get('RADSTORE_API_URL','http://127.0.0.1:3003/api/v1')

def process(prods):
	for prod in prods:
		print prod._id
		try:
			outp = radstore_client.Product.query().filter(
				type='vol.slice:jpg',
				datetime=prod.datetime,
				variable=prod.variable,
				slice=prod.slice).first()
			print "\texists"
			
		except:
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

		for prod2 in radstore_client.Product.query().filter(
			datetime=prod.datetime,
			variable=prod.variable,
			slice=prod.slice).all():
				prod2.thumbnail = outp._id
				prod2.save()

import sys
def main():
	args = radstore_client.parse_cmdline(sys.argv, cmd=False)
	if 'query' in args:
		q = simplejson.loads(args['query'])
		prods = radstore_client.Product.query().filter(type='vol.slice:geotiff', **q).all()
		process(prods)
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
