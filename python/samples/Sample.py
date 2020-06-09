import re
from xml.etree.ElementTree import ElementTree, Element, SubElement, Comment, tostring

class SampleNameParser:
    def __init__(self):
        self.regexps = []
        self.regexps.append( re.compile( r'.*_Tune(?P<tune>[^_/]*)[_/].*' ) )
        self.regexps.append( re.compile( r'.*/RunII(?P<campaign>[^-]*(?P<year>[0-9][0-9])).*' ) )
        self.regexps.append( re.compile( r'.*/(?P<isData>Run20)(?P<year>[0-9][0-9])(?P<era>.)[-_].*' ) )
        self.regexps.append( re.compile( r'.*-Nano(?P<nanotag>[^-_]*)[-_].*' ) )
        self.regexps.append( re.compile( r'.*NanoAODv(?P<nanoversion>[0-9]*).*' )  )
        self.regexps.append( re.compile( r'.*_ext(?P<ext>[0-9]*).*' )  )
        self.regexps.append( re.compile( r'.*-v(?P<version>[0-9]*).*' )  )
        self.regexps.append( re.compile( r'.*_ver(?P<version>[0-9]*).*' )  )
        self.regexps.append( re.compile( r'.*(?P<madgraph>madgraph).*' )  )
        self.regexps.append( re.compile( r'.*(?P<herwig>herwig).*' )  )
        self.regexps.append( re.compile( r'.*(?P<amcatnlo>amcatnlo).*' )  )
        self.regexps.append( re.compile( r'.*(?P<pythia>pythia).*' )  )
        self.regexps.append( re.compile( r'.*(?P<sherpa>[sS]herpa).*' )  )
        self.regexps.append( re.compile( r'.*(?P<pmx>new_pmx).*' )  )
        self.regexps.append( re.compile( r'.*(?P<backup>backup).*' )  )
        self.regexps.append( re.compile( r'.*(?P<ps>[^_]*PS[^_/]*).*' )  )
    
    def parse(self, sample):
        ret = [ re.match( sample ) for re in self.regexps ]
        info = {}
        for regexp in [ r for r in ret if r ]:
            for group, value in regexp.groupdict().items():
                info[group] = value
        return ret, info


class Sample:
    def __init__(self , name , xsections , ds_res , binning=None ):
        self.binning = binning
        self.name = name
        self.xsections = xsections
        self.ds_res = [ re.compile( ds_re ) for ds_re in ds_res ]
        self.parser = SampleNameParser()

        self.datasets = {}
        

    def xsection( self , dataset ):
        if type( self.xsections ) in [int, float] :
            return self.xsections

        ds_info = self.datasets.get( dataset , {} )
        if ds_info == {}:
            #print( "dataset {0} is not found in sample {1}".format( dataset , self.name ) )
            return -1
        for i, val in self.xsections.items():
            if ds_info[i[0]] == i[1]:
                return val
        #print( "dataset {0} does not have cross section information {1} , {2}".format( dataset , self.xsections , ds_info ) )
        return -1

    def add_sample(self , sample):
        match = [ ds_re.match( sample ) for ds_re in self.ds_res ]
        if any(match):
            self.datasets[ sample ] = {}
            additional_info, _ = self.parser.parse( sample )
            for m in [ mm for mm in match+additional_info if mm ]:
                for group,value in m.groupdict().items():
                    self.datasets[sample][group] = value

    def from_list(self , file ):
        for l in file:
            self.add_sample( l )

    def available_bins(self , binning=None , dslist = None):
        if not binning:
            binning = self.binning

        if not dslist:
            dslist = self.datasets.keys()

        ret = {}

        for ds in dslist:
            info = self.datasets[ds]
            binname = info.get( binning , 'none' )
            if binname not in ret: ret[binname] = []
            ret.get( binname ).append( ds )
        return ret

    def byYear(self , year ):
        for ds,info in self.datasets.items():
            if int( info['year'] ) == year :
                yield ds

    def write_html(self , root):
        sample = SubElement( root , "li" )
        SubElement(sample , 'h1').text = self.name
        years_el = SubElement( sample , 'ol' )
        years_el.set( 'class' , "w3-display-container")
        byYear = self.available_bins( 'year' )
        for year in [16,17,18]:
            year_el = SubElement( years_el , 'li' )
            datasets = byYear.get( str(year) , None)
            if not datasets:
                SubElement( year_el , 'h2').text = str(year) + ': No Dataset'
                continue
            else:
                SubElement( year_el , 'h2').text = '20' + str(year)

            binned_samples = self.available_bins( dslist=datasets  )
            if len(binned_samples)==1:
                dss_el = SubElement( year_el , 'ol')
                dss_el.set( 'class',"w3-ul w3-hoverable" )
                for _,dss in binned_samples.items():
                    for ds in dss:
                        ds_el = SubElement( dss_el , 'li' )
                        lnk_el = SubElement(ds_el , 'a' )
                        lnk_el.set('href','https://cmsweb.cern.ch/das/request?input=dataset='+ds)
                        lnk_el.text = ds
            else:
                bins_el = SubElement( year_el , 'ol' )
                for bin_val in sorted(binned_samples.keys()):
                    bin_el = SubElement( bins_el , 'li' )
                    bin_el.text = self.binning + ':' + bin_val
                    dss = binned_samples[bin_val]
                    dss_el = SubElement( bin_el , 'ol' )
                    dss_el.set( 'class',"w3-ul w3-hoverable" )
                    for ds in dss:
                        ds_el = SubElement( dss_el , 'li' )
                        lnk_el = SubElement(ds_el , 'a' )
                        lnk_el.text = ds
                        lnk_el.set('href','https://cmsweb.cern.ch/das/request?input=dataset='+ds)

    def __str__(self):
        ret = self.name
        byYear = self.available_bins( 'year' )
        for year in [16,17,18]:
            ret += '\n\t{0}'.format( year )
            datasets = byYear.get( str(year) , None)
            if not datasets:
                ret += ':\t\tNo Dataset'
                continue
            binned_samples = self.available_bins( dslist=datasets  )
            for bin_val in sorted(binned_samples.keys()):
                dss = binned_samples[bin_val]
                differences = {}
                for ds in dss:
                    for p,v in self.datasets[ds].items():
                        if (p,v) in differences:
                            differences[ (p,v) ] += 1
                        else:
                            differences[ (p,v) ] = 1
                for p in [ p for p,count in differences.items() if count == len(dss) ]:
                    del differences[p]

                ret += '\n\t\t{0} : {1}, {2}'.format(bin_val  , len(dss) ,  '\n' + '\n'.join(dss) ) #differences
        return ret
