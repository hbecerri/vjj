from ScaleFactorBase import *
from ObjectSelectorBase import *
from VJJEvent import _defaultVjjSkimCfg

class PhotonSelector(ScaleFactorBase , ObjectSelectorBase):

    """ Applies standard photon selections, returning a list of indices of good photons """

    def __init__(self , era, min_pt, max_eta, apply_id = True , dr2vetoObjs=0.4, vetoObjs = [("Muon", "mu"), ("Electron", "ele")], vpf=''):
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
        # PixelSeed2016 = ''
        # if vpf=='pre': PixelSeed2016 = 'HasPix_SummaryPlot_UL16_preVFP.root'
        # if vpf=='post': PixelSeed2016 = 'HasPix_SummaryPlot_UL16_postVFP.root'
        photonSFSources={
            2016:{ 
                'id'     : (os.path.join(baseSFDir,'egammaEffi.txt_EGM2D_Pho_Tight_UL16.root'),          'EGamma_SF2D'),
#                'pxseed' : (os.path.join(baseSFDir, PixelSeed2016),                                      'Tight_ID'),
                'pxseed' : (os.path.join('HasPix_SummaryPlot_UL16_preVFP.root' if vpf=='pre' else 'HasPix_SummaryPlot_UL16_postVFP.root'), 'Tight_ID'),
              },
            2017:{
                'id'     : (os.path.join(baseSFDir,'egammaEffi.txt_EGM2D_PHO_Tight_UL17.root'),          'EGamma_SF2D'),
                'pxseed' : (os.path.join(baseSFDir,'HasPix_SummaryPlot_UL17.root'),                      'Tight_ID'),
                },
            2018:{
                'id'     : (os.path.join(baseSFDir,'egammaEffi.txt_EGM2D_PHO_Tight_UL18.root'),          'EGamma_SF2D'),
                'pxseed' : (os.path.join(baseSFDir,'HasPix_SummaryPlot_UL18.root'),                      'Tight_ID'),
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

        if self.apply_id:
            hasId= False
            hasId= photon.cutBased == 3
            if not hasId:
                return False

        has_pixelseed = photon.pixelSeed
        if has_pixelseed : return False

        return True

    def fillSFs(self,photons,combined=True):

        """evaluates the scale factors for a collection of photons """

        SFs={'id':[],'pxseed':[]}
        for p in photons:

            abseta=abs(p.eta)

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


photonSelector2016pre = lambda : PhotonSelector(2016, _defaultVjjSkimCfg['min_photonPt'] , _defaultVjjSkimCfg['max_photonEta'], apply_id = True , dr2vetoObjs=0.4, vetoObjs = [("Muon", "mu"), ("Electron", "ele")], vpf='pre' )
photonSelector2016post = lambda : PhotonSelector(2016, _defaultVjjSkimCfg['min_photonPt'] , _defaultVjjSkimCfg['max_photonEta'], apply_id = True , dr2vetoObjs=0.4, vetoObjs = [("Muon", "mu"), ("Electron", "ele")], vpf='post' ) 
photonSelector2017 = lambda : PhotonSelector(2017, _defaultVjjSkimCfg['min_photonPt'] , _defaultVjjSkimCfg['max_photonEta'] )
photonSelector2018 = lambda : PhotonSelector(2018, _defaultVjjSkimCfg['min_photonPt'] , _defaultVjjSkimCfg['max_photonEta'] )
loosePhotonSelector2016pre = lambda : PhotonSelector(2016 , _defaultVjjSkimCfg['min_photonPt'] , _defaultVjjSkimCfg['max_photonEta'] ,apply_id=False, dr2vetoObjs=0.4, vetoObjs = [("Muon", "mu"), ("Electron", "ele")], vpf='pre')
loosePhotonSelector2016post = lambda : PhotonSelector(2016 , _defaultVjjSkimCfg['min_photonPt'] , _defaultVjjSkimCfg['max_photonEta'] ,apply_id=False, dr2vetoObjs=0.4, vetoObjs = [("Muon", "mu"), ("Electron", "ele")], vpf='post')
loosePhotonSelector2017 = lambda : PhotonSelector(2017 , _defaultVjjSkimCfg['min_photonPt'] , _defaultVjjSkimCfg['max_photonEta'] ,apply_id=False)
loosePhotonSelector2018 = lambda : PhotonSelector(2018 , _defaultVjjSkimCfg['min_photonPt'] , _defaultVjjSkimCfg['max_photonEta'] ,apply_id=False)
