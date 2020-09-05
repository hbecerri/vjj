import os
from Sample import SampleList
from xml.etree.ElementTree import ElementTree, Element, SubElement, Comment, tostring
import json

import os
__dir=os.path.dirname(os.path.abspath(__file__))

class Manager:

    def __init__(self , lst , update_html=False):
        self.all_samples = {}
        self.all_samples[ '00DoubleEGData' ] = SampleList( "DoubleEGData"  , ['/DoubleEG/.*' , '/EGamma/.*' ] , 'era' , color=1)
        self.all_samples[ '01PhotonData' ] = SampleList( "PhotonData"  , ['/SinglePhoton/.*' , '/EGamma/.*'] , 'era' , color=1)
        self.all_samples[ '02DoubleMuData' ] = SampleList( "DoubleMuData"  , [ '/DoubleMuon/.*' ] , 'era' , color=1)

        self.all_samples[ '07GJetsSherpa' ] = SampleList( "GJetsSherpa"  , [ '/GJets_Pt-(?P<ptrange>[^_]*)_13TeV[_-]sherpa/.*' ] , 'ptrange'  , color=2)
        self.all_samples[ '03SignalMGPythia500' ] = SampleList( 'SignalMGPythia500' , ['/GJets_Mjj-500.*pythia.*' , '/GJets_Mjj-500.*(?P<interference>_INTERFERENCE_).*pythia.*'] , signal=True , color=4 , binning = "interference")
        self.all_samples[ '04SignalMGPythia120' ] = SampleList( 'SignalMGPythia120' , ['/GJets_SM_5f.*EWK.*pythia.*' , '/GJets_SM_5f.*(?P<interference>_INTERFERENCE).*pythia.*'] , signal=True , color=4 , binning = "interference")
        self.all_samples[ '05SignalMGHerwig120' ] = SampleList( 'SignalMGHerwig120' , ['/GJets_SM_5f.*EWK.*herwig.*' , '/GJets_SM_5f.*(?P<interference>_INTERFERENCE_).*herwig.*'] , signal=True , color=4, binning = "interference")
        self.all_samples[ '06SignalNLOPythia' ] = SampleList( 'SignalNLOPythia' , ['/AJJ_EWK.*'] , signal=True, color=4)
        self.all_samples[ '09DiPhotonJetBox' ] = SampleList( 'DiPhotonJetsBox'  , [ '/DiPhotonJetsBox_M(?P<mrange>40_80).*' , '/DiPhotonJetsBox_MGG-(?P<mrange>80toInf).*' ] , 'mrange' , color=3)
        self.all_samples[ '10DYJetsMGHT' ] = SampleList( 'DYJetsLO' , [ '/DYJetsToLL_M-(?P<mrange>[^_]*)_HT-(?P<htrange>[^_]*)_.*madgraphMLM.*']  , 'htrange' , color=4)
        self.all_samples[ '10DYJetsMGJets' ] = SampleList( 'DYJetsLOJetBins' , [ '/DY(?P<njets>[0-9])Jet.*_M-(?P<mrange>[^_]*).*madgraphMLM.*']  , 'njets' , Filter=['HT'] , color=4)
        self.all_samples[ '10DYJetsLOInclusive' ] = SampleList( 'DYJetsLOInclusive' , [ '/DYJet.*_M-(?P<mrange>[^_]*).*madgraphMLM.*']  , Filter=['HT'] , color=4)
        self.all_samples[ '11DYJetsNLO' ] = SampleList( 'DYJetsNLO' , [ '/DYJetsToLL_M-(?P<mrange>[^_]*).*amcatnlo.*']  , 'htrange' , color=4)
        self.all_samples[ '11DYJetsJetBins' ] = SampleList( 'DYJetsJetBins' , ['/DYJetsToLL_(?P<njets>[0-9])J' , '/DYToLL_(?P<njets>[0-9])J.*' ] , 'njets' , color=4)
        self.all_samples[ '14QCDEMEnriched' ] = SampleList( 'QCDEMEnriched' ,  [ '/QCD_Pt-(?P<ptrange>[^_]*)_EMEnriched.*' ] , 'ptrange' , color=14)
        self.all_samples[ '08GJetsLO' ] = SampleList( 'GJetsLO' , ['/GJets_HT-(?P<htrange>[^_]*).*' ] , 'htrange' , color=2)
        self.all_samples[ '12lljjherwig' ] = SampleList( 'LLJJherwig'  , ['.*LLJJ.*herwig.*' , '.*LLJJ.*(?P<interference>_INT_).*herwig.*' , '.*MLL[-_](?P<mll>[^_]*).*herwig.*' , '.*MJJ-(?P<mjj>[^_]*).*herwig.*' , '.*p[Tt]J-(?P<ptj>[^_]*).*herwig.*'] , 'mll' , color=5)
        self.all_samples[ '13lljjpythia' ] = SampleList( 'LLJJPythai'  , ['.*LLJJ.*pythia.*' , '/LLJJ_(?P<interference>_INT_).*pythia.*' , '.*MLL[-_](?P<mll>[^_]*).*pythia.*' , '.*MJJ-(?P<mjj>[^_]*).*pythia.*' , '.*p[Tt]J-(?P<ptj>[^_]*).*pythia.*'] , 'mll' , color=5)
        self.all_samples[ '15ttjetsamcatnlo' ] = SampleList('TTJets' , [ '/TTJets.*' ] , color=46 ) # this picks amcatnlo
        self.all_samples[ '15ttjetspowheg' ] = SampleList('TTTo2L2NuPowheg'  , [ '/TTTo2L2Nu.*' ] , color=46 )
        self.all_samples[ '16ttg' ] = SampleList('TTG'  , [ '/TTGJets.*' ] , color=30)
        self.all_samples[ '17wg' ] = SampleList( 'WG'  , ['/WGToLNuG_.*' ] , color=28)
        self.all_samples[ '18wjlnu' ] = SampleList( 'WJetsToLNu'  , ['/WJetsToLNu_Pt-(?P<Pt>[^_]*).*'] , 'Pt' , color=41)
        self.all_samples[ '19wjqq' ] = SampleList( 'WJetsToQQ' , ['/WJetsToQQ_HT[-]{0,1}(?P<htrange>[^_]*).*' ] , 'htrange' , color=43)
        self.all_samples[ '20zgto2lg' ] = SampleList( 'ZG' , ['.*ZGTo2LG.*' ] , color=38 )

        if type(lst) == str:
            self.inputFileName = lst
            with open(self.inputFileName) as f :
                lst = [a[:-1] for a in f.readlines() if not a.startswith('#')]
            self.inputFileName = os.path.basename( self.inputFileName )
        elif type(lst) == list:
            self.inputFileName = 'list'
            update_html = False
    
        if type(lst) == list:
            for _, s in self.all_samples.items():
                s.from_list( lst )
        
        if update_html:
            self.write_html()

    def get_sampleName(self , ds):
        for _,s in self.all_samples.items():
            if ds in s.datasets:
                return s.name
        return None

    def get_sampleColor(self, sample):
        for _,s in self.all_samples.items():
            if s.name == sample:
                return s.color

    def write_html(self):
        html = Element("html")
        head = SubElement( html , 'head')
        css = SubElement( head , 'link'  )
        css.set( 'rel',"stylesheet" )
        css.set( 'href', "https://www.w3schools.com/w3css/4/w3.css")
        body = SubElement( html , 'body')
        index = SubElement( body , 'div')
        lst = SubElement( index , 'ol' )
        lst.set( 'class',"w3-ol" )

        content = SubElement(body , 'div' )
        root = SubElement( content , 'ul' )
        root.set( 'class',"w3-ul" )
        for s_ in sorted(self.all_samples.keys()):
            s = self.all_samples[s_]
            s.write_html(root)
            
            lnk = SubElement( SubElement( lst , 'li' ) , 'a' )
            lnk.text = s.name
            #SubElement( lnk , 'h1')
            lnk.set('href' , '#{0}'.format( s.name ) )
        tree = ElementTree(html)        
        tree.write( '{0}/src/UserCode/VJJPlotter/web/Samples/{1}.html'.format( os.getenv('CMSSW_BASE' , '.') , self.inputFileName.split('.')[0] ) )

    def __str__(self):
        ret = ''
        for name,sample in self.all_samples.items():
            ret += str(sample) + '\n' 
        return ret
    
    def all_datasets(self,moreinfo = False):
        for name,sample in self.all_samples.items():
            for ds,info in sample.datasets.items():
                if moreinfo:
                    yield ds,info['year'],sample.get_binValue(ds), sample.name
                else:
                    yield ds,info

    def is_signal(self, ds1):
        for ds,info in self.all_datasets():
            if ds == ds1:
                #print('is_signal', info['signal'])
                return info['signal']

        return False

    def write_txt(self, outfname):
        lst = set( [a for a,_ in self.all_datasets() ] )
        with open(outfname , 'w' ) as f:
            for ds in lst:
                f.write(ds)
                f.write('\n')
            f.write('\n')


#a = Manager( 'NanoAODv7_v2.lst' )
#a.write_html()
#a.write_txt( 'NanoAODv7_v2.lst' )
samplesV6 = lambda : Manager(__dir+'/lists/NanoAODv6.lst')
samplesV7 = lambda : Manager(__dir+'/lists/NanoAODv7.lst')
currentSampleList = samplesV7()
