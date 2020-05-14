from ScaleFactorBase import *

class ElectronSelector(ScaleFactorBase):

    """ Applies standard electron selections, returning a list of indices of good photons """

    def __init__(self , era, min_pt=20., max_eta=2.4, dr2vetoObjs=0.4):
        self.era = era
        self.min_pt = min_pt
        self.max_eta = max_eta
        self.min_dr2vetoObjs = dr2vetoObjs
        self.indices=[]
        
        #scale factors for electron objects
        ScaleFactorBase.__init__(self)

        #these files come from https://twiki.cern.ch/twiki/bin/view/CMS/EgammaRunIIRecommendations
        baseSFDir='${CMSSW_BASE}/src/UserCode/VJJSkimmer/python/postprocessing/etc/'
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

    def __call__(self, electrons, vetoObjs, returnIndices=True):
        self.indices=[i for i,ele in enumerate(electrons) if self.isGood(ele,vetoObjs)]

        if not returnIndices:
            return [electrons[i] for i in self.indices]

        return self.indices

    def isGood(self, ele, vetoObjs):

        """checks if electron passes standard selection"""
        
        if ele.pt < self.min_pt : return False
        absEta=abs( ele.eta )
        if absEta > self.max_eta : return False
        if absEta> 1.4442 and absEta<1.5660 : return False #EB->EE transition
        min_dr = min([obj.DeltaR(ele) for obj in vetoObjs] or [2*self.min_dr2vetoObjs])
        if min_dr < self.min_dr2vetoObjs : return False

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
            for k in SFs:
                selSFs=[x for x in SFs[k] if x]
                SFs[k] = [self.combineScaleFactors(selSFs)]
            
        return SFs

            
    def fillBranches(self):
        pass
                
    def makeBranches(self, out):
        pass
