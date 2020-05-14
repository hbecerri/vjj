from ScaleFactorBase import *

class JetSelector(ScaleFactorBase):

    """ Applies standard jet selections, returning a list of indices of good jets """

    def __init__(self , era, min_pt=20, max_eta=4.7, dr2vetoObjs=0.4, applyPUid=True, applyEraAdHocCuts=True):

        self.era               = era
        self.min_pt            = min_pt
        self.max_eta           = max_eta
        self.min_dr2vetoObjs   = dr2vetoObjs
        self.applyPUid         = applyPUid
        self.applyEraAdHocCuts = applyEraAdHocCuts
        self.indices           = []

        ScaleFactorBase.__init__(self)

        #quark-gluon weights
        self.addSFObject(tag='qglgWgt',
                          obj=ROOT.TF1('qgsf_g','min(max(0.5,55.7067*pow(x,7) + 113.218*pow(x,6) -21.1421*pow(x,5) -99.927*pow(x,4) + 92.8668*pow(x,3) -34.3663*pow(x,2) + 6.27*x + 0.612992),2.)'))
        self.addSFObject(tag='qglqWgt',
                          obj=ROOT.TF1('qgsf_q','min(max(0.5,-0.666978*pow(x,3) + 0.929524*pow(x,2) -0.255505*x + 0.981581),2.)'))


    def __call__(self , jets , veto_objs, returnIndices=True ):

        self.indices=[i for i,j in enumerate(jets) if self.isGood(j,veto_objs) ]        

        if not returnIndices:
            return [jets[i] for i in self.indices]

        return self.indices

    def isGood(self,jet,vetoObjs):

        """ checks if jet is good for analysis applying a series of standard cuts """
        
        #base cuts
        if jet.pt < self.min_pt : return False
        abseta=abs(jet.eta)
        if abseta > self.max_eta : return False        
        min_dr = min([obj.DeltaR(jet) for obj in vetoObjs] or [2*self.min_dr2vetoObjs])
        if min_dr < self.min_dr2vetoObjs : return False

        #id bits
        #https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookNanoAOD#Jets

        #pileup id (optional)
        if self.applyPUid:
            loosePuID=((jet.puId>>2) & 1)
            if loosePuID!=1:
                return False

        #jet id: loose + tightLepVeto (these are run-dependent, see below)
        looseID=(jet.jetId & 1)
        tightLepVeto=((jet.jetId>>2) & 1)

        #era-dependent (optional)
        if self.applyEraAdHocCuts :

            if self.era == 2016 :

                if looseID==0:
                    return False

            if self.era == 2017:
                
                if tightLepVeto==0 : 
                    return False

                #ECAL noise (2017)
                if abseta>2.650 and abseta<3.139:
                    if jet.chEmEF+jet.neEmEF > 0.55: 
                        return False
                
            if self.era == 2018:

                if tightLepVeto==0:
                    return False

                #HEM 15/16 failure (2018)
                if jet.eta>-3.0 and jet.eta<-1.3 and jet.phi>-1.57 and jet.phi<-0.87:
                    return False

        return True

    def fillSFs(self,jets):

        SFs={'qglgWgt':[],'qglqWgt':[]}

        for j in jets:
            flav=j.partonFlavour
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

        return SFs

    def fillBranches(self):
        pass
        
    def makeBranches(self, out):
        pass        
        
