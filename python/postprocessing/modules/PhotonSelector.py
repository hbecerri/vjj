from ScaleFactorBase import *

class PhotonSelector(ScaleFactorBase):

    """ Applies standard photon selections, returning a list of indices of good photons """

    def __init__(self , era, min_pt=75., max_eta=2.4, dr2vetoObjs=0.4):
        self.era = era
        self.min_pt = min_pt
        self.max_eta = max_eta
        self.min_dr2vetoObjs = dr2vetoObjs
        self.indices=[]

        #scale factors for photon objects
        ScaleFactorBase.__init__(self)

        #these files come from https://twiki.cern.ch/twiki/bin/view/CMS/EgammaRunIIRecommendations
        #no need for reconstructed efficiency (assumed to be 100% for superclusters)
        baseSFDir='${CMSSW_BASE}/src/UserCode/VJJSkimmer/python/postprocessing/etc/'
        photonSFSources={
            2016:{
                'id'     : (os.path.join(baseSFDir,'Fall17V2_2016_Tight_photons.root'),          'EGamma_SF2D'),
              },
            2017:{
                'id'     : (os.path.join(baseSFDir,'2017_PhotonsTight.root'),                         'EGamma_SF2D'),
                'pxseed' : (os.path.join(baseSFDir,'PixelSeed_ScaleFactors_2017.root'),               'Tight_ID'),
                },
            2018:{
                'id'     : (os.path.join(baseSFDir,'2018_PhotonsTight.root'),               'EGamma_SF2D'),
                }        
        }    
        for k in photonSFSources[self.era]:
            url,obj=photonSFSources[self.era][k]
            self.addSFFromSource(k,url,obj)


    def __call__(self, photons , vetoObjs):
        self.indices=[i for i,a in enumerate(photons) if self.isGood(a,vetoObjs)]
        return self.indices

    def isGood(self, photon, vetoObjs):

        if photon.pt < self.min_pt : return False
        absEta=abs( photon.eta )
        if absEta > self.max_eta : return False
        if absEta> 1.4442 and absEta<1.5660 : return False #EB->EE transition
        
        min_dr = min([obj.DeltaR(photon) for obj in vetoObjs] or [2*self.min_dr2vetoObjs])
        if min_dr < self.min_dr2vetoObjs : return False

        #id+iso requirement (tight id is the 3rd bit)
        hasId=False
        if self.era == 2016:
            hasId=((photon.cutBasedV1Bitmap>>2)&0x1)
        elif self.era == 2017:
            hasId=((photon.cutBasedV1Bitmap>>2)&0x1)
        elif self.era == 2018:
            hasId=((photon.cutBasedV1Bitmap>>2)&0x1)
        if not hasId : return False

        #additional requirements
        #ele_veto = photon.electronVeto
        #if not ele_veto : return False
        has_pixelseed = photon.pixelSeed
        if has_pixelseed : return False

        return True

    def fillSFs(self,photons,mjj=0,combined=True):

        """evaluates the scale factors for a collection of photons """

        SFs={'trig_ajj':[],'trig_highpta':[],'id':[],'pxseed':[]}
        for p in photons:

            abseta=abs(p.eta)
            SFs['trig_ajj'].append(     
                self.evalSF('trig_ajj', objAttrs=[p.pt,mjj]) 
            )
            SFs['trig_highpta'].append( 
                self.evalSF('trig_highpta', objAttrs=[p.pt]) 
            )
            SFs['id'].append(  
                self.evalSF('id', objAttrs=[p.eta,p.pt]) 
            )
            SFs['pxseed'].append( 
                self.evalSF('pxseed',objAttrs=[3.5 if abseta>1.5 else 0.5]) 
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
