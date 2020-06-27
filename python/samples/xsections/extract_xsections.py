import glob
import re
import json

all_xsections = {}
for fname in glob.iglob("output/*.out"):
    f = open(fname)
    ds_name = None
    xsec = None
    err = None
    unit = None
    nevents = None
    negweightfraction = None
    for l in f:
        if not ds_name:
            if 'Name read from file - ' in l:
                ds_name = '/'.join( l.split( '/' )[1:] )
                ds_name = '/' + ds_name[:-1]
                
        if 'After filter: final cross section =' in l:
            xsecs = l.split('=')[-1].strip().split(' ')
            xsec = float(xsecs[0].strip())
            err = float(xsecs[2].strip())
            unit = xsecs[3].strip()
        if 'Total' in l:
            rr = re.compile('Total\t.*')
            if rr.match( l ):
                ll = re.split(r'\t+', l.strip())
                nevents = ll[2]

        if 'After filter: final fraction of events with negative weights =' in l:
            negweightfraction = l.strip().split('=')[-1].strip()
    all_xsections[ds_name] = {'xsec':xsec , 'err':err , 'unit':unit , 'nevents':nevents , 'negweightfraction':negweightfraction}


fout = open('xsections.json' , 'w' )
json.dump( all_xsections , fout )
fout.close()
