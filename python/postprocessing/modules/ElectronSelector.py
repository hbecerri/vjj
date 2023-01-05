from ScaleFactorBase import *
from ObjectSelectorBase import *
from VJJEvent import _defaultObjCfg
import copy

class ElectronSelector(ScaleFactorBase, ObjectSelectorBase):

    """ Applies standard electron selections, returning a list of indices of good photons """

    def __init__(self , era, cfg=_defaultObjCfg , vetoObjs = [("Muon", "mu")], vpf=''):
        super(ScaleFactorBase, self).__init__()
        super(ObjectSelectorBase, self).__init__()
        self.init() #init scale factor object
        self.setParams(2 , vetoObjs , dofilter=False) #set parameters for object selection

        self.era = era
        self.selCfg = copy.deepcopy(cfg)
        self.indices=[]

        #these files come from https://twiki.cern.ch/twiki/bin/view/CMS/EgammaRunIIRecommendations
	#UL electron ID comes from https://twiki.cern.ch/twiki/bin/view/CMS/EgammaUL2016To2018    --Nov 19, rec SF needs to be updated.
        baseSFDir='${CMSSW_BASE}/python/UserCode/VJJSkimmer/postprocessing/etc/'
        eleSFSources={
            2016:{
                'rec'    : (os.path.join(baseSFDir,'egammaEffi_ptAbove20.txt_EGM2D_UL2016preVFP.root' if vpf=='pre' else 'egammaEffi_ptAbove20.txt_EGM2D_UL2016postVFP.root'),    'EGamma_SF2D'),
		'id'     : (os.path.join(baseSFDir,'egammaEffi.txt_Ele_wp80iso_preVFP_EGM2D.root' if vpf=='pre' else 'egammaEffi.txt_Ele_wp80iso_postVFP_EGM2D.root'), 'EGamma_SF2D'),
              },
            2017:{
                'rec'    : (os.path.join(baseSFDir,'egammaEffi_ptAbove20.txt_EGM2D_UL2017.root'), 'EGamma_SF2D'),
                'id'     : (os.path.join(baseSFDir,'egammaEffi.txt_EGM2D_MVA80iso_UL17.root'),        'EGamma_SF2D'),
                },
            2018:{
                'rec'    : (os.path.join(baseSFDir,'egammaEffi_ptAbove20.txt_EGM2D_UL2018.root'), 'EGamma_SF2D'),
		'id'     : (os.path.join(baseSFDir,'egammaEffi.txt_Ele_wp80iso_EGM2D.root'), 'EGamma_SF2D'),
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
        print('ele length:',len(electrons),SFs)
        #combine scale factors
        if combined:
            selSFs = []
            combSFs={}
            a=[]
            for k in SFs:
                selSFs=( [x for x in SFs[k] if x] )
                combSFs[k] = self.combineScaleFactors(selSFs)
                print(selSFs,combSFs)
                a.extend([ combSFs[k][0] , combSFs[k][0]+combSFs[k][1] , combSFs[k][0]-combSFs[k][1] ])
            ret = dict( zip( self.weight_names() , a ) )
            print(self.weight_names(),ret)
            return ret


        return SFs

electronSelector2016pre = lambda : ElectronSelector(2016,vpf='pre')
electronSelector2016post = lambda : ElectronSelector(2016,vpf='post')
electronSelector2017 = lambda : ElectronSelector(2017)
electronSelector2018 = lambda : ElectronSelector(2018)
