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
        self.selCfg = copy.deepCopy(cfg)
        self.indices=[]

        #these files come from https://twiki.cern.ch/twiki/bin/view/CMS/MuonPOG
        baseSFDir='${CMSSW_BASE}/python/UserCode/VJJSkimmer/postprocessing/etc/'
        muSFSources={
            2016:{
                'id'     : (os.path.join(baseSFDir,'2016_RunBCDEF_SF_ID.root'),  'NUM_TightID_DEN_genTracks_eta_pt'),
                'id_gh'  : (os.path.join(baseSFDir,'2016_RunGH_SF_ID.root'),    'NUM_TightID_DEN_genTracks_eta_pt'),
                'iso'    : (os.path.join(baseSFDir,'2016_RunBCDEF_SF_ISO.root'), 'NUM_TightRelIso_DEN_TightIDandIPCut_eta_pt'),
                'iso_gh' : (os.path.join(baseSFDir,'2016_RunGH_SF_ISO.root'),    'NUM_TightRelIso_DEN_TightIDandIPCut_eta_pt'),

              },
            2017:{
                'id'  : (os.path.join(baseSFDir,'RunBCDEF_SF_ID_syst.root'),  'NUM_TightID_DEN_genTracks_pt_abseta'),
                'iso' : (os.path.join(baseSFDir,'RunBCDEF_SF_ISO_syst.root'), 'NUM_TightRelIso_DEN_TightIDandIPCut_pt_abseta'),
                },
            2018:{
                'id'       : (os.path.join(baseSFDir,'RunABCD_SF_ID.root'),  'NUM_TightID_DEN_TrackerMuons_pt_abseta'),
                'iso'      : (os.path.join(baseSFDir,'RunABCD_SF_ISO.root'), 'NUM_TightRelIso_DEN_TightIDandIPCut_pt_abseta'),
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

        if mu.pt < self.selCfg['min_leptonPt']          : return False
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
                    sfVal=self.evalSF(k, objAttrs=[m.eta, m.pt])

                    sfValGH=self.evalSF(k+'_gh', objAttrs=[m.eta,m.pt])
                    w=16551.4/(16551.4+19323.4)
                    sfVal=(w*sfVal[0]+(1-w)*sfValGH[0],
                           np.sqrt( (w*sfVal[1])**2 + ((1-w)*sfValGH[1])**2 ) )

                else:
                    sfVal=self.evalSF(k, objAttrs=[m.pt,abs(m.eta)])

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
