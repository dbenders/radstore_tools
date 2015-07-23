import requests
import simplejson
import datetime
import radstore_client
import os
import tempfile
import subprocess
from completa_blancos import completa_blancos
import shutil
import traceback

radstore_client.config.base_url = os.environ.get('RADSTORE_API_URL','http://127.0.0.1:3003/api/v1')

vrt = """
<OGRVRTDataSource>
<OGRVRTLayer name="%(layer_name)s">
<SrcDataSource>%(csv_fname)s</SrcDataSource>
<GeometryType>wkbPoint</GeometryType>
<LayerSRS>WGS84</LayerSRS>
<GeometryField separator="," encoding="PointFromColumns" x="lon" y="lat" z="%(variable)s"/>
</OGRVRTLayer>
</OGRVRTDataSource>
"""

def process(prods):
	for prod in prods:
		try:
			if radstore_client.Product.query().filter(
					type='vol.slice:geotiff',
					datetime=prod.datetime,
					variable=prod.variable,
					slice=prod.slice).exists():
				print "\texists"
				continue

			fo_tiff = tempfile.NamedTemporaryFile('w', suffix='.tif')
			fo_csv = tempfile.NamedTemporaryFile('w', suffix='.csv')
			dir_shp = tempfile.mkdtemp()
			fo_csv.write(prod.content)
			fo_csv.flush()
			var = prod.content[:prod.content.index('\n')].split(',')[-1]
			layer_name = os.path.split(fo_csv.name)[-1].split('.')[0]
			fo_vrt = tempfile.NamedTemporaryFile('w', suffix='.vrt')
			fo_vrt.write(vrt % dict(csv_fname=fo_csv.name, variable=var, layer_name=layer_name))
			fo_vrt.flush()
			subprocess.call(['ogr2ogr','-f','ESRI Shapefile',dir_shp,fo_vrt.name])
			subprocess.call(['gdal_rasterize','-ts','487','505','-a_nodata','-99','-a',var,'-l',layer_name,'%s/%s.shp' % (dir_shp,layer_name), fo_tiff.name])
			completa_blancos(fo_tiff.name, 2, 'max')

			shutil.rmtree(dir_shp)
			fo_vrt.close()
			fo_csv.close()

			try:
				style_id = radstore_client.Product.query().filter(type='style:qml', name='geotiff.%s' % var).first()._id
			except:
				style = radstore_client.Product(dict(type='style:qml', name='geotiff_%s.qml' % var))
				style.content = open('%s.qml' % var).read()
				style.save()
				style_id = style._id

			outp = radstore_client.Product(prod._metadata)
			outp.type = 'vol.slice:geotiff'
			outp.name = outp.name.replace('.csv','.tif')
			outp.default_style = style_id
			outp.content = open(fo_tiff.name).read()
			outp.save()
		except Exception,e:
			traceback.print_stack()

import sys
def main():
	args = radstore_client.parse_cmdline(sys.argv, cmd=False)
	if 'query' in args:
		q = simplejson.loads(args['query'])
		prods = radstore_client.Product.query().filter(type='vol.slice:latlon:csv', **q).all()
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
