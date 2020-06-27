import json
class Reader():
    def __init__(self , fname ):
        with open(fname) as f:
            self.values = json.load( f )

    def __getitem__(self, ds):
        vals = self.get_allvals(ds)
        return vals['xsec']

    def get_err(self , ds):
        return self.values[ds]['err']

    def get_allvals(self,ds):
        return self.values[ds]



import os
__dir=os.path.dirname(os.path.abspath(__file__))
TheXSecReader = Reader(__dir+ '/xsections.json')
