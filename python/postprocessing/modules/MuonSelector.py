from ScaleFactorBase import *
from ObjectSelectorBase import *
from VJJEvent import _defaultObjCfg
import copy

class MuonSelector(ScaleFactorBase , ObjectSelectorBase):

    def __init__(self , era, cfg=_defaultObjCfg):
        super(ScaleFactorBase, self).__init__()
        super(ObjectSelectorBase, self).__init__()
        self.init() #init scale factor object
        self.setParams(2, dofilter=False) #set parameters for object selection

        self.era = era
        self.selCfg = copy.deepcopy(cfg)
        self.indices=[]

        #these files come from https://twiki.cern.ch/twiki/bin/view/CMS/MuonPOG
        #files come from https://twiki.cern.ch/twiki/bin/view/CMS/MuonUL2016 or  MuonUL2017  for UL
        baseSFDir='${CMSSW_BASE}/python/UserCode/VJJSkimmer/postprocessing/etc/'
        muSFSources={
            2016:{
                'id'     : (os.path.join(baseSFDir,'Efficiencies_muon_generalTracks_Z_Run2016_UL_HIPM_ID.root'),    'NUM_TightID_DEN_TrackerMuons_abseta_pt'),
                'id_gh'  : (os.path.join(baseSFDir,'Efficiencies_muon_generalTracks_Z_Run2016_UL_ID.root'),    'NUM_TightID_DEN_TrackerMuons_abseta_pt'),
                'iso'    : (os.path.join(baseSFDir,'Efficiencies_muon_generalTracks_Z_Run2016_UL_HIPM_ISO.root'),    'NUM_TightRelIso_DEN_TightIDandIPCut_abseta_pt'),
                'iso_gh' : (os.path.join(baseSFDir,'Efficiencies_muon_generalTracks_Z_Run2016_UL_ISO.root'),    'NUM_TightRelIso_DEN_TightIDandIPCut_abseta_pt'),

              },
            2017:{
	        'id'  : (os.path.join(baseSFDir,'Efficiencies_muon_generalTracks_Z_Run2017_UL_ID.root'),  'NUM_TightID_DEN_TrackerMuons_abseta_pt'),
                'iso' : (os.path.join(baseSFDir,'Efficiencies_muon_generalTracks_Z_Run2017_UL_ISO.root'),  'NUM_TightRelIso_DEN_TightIDandIPCut_abseta_pt'),
                },
            2018:{
                'id'  : (os.path.join(baseSFDir,'Efficiencies_muon_generalTracks_Z_Run2018_UL_ID.root'),  'NUM_TightID_DEN_TrackerMuons_abseta_pt'),
                'iso' : (os.path.join(baseSFDir,'Efficiencies_muon_generalTracks_Z_Run2018_UL_ISO.root'),  'NUM_TightRelIso_DEN_TightIDandIPCut_abseta_pt'),
                }
        }
        for k in muSFSources[self.era]:
            url,obj=muSFSources[self.era][k]
            self.addSFFromSource(k,url,obj)


        pass

    def collection_name(self):
        return "Muon"

    def obj_name(self):
        return "mu"

    def isGood(self, mu):
        if mu.corrected_pt < self.selCfg['min_leptonPt']          : return False
        if abs( mu.eta ) > self.selCfg['max_leptonEta'] : return False
        min_dr = self.mindr_toVetoObjs( mu )
        if min_dr < self.selCfg['min_drVeto']           : return False

        hasId=mu.tightId
        if not hasId : return False

        isIso=(mu.pfRelIso04_all<0.15)
        if not isIso : return False

        return True

    def fillSFs(self,muons,combined=True):

        """evaluates the scale factors for a collection of muons """

        SFs={'id':[],'iso':[]}
        for m in muons:

            for k in SFs:
                #average by luminosity in 2016
                if self.era==2016:
                    sfVal=self.evalSF(k, objAttrs=[m.eta, m.corrected_pt])

                    sfValGH=self.evalSF(k+'_gh', objAttrs=[m.eta,m.corrected_pt])
                    w=16551.4/(16551.4+19323.4)
                    sfVal=(w*sfVal[0]+(1-w)*sfValGH[0],
                           np.sqrt( (w*sfVal[1])**2 + ((1-w)*sfValGH[1])**2 ) )

                else:
                    sfVal=self.evalSF(k, objAttrs=[m.corrected_pt,abs(m.eta)])

                SFs[k].append( sfVal )

        #combine scale factors
        if combined:
            selSFs = []
            for k in SFs:
                selSFs.extend([x for x in SFs[k] if x])
            SFs = self.combineScaleFactors(selSFs)
            ret = dict( zip( self.weight_names() , [SFs[0] , SFs[0]+SFs[1] , SFs[0] -SFs[1] ] ) )
            return ret


        return SFs

muonSelector2016 = lambda : MuonSelector(2016)
muonSelector2017 = lambda : MuonSelector(2017)
muonSelector2018 = lambda : MuonSelector(2018)
