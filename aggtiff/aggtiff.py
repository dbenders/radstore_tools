import requests
import dateutil.parser
import datetime as dt
import simplejson
import subprocess
import os
import uuid
import shutil
import radstore_client

radstore_client.config.base_url = os.environ.get('RADSTORE_API_URL','http://127.0.0.1:3003/api/v1')

def op_tree(op, args):
    if len(args) == 1: return args[0]
    elif len(args) % 2 == 1:
        l,r = args[0],op_tree(op,args[1:])
    else:
        m = len(args)/2
        l,r = op_tree(op,args[:m]),op_tree(op,args[m:])
    return "%s(%s,%s)" % (op,l,r)

def aggregate_multislice(datetime, variable, operation, filters="{}", **kwargs):

    date = dateutil.parser.parse(datetime)

    url_params = {'type':'vol.slice:geotiff',
        'datetime': date.isoformat(),
        'variable': variable}

    #url_params.update(filters)

    prods = radstore_client.Product.query().filter(**url_params).all()
    params = {}

    tmpdir = '/tmp/aggregate_raster/%s' % uuid.uuid1()
    try: os.makedirs(tmpdir)
    except: pass

    AlphaList=["A","B","C","D","E","F","G","H","I","J","K","L","M",
        "N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]

    cmdline = ['/usr/bin/python','/usr/bin/gdal_calc.py']
    params = {}

    transf = radstore_client.Transformation()
    transf.datetime = dt.datetime.now()
    transf.process = 'aggtiff'

    for i,prod in enumerate(prods):
        fname = '%s.tiff' % AlphaList[i]
        with open(os.path.join(tmpdir,fname), 'w') as fo:
            fo.write(prod.content)
        params[AlphaList[i]] = fname
        transf.add_input(prod)

    for k,v in params.items(): cmdline.extend(['-%s' % k, v])

    if operation == 'all':
        ops = ['avg','max','min']
    else:
        ops = [operation]

    cmdline_ori = cmdline
    for op in ops:
        cmdline = [x for x in cmdline_ori]
        cmdline.extend(['--outfile','%s.tiff' % op])
        if op == 'avg':
            cmdline.extend(['--calc','(%s)/%d' % ('+'.join(params.keys()),len(params))])
        elif op == 'max':
            cmdline.extend(['--calc',op_tree('fmax',params.keys())])
        elif op == 'min':
            cmdline.extend(['--calc',op_tree('fmin',params.keys())])

        print ' '.join(cmdline)
        p = subprocess.Popen(cmdline, cwd=tmpdir)
        out = p.communicate()

        outp = radstore_client.Product()
        outp.type = 'vol:geotiff'
        outp.datetime = date
        outp.operation = op
        outp.variable = variable
        outp.default_style = prods[0].default_style
        outp.name = '%s%s_%s.tif' % (dt.datetime.strftime(date,'%Y%m%d%H%M%S'),variable,op)
        #for k,v in filters.items():
        #    setattr(outp,k,v)

        with open(os.path.join(tmpdir,'%s.tiff' % op)) as f:
            outp.content = f.read()
        outp.save()
        transf.add_output(outp)

    transf.save()
    shutil.rmtree(tmpdir)


import sys
def main():
	cmd,args = radstore_client.parse_cmdline(sys.argv)
	if cmd == 'multislice':
		aggregate_multislice(**args)

if __name__ == '__main__':
    main()
