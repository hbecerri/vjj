import json
import re
import numpy

class Reader():
    def __init__(self , fname , scales ):
        with open(fname) as f:
            self.values = json.load( f )
        with open(scales) as f:
            scales_ = json.load(f)
            self.scales = {}
            for sample_name in scales_:
                self.scales[ re.compile( sample_name ) ] = numpy.prod( [ l for _,l in scales_[ sample_name ].items() ] )

    def __getitem__(self, ds):
        vals = self.get_allvals(ds)
        scale = 1.0
        for scale_re,scale_val in self.scales.items() :
            if scale_re.match( ds ):
                scale *= scale_val
        #if scale != 1.0:
        #    print( ds , vals['xsec'] , scale )
        return vals['xsec']*scale

    def get_err(self , ds):
        return self.values[ds]['err']

    def get_allvals(self,ds):
        return self.values[ds]



import os
__dir=os.path.dirname(os.path.abspath(__file__))
TheXSecReader = Reader(__dir+ '/xsections.json' , __dir+'/scales.json')
