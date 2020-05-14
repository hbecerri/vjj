from ScaleFactorBase import *

class MuonSelector(ScaleFactorBase):

    def __init__(self , era, min_pt=20., max_eta=2.4, dr2vetoObjs=0.4):
        self.era = era
        self.min_pt = min_pt
        self.max_eta = max_eta
        self.min_dr2vetoObjs   = dr2vetoObjs
        self.indices=[]

        #scale factors for electron objects
        ScaleFactorBase.__init__(self)

        #these files come from https://twiki.cern.ch/twiki/bin/view/CMS/MuonPOG
        baseSFDir='${CMSSW_BASE}/src/UserCode/VJJSkimmer/python/postprocessing/etc/'
        muSFSources={
            2016:{
                'id'     : (os.path.join(baseSFDir,'2016_RunBCDEF_SF_ID.root'),  'NUM_TightID_DEN_genTracks_pt_abseta'),
                'id_gh'  : (os.path.join(baseSFDir,'2016_RunGH_SF_ISO.root'),    'NUM_TightID_DEN_genTracks_pt_abseta'),
                'iso'    : (os.path.join(baseSFDir,'2016_RunBCDEF_SF_ISO.root'), 'NUM_TightRelIso_DEN_TightIDandIPCut_pt_abseta'),
                'iso_gh' : (os.path.join(baseSFDir,'2016_RunGH_SF_ISO.root'),    'NUM_TightRelIso_DEN_TightIDandIPCut_pt_abseta'),

              },
            2017:{
                'id'  : (os.path.join(baseSFDir,'RunBCDEF_SF_ID_syst.root'),  'NUM_TightID_DEN_genTracks_pt_abseta'),
                'iso' : (os.path.join(baseSFDir,'RunBCDEF_SF_ISO_syst.root'), 'NUM_TightRelIso_DEN_TightIDandIPCut_pt_abseta'),
                },
            2018:{
                'id'       : (os.path.join(baseSFDir,'RunABCD_SF_ID.root'),  'NUM_TightID_DEN_genTracks_pt_abseta'),
                'iso'      : (os.path.join(baseSFDir,'RunABCD_SF_ISO.root'), 'NUM_TightRelIso_DEN_TightIDandIPCut_pt_abseta'),
                }        
        }    
        for k in muSFSources[self.era]:
            url,obj=muSFSources[self.era][k]
            self.addSFFromSource(k,url,obj)


        pass

    def __call__(self, muons, vetoObjs):
        self.indices=[i for i,mu in enumerate(muons) if self.isGood(mu,vetoObjs)]
        return self.indices

    def isGood(self, mu, vetoObjs):

        if mu.pt < self.min_pt : return False
        if abs( mu.eta ) > self.max_eta : return False
        min_dr = min([obj.DeltaR(mu) for obj in vetoObjs] or [2*self.min_dr2vetoObjs])
        if min_dr < self.min_dr2vetoObjs : return False

        hasId=mu.tightId
        if not hasId : return False

        isIso=(mu.pfRelIso04_all<0.15)
        if not isIso : return False

        return True

    def fillSFs(self,muons,combined=True):

        """evaluates the scale factors for a collection of muons """

        SFs={'id':[],'iso':[]}
        for m in muons:

            abseta=abs(m.eta)
            for k in SFs:
                sfVal=self.evalSF(k, objAttrs=[m.pt,abseta]) 

                #average by luminosity in 2016
                if self.era==2016:
                    sfValGH=self.evalSF(k+'_gh', objAttrs=[m.pt,abseta]) 
                    w=16551.4/(16551.4+19323.4)
                    sfVal=(w*sfVal[0]+(1-w)*sfValGH[0],
                           np.sqrt( (w*sfVal[1])**2 + ((1-w)*sfValGH[1])**2 ) )

                SFs[k].append( sfVal )

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

