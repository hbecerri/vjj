import ROOT
import copy

_defaultVjjCfg={'max_jetEta':4.7,
                'min_jetPt':20,
                'min_jetdr2v':0.4,
                'min_tagJetPt':40,
                'min_leadTagJetPt':50,
                'min_mjj':200}

_defaultGenVjjCfg={'max_jetEta':4.7,
                   'min_jetPt':15,
                   'min_jetdr2v':0.4,
                   'min_tagJetPt':35,
                   'min_leadTagJetPt':35,
                   'min_mjj':200}

class VJJEvent:

    """A summary of a vector boson + 2 jets event for plotting, stat analysis etc."""

    def __init__(self,cfg=_defaultVjjCfg):
        self.selCfg=copy.deepcopy(cfg)
        self.pfix=''
        self.outvars=[]
        self.photonExtra=[]

    def makeBranches(self, out, isGen=False):

        """ prepare the branches """

        self.out = out

        self.pfix='genvjj_' if isGen else 'vjj_'

        #floating point variables
        for v in ['trigWgt',       'trigWgtUp',       'trigWgtDn',
                  'trigHighPtWgt', 'trigHighPtWgtUp', 'trigHighPtWgtDn',
                  'effWgt',  'effWgtUp',  'effWgtDn',
                  'qglqWgt', 'qglgWgt', 
                  'v_pt', 'v_eta', 'v_phi', 'v_m', 'v_ystar', 
                  'lead_pt', 'lead_eta', 'lead_phi', 'lead_m', 'lead_qgl', 'lead_dr2v',
                  'sublead_pt','sublead_eta','sublead_phi', 'sublead_m', 'sublead_qgl', 'sublead_dr2v',
                  'j_maxEta','j_minEta',
                  'jj_pt','jj_eta','jj_phi','jj_m','jj_dr2v','jj_scalarht','jj_deta','jj_dphi','jj_seta',
                  'vjj_pt', 'vjj_eta', 'vjj_phi', 'vjj_m',
                  'vjj_scalarht', 'vjj_isotropy', 'vjj_circularity', 'vjj_sphericity', 'vjj_aplanarity', 
                  'vjj_C', 'vjj_D',
                  'centj_pt', 'centj_eta', 'centj_phi', 'centj_m', 'centj_ystar', 'centj_dr2v',
                  'htsoft','centhtsoft']:            
            outv=self.pfix+v
            self.outvars.append(outv)
            self.out.branch(outv,'F')

        #reco only
        if not isGen:
            setattr(self,'photonExtra',['r9','sieie','hoe','pfRelIso03_all','pfRelIso03_chg'])
            for v in self.photonExtra:
                outv=self.pfix+'a_'+v
                self.outvars.append(outv)
                self.out.branch(outv,'F')

        # integer variables
        for v in ['nwgt', 'fs', 'trig', 'nextraj','ncentj', 'lead_flav', 'sublead_flav']:
            outv=self.pfix+v
            self.outvars.append(outv)
            self.out.branch(outv,'I')

        #arrays
        self.out.branch(self.pfix+"wgt", "F", lenVar="nwgt")


    def resetOutVars(self):
        
        """reset all values to 0"""

        for v in self.outvars:
            self.out.fillBranch(v,0)
            

    def fillPhotonExtraBranches(self, photon):

        """ special photon variables, they are defined by makeBranches """

        for v in self.photonExtra:
            self.out.fillBranch(self.pfix+'a_'+v,getattr(photon,v))


    def fillWeightBranches(self, wgt_dict):

        """ receives a dict with weights and fills the appropriate branches """

        for key,val in wgt_dict.items():
            self.out.fillBranch(self.pfix+key,val)


    def isGoodVJJ(self, v, jets, trigCats, fsCat ):

        """ fill the branches """

        #check first trigger/final state
        trigWord=0
        for it,tstate in enumerate(trigCats):
            trigWord = trigWord | (tstate<<it)
        self.out.fillBranch(self.pfix+'trig', trigWord)

        self.out.fillBranch(self.pfix+'fs',   fsCat)
        if fsCat<=0 : return False

        #boson selection (base variables)
        self.out.fillBranch(self.pfix+'v_pt',v.Pt())
        veta=v.Eta()
        self.out.fillBranch(self.pfix+'v_eta',veta)
        self.out.fillBranch(self.pfix+'v_phi',v.Phi())
        self.out.fillBranch(self.pfix+'v_m',v.M())

        #select jets
        cleanJets=[j for j in jets if j.DeltaR(v)>self.selCfg['min_jetdr2v'] and abs(j.eta)<self.selCfg['max_jetEta'] and j.pt>self.selCfg['min_jetPt'] ]
        cleanJets.sort(key = lambda x : x.pt, reverse=True)
        
        tagJets=[j for j in cleanJets if j.pt>self.selCfg['min_tagJetPt'] ]
        if len(tagJets)<2 : return False
        if tagJets[0].pt<self.selCfg['min_leadTagJetPt'] : return False

        self.out.fillBranch(self.pfix+'lead_pt',      tagJets[0].pt)
        self.out.fillBranch(self.pfix+'lead_eta',     tagJets[0].eta)
        self.out.fillBranch(self.pfix+'lead_phi',     tagJets[0].phi)
        self.out.fillBranch(self.pfix+'lead_m',       tagJets[0].mass)
        self.out.fillBranch(self.pfix+'lead_dr2v',    tagJets[0].DeltaR(v))
        self.out.fillBranch(self.pfix+'lead_flav',    tagJets[0].partonFlavour)
        self.out.fillBranch(self.pfix+'sublead_pt',   tagJets[1].pt)
        self.out.fillBranch(self.pfix+'sublead_eta',  tagJets[1].eta)
        self.out.fillBranch(self.pfix+'sublead_phi',  tagJets[1].phi)
        self.out.fillBranch(self.pfix+'sublead_m',    tagJets[1].mass)
        self.out.fillBranch(self.pfix+'sublead_dr2v', tagJets[1].DeltaR(v))
        self.out.fillBranch(self.pfix+'sublead_flav', tagJets[1].partonFlavour)

        #reco-level only variables
        try:
            self.out.fillBranch(self.pfix+'lead_qgl',      tagJets[0].qgl)
            self.out.fillBranch(self.pfix+'sublead_qgl',   tagJets[1].qgl)
        except:
            pass

        #dijet system
        jj=tagJets[0].p4()+tagJets[1].p4()
        jj_m=jj.M()
        if(jj_m<self.selCfg['min_mjj']) : return False
        self.out.fillBranch(self.pfix+'jj_m',    jj_m)
        self.out.fillBranch(self.pfix+'jj_pt',   jj.Pt())
        self.out.fillBranch(self.pfix+'jj_eta',  jj.Eta())
        self.out.fillBranch(self.pfix+'jj_phi',  jj.Phi())               
        self.out.fillBranch(self.pfix+'jj_dr2v', jj.DeltaR(v))
        jj_scalarht=tagJets[0].pt+tagJets[1].pt
        self.out.fillBranch(self.pfix+'jj_scalarht',jj_scalarht)
        etaList=[abs(tagJets[0].eta),abs(tagJets[1].eta)]
        maxEta=max(etaList)
        minEta=min(etaList)
        self.out.fillBranch(self.pfix+'j_maxEta',maxEta)
        self.out.fillBranch(self.pfix+'j_minEta',minEta)
        self.out.fillBranch(self.pfix+'jj_deta',(maxEta-minEta))
        jj_seta=(maxEta+minEta)
        self.out.fillBranch(self.pfix+'jj_seta',jj_seta)
        self.out.fillBranch(self.pfix+'jj_dphi',tagJets[0].p4().DeltaPhi( tagJets[1].p4() ))
        self.out.fillBranch(self.pfix+'v_ystar',veta-0.5*jj_seta)
        
        #hard process object candidates
        vjj=v+jj;
        self.out.fillBranch(self.pfix+'vjj_pt', vjj.Pt())
        self.out.fillBranch(self.pfix+'vjj_eta',vjj.Eta())
        self.out.fillBranch(self.pfix+'vjj_phi',vjj.Phi())
        self.out.fillBranch(self.pfix+'vjj_m',  vjj.M())
        self.out.fillBranch(self.pfix+'vjj_scalarht',v.Pt()+jj_scalarht)

        eventShape = ROOT.EventShapeVariables()
        eventShape.addObject( v )
        eventShape.addObject( tagJets[0].p4() )
        eventShape.addObject( tagJets[1].p4() )
        self.out.fillBranch(self.pfix+"vjj_isotropy",    eventShape.isotropy() )
        self.out.fillBranch(self.pfix+"vjj_circularity", eventShape.circularity() )
        self.out.fillBranch(self.pfix+"vjj_sphericity",  eventShape.sphericity() )
        self.out.fillBranch(self.pfix+"vjj_aplanarity",  eventShape.aplanarity() )
        self.out.fillBranch(self.pfix+"vjj_C",           eventShape.C() )
        self.out.fillBranch(self.pfix+"vjj_D",           eventShape.D() )
        del eventShape

        #extra radiation activity
        extraJets=[j for j in cleanJets if not j in tagJets]
        nextraj,ncentj=len(extraJets),0
        htsoft,centhtsoft=0.,0.
        for j in extraJets:
            htsoft+=j.pt
            if j.eta<minEta+0.2 : continue
            if j.eta>maxEta+0.2 : continue
            ncentj+=1
            centhtsoft+=j.pt
            if ncentj>1 : continue
            self.out.fillBranch(self.pfix+'centj_pt',j.pt)
            self.out.fillBranch(self.pfix+'centj_eta',j.eta)
            self.out.fillBranch(self.pfix+'centj_phi',j.phi)
            self.out.fillBranch(self.pfix+'centj_m',  j.mass)
            self.out.fillBranch(self.pfix+'centj_ystar',j.eta-0.5*jj_seta)
            self.out.fillBranch(self.pfix+'centj_dr2v',j.DeltaR(v))
        
        self.out.fillBranch(self.pfix+'ncentj',ncentj)
        self.out.fillBranch(self.pfix+'centhtsoft',centhtsoft)
        self.out.fillBranch(self.pfix+'nextraj',nextraj)
        self.out.fillBranch(self.pfix+'htsoft',htsoft)

        #ready to fill entry
        return True

        
