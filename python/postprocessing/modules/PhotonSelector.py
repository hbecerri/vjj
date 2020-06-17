from ScaleFactorBase import *
from ObjectSelectorBase import *

class PhotonSelector(ScaleFactorBase , ObjectSelectorBase):

    """ Applies standard photon selections, returning a list of indices of good photons """

    def __init__(self , era, apply_id = True , min_pt=70., max_eta=2.4, dr2vetoObjs=0.4, vetoObjs = [("Muon", "mu"), ("Electron", "ele")]):
        super(ScaleFactorBase, self).__init__()
        super(ObjectSelectorBase, self).__init__()
        self.init() #init scale factor object
        self.setParams(1 , vetoObjs , dofilter=False) #set parameters for object selection

        self.era = era
        self.min_pt = min_pt
        self.max_eta = max_eta
        self.apply_id = apply_id
        self.min_dr2vetoObjs = dr2vetoObjs
        self.indices=[]

        #these files come from https://twiki.cern.ch/twiki/bin/view/CMS/EgammaRunIIRecommendations
        #no need for reconstructed efficiency (assumed to be 100% for superclusters)
        baseSFDir='${CMSSW_BASE}/python/UserCode/VJJSkimmer/postprocessing/etc/'
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


    def collection_name(self):
        return "Photon"

    def obj_name(self):
        if self.apply_id:
            return "photon"
        else:
            return 'loosePhoton'

    def isGood(self, photon):

        if photon.pt < self.min_pt : return False
        absEta=abs( photon.eta )
        if absEta > self.max_eta : return False
        if absEta> 1.4442 and absEta<1.5660 : return False #EB->EE transition
        
        min_dr = self.mindr_toVetoObjs(photon)
        if min_dr < self.min_dr2vetoObjs : return False

        #id+iso requirement (tight id is the 3rd bit)
        hasId=False
        if self.era == 2016:
            hasId=((photon.cutBased>>2)&0x1)
            #hasId=((photon.cutBased17Bitmap>>2) & 0x1)
        elif self.era == 2017:
            hasId=((photon.cutBased>>2)&0x1)
        elif self.era == 2018:
            hasId=((photon.cutBased>>2)&0x1)
        if not hasId and self.apply_id : return False

        #additional requirements
        #ele_veto = photon.electronVeto
        #if not ele_veto : return False
        has_pixelseed = photon.pixelSeed
        if has_pixelseed : return False

        return True

    def fillSFs(self,photons,combined=True):

        """evaluates the scale factors for a collection of photons """

        #SFs={'trig_ajj':[],'trig_highpta':[],'id':[],'pxseed':[]}
        #,mjj=0
        SFs={'id':[],'pxseed':[]}
        for p in photons:

            abseta=abs(p.eta)
            # SFs['trig_ajj'].append(     
            #     self.evalSF('trig_ajj', objAttrs=[p.pt,mjj]) 
            # )
            # SFs['trig_highpta'].append( 
            #     self.evalSF('trig_highpta', objAttrs=[p.pt]) 
            # )
            SFs['id'].append(  
                self.evalSF('id', objAttrs=[p.eta,p.pt]) 
            )
            SFs['pxseed'].append( 
                self.evalSF('pxseed',objAttrs=[3.5 if abseta>1.5 else 0.5]) 
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


photonSelector2016 = lambda : PhotonSelector(2016)
photonSelector2017 = lambda : PhotonSelector(2017)
photonSelector2018 = lambda : PhotonSelector(2018)
loosePhotonSelector2016 = lambda : PhotonSelector(2016 , apply_id=False)
loosePhotonSelector2017 = lambda : PhotonSelector(2017 , apply_id=False)
loosePhotonSelector2018 = lambda : PhotonSelector(2018 , apply_id=False)
