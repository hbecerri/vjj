from ScaleFactorBase import *
from ObjectSelectorBase import *
from VJJEvent import _defaultObjCfg
import copy

class ElectronSelector(ScaleFactorBase, ObjectSelectorBase):

    """ Applies standard electron selections, returning a list of indices of good photons """

    def __init__(self , era, cfg=_defaultObjCfg , vetoObjs = [("Muon", "mu")]):
        super(ScaleFactorBase, self).__init__()
        super(ObjectSelectorBase, self).__init__()
        self.init() #init scale factor object
        self.setParams(2 , vetoObjs , dofilter=False) #set parameters for object selection

        self.era = era
        self.selCfg = copy.deepCopy(cfg)
        self.indices=[]

        #these files come from https://twiki.cern.ch/twiki/bin/view/CMS/EgammaRunIIRecommendations
        baseSFDir='${CMSSW_BASE}/python/UserCode/VJJSkimmer/postprocessing/etc/'
        eleSFSources={
            2016:{
                'rec'    : (os.path.join(baseSFDir,'EGM2D_BtoH_GT20GeV_RecoSF_Legacy2016.root'),    'EGamma_SF2D'),
                'id'     : (os.path.join(baseSFDir,'2016LegacyReReco_ElectronMVA80_Fall17V2.root'), 'EGamma_SF2D'),
              },
            2017:{
                'rec'    : (os.path.join(baseSFDir,'egammaEffi.txt_EGM2D_runBCDEF_passingRECO.root'), 'EGamma_SF2D'),
                'id'     : (os.path.join(baseSFDir,'2017_ElectronMVA80.root'),                        'EGamma_SF2D'),
                },
            2018:{
                'rec'    : (os.path.join(baseSFDir,'egammaEffi.txt_EGM2D_updatedAll.root'), 'EGamma_SF2D'),
                'id'     : (os.path.join(baseSFDir,'2018_ElectronMVA80.root'),              'EGamma_SF2D'),
                }
        }
        for k in eleSFSources[self.era]:
            url,obj=eleSFSources[self.era][k]
            self.addSFFromSource(k,url,obj)

    def collection_name(self):
        return "Electron"

    def obj_name(self):
        return "ele"

    def isGood(self, ele):

        """checks if electron passes standard selection"""

        if ele.pt < self.selCfg['min_leptonPt']  : return False
        absEta=abs( ele.eta )
        if absEta > self.selCfg['max_leptonEta'] : return False
        if absEta> self.selCfg['max_EB'] and absEta< self.selCfg['min_EE'] : return False #EB->EE transition
        min_dr = self.mindr_toVetoObjs(ele)
        if min_dr < self.selCfg['min_drVeto']    : return False

        #id requirement
        hasId=ele.mvaFall17V2Iso_WP80
        if not hasId : return False

        return True

    def fillSFs(self,electrons,combined=True):

        """evaluates the scale factors for a collection of electrons """

        SFs={'rec':[],'id':[]}
        for ele in electrons:
            SFs['rec'].append(
                self.evalSF('rec', objAttrs=[ele.eta,ele.pt])
            )
            SFs['id'].append(
                self.evalSF('id', objAttrs=[ele.eta,ele.pt])
            )

        #combine scale factors
        if combined:
            selSFs = []
            for k in SFs:
                selSFs.extend( [x for x in SFs[k] if x] )
            SFs = self.combineScaleFactors(selSFs)
            ret = dict( zip( self.weight_names() , [SFs[0] , SFs[0]+SFs[1] , SFs[0] -SFs[1] ] ) )
            return ret


        return SFs

electronSelector2016 = lambda : ElectronSelector(2016)
electronSelector2017 = lambda : ElectronSelector(2017)
electronSelector2018 = lambda : ElectronSelector(2018)
