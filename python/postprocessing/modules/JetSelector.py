from ScaleFactorBase import *
from ObjectSelectorBase import *
import numpy as np

class JetSelector(ScaleFactorBase , ObjectSelectorBase ):

    """ Applies standard jet selections, returning a list of indices of good jets """

    def __init__(self , era, min_pt=20, max_eta=4.7, dr2vetoObjs=0.4, applyPUid=True, applyEraAdHocCuts=True , vetoObjs = [("Muon", "mu"), ("Electron", "ele"), ("Photon", "photon")] ):
        super(ScaleFactorBase, self).__init__()
        super(ObjectSelectorBase, self).__init__()
        self.init() #init scale factor object
        self.setParams(2 , vetoObjs , dofilter=False) #set parameters for object selection

        self.era               = era
        self.min_pt            = min_pt
        self.max_eta           = max_eta
        self.min_dr2vetoObjs   = dr2vetoObjs
        self.applyPUid         = applyPUid
        self.applyEraAdHocCuts = applyEraAdHocCuts
        self.indices           = []

        #quark-gluon weights
        self.addSFObject(tag='qglgWgt',
                          obj=ROOT.TF1('qgsf_g','min(max(0.5,55.7067*pow(x,7) + 113.218*pow(x,6) -21.1421*pow(x,5) -99.927*pow(x,4) + 92.8668*pow(x,3) -34.3663*pow(x,2) + 6.27*x + 0.612992),2.)'))
        self.addSFObject(tag='qglqWgt',
                          obj=ROOT.TF1('qgsf_q','min(max(0.5,-0.666978*pow(x,3) + 0.929524*pow(x,2) -0.255505*x + 0.981581),2.)'))

    def collection_name(self):
        return "Jet"

    def obj_name(self):
        return "jet"

    def weight_names(self):
        return ["vjj_qglqWgt_jets" , "vjj_qglgWgt_jets"]

    def isGood(self,jet):

        """ checks if jet is good for analysis applying a series of standard cuts """
        
        #base cuts
        #print('pt',jet.pt),
        if jet.pt < self.min_pt : 
            #print("NO")
            return False
        #print('eta',abs(jet.eta), self.max_eta),
        abseta=abs(jet.eta)
        if abseta > self.max_eta :
            #print("NO")
            return False        
        min_dr = self.mindr_toVetoObjs(jet) #min([obj.DeltaR(jet) for obj in vetoObjs] or [2*self.min_dr2vetoObjs])
        #print('mindr',min_dr < self.min_dr2vetoObjs),
        if min_dr < self.min_dr2vetoObjs : 
            #print("NO")
            return False

        #id bits
        #https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookNanoAOD#Jets

        #pileup id (optional)
        if self.applyPUid:
            loosePuID=((jet.puId>>2) & 1)
            #print('loosepuid',loosePuID),
            if loosePuID!=1:
                #print("NO")
                return False

        #jet id: loose + tightLepVeto (these are run-dependent, see below)
        looseID=(jet.jetId & 1)
        tightLepVeto=((jet.jetId>>2) & 1)

        #era-dependent (optional)
        if self.applyEraAdHocCuts :

            if self.era == 2016 :
                
                if looseID==0:
                    #print("NO")
                    return False

            if self.era == 2017:
                #print('id',tightLepVeto),
                if tightLepVeto==0 : 
                    #print("NO")
                    return False

                #ECAL noise (2017)
                #print("ECAL NOISE"),
                if abseta>2.650 and abseta<3.139:
                    if jet.chEmEF+jet.neEmEF > 0.55: 
                        #print("NO")
                        return False
                
            if self.era == 2018:

                if tightLepVeto==0:
                    return False

                #HEM 15/16 failure (2018)
                if jet.eta>-3.0 and jet.eta<-1.3 and jet.phi>-1.57 and jet.phi<-0.87:
                    return False
        #print("PASS")
        return True

    def fillSFs(self,jets , combined=True):

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
                ret["vjj_{0}_jets".format(k)] = np.prod( selSFs )
            return ret

        return SFs

        
jetSelector2016 = lambda : JetSelector(2016)
jetSelector2017 = lambda : JetSelector(2017)
jetSelector2018 = lambda : JetSelector(2018)
