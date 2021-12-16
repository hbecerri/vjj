from ScaleFactorBase import *
from ObjectSelectorBase import *
import numpy as np
from VJJEvent import _defaultObjCfg
import copy

class JetSelector(ScaleFactorBase, ObjectSelectorBase):

    """ Applies standard jet selections, returning a list of indices of good jets """

    def __init__(self , era, cfg=_defaultObjCfg, applyPUid=True, apply_id=True, applyEraAdHocCuts=True , vetoObjs = [("Muon", "mu"), ("Electron", "ele"), ("Photon", "photon")], JMEvar=""):
        super(ScaleFactorBase, self).__init__()
        super(ObjectSelectorBase, self).__init__()
        self.init() #init scale factor object
        self.setParams(2 , vetoObjs , dofilter=False, JMEvar=JMEvar) #set parameters for object selection

        self.era               = era
        self.selCfg            = copy.deepcopy(cfg)
        self.applyPUid         = applyPUid
        self.apply_id          = apply_id
        if not apply_id:
            self.applyPUid     = False
        self.applyEraAdHocCuts = applyEraAdHocCuts
        self.indices           = []
        self.JMEvar            = JMEvar #'' <-> nominal; else, will consider the updated jet collection corresponding to this JME variation

        #quark-gluon weights
        self.addSFObject(tag='qglgWgt',
                          obj=ROOT.TF1('qgsf_g','min(max(0.5,55.7067*pow(x,7) + 113.218*pow(x,6) -21.1421*pow(x,5) -99.927*pow(x,4) + 92.8668*pow(x,3) -34.3663*pow(x,2) + 6.27*x + 0.612992),2.)'))
        self.addSFObject(tag='qglqWgt',
                          obj=ROOT.TF1('qgsf_q','min(max(0.5,-0.666978*pow(x,3) + 0.929524*pow(x,2) -0.255505*x + 0.981581),2.)'))

    def collection_name(self):
        return "Jet"

    def obj_name(self):
        if self.apply_id:
            name = 'jet'
        else:
            name = "looseJet"
        if self.JMEvar != "": name+= "s_{}".format(self.JMEvar) #Ex: 'jets_TotalUp' for JEC variation 'TotalUp'  (NB: add the 's' suffix here, not in ObjectSelectorBase like for other objects, to get correct naming)
        return name

    def weight_names(self):
        return ["vjj_qglqWgt_{0}s".format(self.obj_name()) , "vjj_qglgWgt_{0}s".format( self.obj_name() )]

    def isGood(self, jet):

        """ checks if jet is good for analysis applying a series of standard cuts """

        if jet.pt < self.selCfg['min_jetPt']  :  return False
        abseta=abs(jet.eta)
        if abseta > self.selCfg['max_jetEta'] :  return False
        min_dr = self.mindr_toVetoObjs(jet) 
        if min_dr < self.selCfg['min_drVeto'] :  return False

        #id bits
        #https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookNanoAOD#Jets
        #https://twiki.cern.ch/twiki/bin/view/CMS/PileupJetIDUL
        #pileup id (optional)
        if self.applyPUid:
            loosePuID = ((jet.puId > 0) if self.era == 2016 else (jet.puId > 3))
            if not loosePuID: 
                return False

        #jet id in UL: only tight and tightLeptonVeto are supported. No loose anymore
        #tightleptonveto is recommended
        #https://twiki.cern.ch/twiki/bin/view/CMS/JetID13TeVUL
        #https://twiki.cern.ch/twiki/bin/viewauth/CMS/JetID#nanoAOD_Flags

        if self.apply_id:
            tightLeptonVeto=((jet.jetId > 5) if self.era == 2016 else (jet.jetId > 6))
            if not tightLeptonVeto: 
                return False

        #era-dependent (optional)
        if self.applyEraAdHocCuts :
            if self.era == 2018:
                #HEM 15/16 failure (2018)
                if jet.eta>-3.0 and jet.eta<-1.3 and jet.phi>-1.57 and jet.phi<-0.87:
                    return False
        return True

    def fillSFs(self, jets, combined=True):

        SFs={'qglgWgt':[],'qglqWgt':[]}

        for j in jets:
            flav=getattr( j , 'partonFlavour') if hasattr( j , 'partonFlavour') else 0
            objAttrs=[j.qgl]
            if flav==21:
                SFs['qglgWgt'].append( self.evalSF('qglgWgt',objAttrs) )
                SFs['qglqWgt'].append( None )
            elif flav!=0:
                SFs['qglgWgt'].append( None )
                SFs['qglqWgt'].append( self.evalSF('qglqWgt',objAttrs) )
            else:
                SFs['qglqWgt'].append( None )
                SFs['qglgWgt'].append( None )

        #combine scale factors
        if combined:
            ret = {}
            for k in SFs:
                selSFs=[x for x in SFs[k] if x]
                ret["vjj_{0}_{1}s".format( k, self.obj_name() )] = np.prod( selSFs )
            return ret

        return SFs


jetSelector2016 = lambda apply_id=True : JetSelector(2016,_defaultObjCfg, apply_id=apply_id)
jetSelector2017 = lambda apply_id=True : JetSelector(2017,_defaultObjCfg, apply_id=apply_id)
jetSelector2018 = lambda apply_id=True : JetSelector(2018,_defaultObjCfg, apply_id=apply_id)
