import subprocess
import re
from xml.etree.ElementTree import ElementTree, Element, SubElement, Comment, tostring

class SampleNameParser:
    def __init__(self):
        self.regexps = []
        self.regexps.append( re.compile( r'.*_Tune(?P<tune>[^_/]*)[_/].*' ) )
        self.regexps.append( re.compile( r'.*/RunII(?P<campaign>[^-]*(?P<year>[0-9][0-9])).*' ) )
        self.regexps.append( re.compile( r'.*/(?P<isData>Run20)(?P<year>[0-9][0-9])(?P<era>.)[-_].*' ) )
        self.regexps.append( re.compile( r'.*-Nano(?P<nanotag>[^-_]*)[-_].*' ) )
        self.regexps.append( re.compile( r'.*NanoAODv(?P<nanoversion>[0-9]*).*' ))
        self.regexps.append( re.compile( r'.*NanoAODAPVv(?P<nanoversion>[0-9]*).*' ))
        self.regexps.append( re.compile( r'.*(?P<prevfp>NanoAODAPV).*' )  )
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

    def parse(self , sample):
        ret = [ re.match( sample ) for re in self.regexps ]
        info = {}
        for regexp in [ r for r in ret if r ]:
            for group, value in regexp.groupdict().items():
                info[group] = value
        
        return ret , info
    
class Sample:
    def __init__(self , ds , parser = None):
        self.ds = ds
        self.parser = parser if parser else SampleNameParser()
        self.regexp_results , self.info = self.parser.parse( ds ) 

    def isData(self):
        return self.info.get('isData' , False) != False

    def year(self):
        return 2000 + int( self.info['year'] )
    
    def tune(self):
        return self.info.get('tune' , 'noTune' )

    def preVFP(self):
        return 'prevfp' in self.info 

    def makeUniqueName(self):
        uName = self.ds.split('/')[1]
        if self.isData():
            uName = "{0}_{1}_{2}".format( uName , self.year() , self.info.get('era') )
        else:
            if 'G1Jet' in uName and self.year() == 2016: return uName #FIXME #G1Jet big ntuples produced by Davide do not follow the same naming convention
            uName = "{0}_{1}".format( uName , self.year() )
            if 'pmx' in self.info :
                uName += "_pmx"
            if 'ext' in self.info :
                uName += '_ext{0}'.format( self.info['ext'] )
            if 'backup' in self.info :
                uName += '_backup'
            if 'ps' in self.info:
                uName += '_' + self.info['ps']
        if 'version' in self.info:
            uName += '_v' + self.info['version']

        return uName

    def GetParent(self):
        if not hasattr( self , 'parents' ):
            process = subprocess.Popen( [ '/cvmfs/cms.cern.ch/common/dasgoclient', "-query=parent dataset={0}".format(self.ds) ], stdout=subprocess.PIPE)
            self.parents = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    s = output.strip()
                    self.parents.append( s )
        if len(self.parents) == 1:
            return Sample( self.parents[0] )
        else:
            print( 'here is the list of found parents for {0} : {1}'.format( self.ds , self.parents ) )
            return None
                   

class SampleList:
    def __init__(self , name  , ds_res , binning=None  , Filter = [] , signal = False , color=None , regions=['gamma' , 'ee' , 'mm']):
        self.binning = binning
        self.name = name
        self.ds_res = [ re.compile( ds_re ) for ds_re in ds_res ]
        self.parser = SampleNameParser()
        self.filter = Filter
        self.datasets = {}
        self.signal = signal
        self.color = color
        if not self.color:
            import random
            self.color = random.randrange(50)
            print( 'color for sample {0} chosen randomely: {1}'.format( name , self.color ) )
        self.Regions = regions

    def add_sample(self , sample):
        if any( [ a in sample for a in self.filter ] ):
            return
        match = [ ds_re.match( sample ) for ds_re in self.ds_res ]
        additional_info = []
        if any(match):
            self.datasets[ sample ] = {'signal':self.signal}
            additional_info, _ = self.parser.parse( sample )
            for m in [ mm for mm in match+additional_info if mm ]:
                for group,value in m.groupdict().items():
                    self.datasets[sample][group] = value

            if self.binning:
                if self.binning in self.datasets[sample].keys():
                    pass
                else:
                    self.datasets[sample][self.binning] = 'None'

    def sub_samples(self):
        for ds in self.datasets:
            yield Sample(ds , self.parser)

    def get_binValue(self, ds):
        if self.binning:
            if self.binning in self.datasets[ds]:
                return '{0} : {1}'.format( self.binning , self.datasets[ds][self.binning] )
            else:
                return '{0} : {1}'.format( self.binning , 'None' )
        else:
            return None

    def from_list(self , file ):
        for l in file:
            self.add_sample( l )


    def find_dsgroup( self , dataset , binning = None ):
        if not dataset in self.datasets:
            print( '{0} is not in {1}'.format( dataset , self.name )) 
            return []
        info = self.datasets[dataset]
        if not binning:
            binning = self.binning
        binname = info.get( binning , 'none' )
        year = info.get( 'year' )
        return self.filter_datasets( year , binname , binning)

    def filter_datasets(self, year , binvalue , binning  = None):
        ds_byYear = self.byYear( year )
        all_bins = self.available_bins( binning , ds_byYear )
        return all_bins[binvalue] 

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
        lnk = SubElement(sample , 'a' )
        SubElement(lnk , 'h1').text = self.name
        lnk.set('name' , self.name )
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
                    bin_el.text = self.binning + ':' + str(bin_val)
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
