import re

class Sample:
    def __init__(self , name , xsection , ds_res ):
        self.name = name
        self.xsection = xsection
        self.ds_res = [ re.compile( ds_re ) for ds_re in ds_res ]
        self.ds_res.append( re.compile( r'.*_Tune(?P<tune>[^_/]*)[_/].*' ) )
        self.ds_res.append( re.compile( r'.*/RunII(?P<campaign>[^-]*(?P<year>[0-9][0-9])).*' ) )
        self.ds_res.append( re.compile( r'.*/Run20(?P<year>[0-9][0-9])(?P<era>.)-.*' ) )
        self.ds_res.append( re.compile( r'.*-Nano(?P<nanotag>[^-]*)-.*' ) )
        self.ds_res.append( re.compile( r'.*NanoAODv(?P<nanoversion>[0-9]*).*' )  )
        self.ds_res.append( re.compile( r'.*_ext(?P<ext>[0-9]*).*' )  )
        self.ds_res.append( re.compile( r'.*-v(?P<version>[0-9]*).*' )  )
        self.datasets = {}
        

    def add_sample(self , sample):
        match = [ ds_re.match( sample ) for ds_re in self.ds_res ]
        if any(match):
            self.datasets[ sample ] = {}
            for m in [ mm for mm in match if mm ]:
                for group,value in m.groupdict().items():
                    self.datasets[sample][group] = value

    def from_file(self , fname ):
        with open(fname) as f:
            for l in f:
                self.add_sample( l )

