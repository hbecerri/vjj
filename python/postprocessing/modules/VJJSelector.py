import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
import os
import copy
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection 
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from VJJEvent import VJJEvent,_defaultVjjCfg,_defaultGenVjjCfg
import numpy as np

class VJJSelector(Module):

    """Implements a generic V+2j selection for VBF X studies"""

    def __init__(self, isData, era):

        self.isData           = isData
        self.era              = era
        self.vjjEvent         = VJJEvent(cfg=_defaultVjjCfg)
        self.gen_vjjEvent     = None 
        if not isData:
            self.gen_vjjEvent=VJJEvent(cfg=_defaultGenVjjCfg)
 
        self.histos={}

        #triggers of interest
        self.trigList={
            2016: {'ajj'     : ['HLT_Photon75_R9Id90_HE10_Iso40_EBOnly_VBF'],
                   'highpta' : ['HLT_Photon175'],
                   'ee'      : ['HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ'],
                   'mm'      : ['HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ','HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_DZ','HLT_IsoMu24','HLT_IsoTkMu24']},
            2017: {'ajj'     : ['HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3'],
                   'highpta' : ['HLT_Photon200'],
                   'ee'      : ['HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL','HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ'],
                   'mm'      : ['HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ','HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass8','HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8','HLT_IsoMu27']},
            2018: {'ajj'     : ['HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3'],
                   'highpta' : ['HLT_Photon200'],
                   'ee'      : ['HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL','HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ'],
                   'mm'      : ['HLT_IsoMu24']}
        }

        #category codes
        self.finalStates={'a':22,'ee':11*11,'mm':13*13}

        #compile auxiliary C++ code
        script_dir="${CMSSW_BASE}/src/UserCode/VJJSkimmer/python/postprocessing/helpers/"
        ROOT.gROOT.ProcessLine(".L {0}/EventShapeVariables.cc++".format(script_dir))
            
    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):

        outputFile.cd()

        #book aux histos (wgtSum is instantiated on the fly, first time weights are read)
        self.histos={
            'nwgts'   : ROOT.TH1D("nwgts",  ";Number of weights;",3,0,3),
            'cutflow' : ROOT.TH1F('cutflow',';Selection step; Events',4,0,4)
        }

        #define output tree
        self.out = wrappedOutputTree
        self.vjjEvent.makeBranches( self.out )
        self.out.branch('vjj_isGood','O')

        if self.gen_vjjEvent:
            self.gen_vjjEvent.makeBranches(self.out,isGen=True)
            self.out.branch('genvjj_isGood','O')
            self.out.branch('genvjj_hasPromptPhoton','O')
        
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):

        #write histos to output file
        outputFile.cd()
        for _,h in self.histos.items():
            h.SetDirectory(outputFile)
            h.Sumw2()
            h.Write()

    def arbitrateBosonCandidate(self,good_photons,good_muons,good_electrons,trig_cats=None):

        """ 
        arbitrates the boson candidate choice and 
        eventually checks if it's compatible with triggers 
        """

        if len(good_muons)>=2:
            mm=good_muons[0].p4()+good_muons[1].p4()
            goodZmm=(abs(mm.M()-91)<15)
            if trig_cats and trig_cats.count('mm')==0: 
                goodZmm=False
            if goodZmm:
                return 13*13,[1,1],mm
        
        if len(good_electrons)>=2:
            ee=good_electrons[0].p4()+good_electrons[1].p4()
            goodZee=(abs(ee.M()-91)<15)
            if trig_cats and trig_cats.count('ee')==0:
                goodZee=False
            if goodZee:
                return 11*11,[1,1],ee
        
        if len(good_photons)>0:
            #trigger categories are not re-inforced for the photon case
            #so that trigger efficiency can be measured
            isAjj     = 1 if (trig_cats and trig_cats.count('ajj')>0)     else 0
            isHighPtA = 1 if (trig_cats and trig_cats.count('highpta')>0) else 0
            return 22,[isAjj,isHighPtA],good_photons[0].p4()

        return None

    def analyze(self, event):

        """process event, return True (go to next module) or False (fail, go to next event)"""

        isGoodForReco=self.reco_analyze(event)
        self.out.fillBranch('vjj_isGood',isGoodForReco)
        
        isGoodForGen=False
        if self.gen_vjjEvent:
            isGoodForGen=self.gen_analyze(event)
            self.out.fillBranch('genvjj_isGood',isGoodForGen)
        
        return  isGoodForReco or isGoodForGen 


    def gen_analyze(self,event):

        """generator-level specific analysis"""

        if self.isData : return True

        self.gen_vjjEvent.resetOutVars()

        #event weights (for additional weights we divide by the nominal one)
        wgts=[ getattr(event,'Generator_weight',1.0) ]
            
        npswgts=getattr(event,'nPSWeight', 0)
        self.histos['nwgts'].SetBinContent(1,npswgts)
        for i in range( npswgts ):
            wgts.append( wgts[0]*np.divide(event.PSWeight[i],event.PSWeight[0]) )

        nscalewgts=getattr(event, 'nLHEScaleWeight', 0)
        self.histos['nwgts'].SetBinContent(2,nscalewgts)
        for i in range( nscalewgts ):
            wgts.append( wgts[0]*np.divide(event.LHEScaleWeight[i],event.LHEScaleWeight[0]) )

        nlherwgwgts=getattr(event, 'nLHEReweightingWeight', 0)
        self.histos['nwgts'].SetBinContent(3,nlherwgwgts)
        for i in range( nlherwgwgts ):
            wgts.append( wgts[0]*np.divide(event.LHEReweightingWeight[i],event.LHEReweightingWeight[0]) )

        npdfwgts=getattr(event,'nLHEPdfWeight',0 )
        self.histos['nwgts'].SetBinContent(4,npdfwgts)
        for i in range( npdfwgts ):
            wgts.append( wgts[0]*np.divide(event.LHEPdfWeight[i],event.LHEPdfWeight[0]) )

        totalWgts=1+npswgts+nscalewgts+nlherwgwgts+npdfwgts
    
        #if not yet available, instantiate it
        if not 'wgtSum' in self.histos:
            print('Starting wgtSum histogram with',totalWgts,'variations')
            self.histos['wgtSum']=ROOT.TH1D("wgtSum", ";Weight index;Sum",totalWgts,0,totalWgts)

        for i,w in enumerate(wgts):
            self.histos['wgtSum'].Fill(i+0.5 , w)

        self.gen_vjjEvent.fillWeightBranches( {'nwgt':totalWgts, 'wgt':wgts} )


        #select base objects for boson construction
        all_dressedLeptons = Collection(event,'GenDressedLepton')
        def isGoodGenLepton(p,pid):
            if abs(p.pdgId)!=pid: return False
            if p.pt<20 : return False
            if abs(p.eta)>2.4 : return False
            return True
        good_muons = [p for p in all_dressedLeptons if isGoodGenLepton(p,13)]
        good_elecs = [p for p in all_dressedLeptons if isGoodGenLepton(p,11)]
        
        all_genParts = Collection(event,'GenPart')
        def isGoodGenPhoton(p):
            if p.status!=1              : return False
            if (p.statusFlags & 0x1)==0 : return False
            if p.pdgId!=22              : return False
            if p.pt<70                  : return False
            if abs(p.eta)>2.4           : return False
            return True
        good_photons = [p for p in all_genParts if isGoodGenPhoton(p)]

        #add this piece of MC information
        self.out.fillBranch('genvjj_hasPromptPhoton',True if len(good_photons)>0 else False)

        #call boson candidate arbitration
        trig_cats=['mm','ee','ajj','highpta']
        bosonArbitration = self.arbitrateBosonCandidate(good_photons,good_muons,good_elecs,trig_cats)
        if bosonArbitration is None:
            return False
        fsCat,arbTrigCats,boson=bosonArbitration

        #jet selection
        all_genJets = Collection(event,'GenJet')
        vetoObjs    = good_muons+good_elecs+good_photons
        def isGoodGenJet(p,vetoObjs,min_dr2vetoObjs=0.4):
            if p.pt<15 : return False
            if abs(p.eta)>4.7 : return False
            min_dr = min([obj.DeltaR(p) for obj in vetoObjs] or [2*min_dr2vetoObjs])
            if min_dr<min_dr2vetoObjs : return False
            return True
        jets = [ j for j in all_genJets if isGoodGenJet(j,vetoObjs)]

        #analyze v+2j event candidate
        isGoodV2J =  self.gen_vjjEvent.isGoodVJJ( boson, jets, arbTrigCats, fsCat ) 
            
        return isGoodV2J


    def reco_analyze(self,event):
        
        """reco-level specific analysis"""

        self.vjjEvent.resetOutVars()

        self.histos['cutflow'].Fill(0)

        #start possible event categories by checking the triggers that fired
        trig_cats=[]
        for cat,tlist in self.trigList[self.era].items():
            tbits=[ getattr(event,t) if hasattr(event,t) else False for t in tlist ]
            if tbits.count(1)==0: continue
            trig_cats.append(cat)
        if self.isData and len(trig_cats)==0 : return False

        #select base objects for boson construction
        all_muons      = Collection(event, "Muon")
        good_muonsIdx  = event.vjj_mus
        good_muons     = [all_muons[i] for i in good_muonsIdx]

        all_electrons     = Collection(event, "Electron")
        good_electronsIdx = event.vjj_eles
        good_electrons    = [all_electrons[i] for i in good_electronsIdx]

        all_photons     = Collection(event, "Photon")
        good_photonsIdx = event.vjj_photons
        good_photons    = []
        if len(good_photonsIdx)>0:
            good_photons = [ all_photons[ good_photonsIdx[0] ] ]

        #call boson candidate arbitration
        bosonArbitration = self.arbitrateBosonCandidate(good_photons,good_muons,good_electrons,trig_cats)        
        if bosonArbitration is None:
            return False
        fsCat,arbTrigCats,boson=bosonArbitration
        self.histos['cutflow'].Fill(1)

        #jet selection
        all_jets = Collection(event, "Jet")
        jetsIdx  =  event.vjj_jets
        jets     = [all_jets[i] for i in jetsIdx]

        #analyze v+2j event candidate
        isGoodV2J =  self.vjjEvent.isGoodVJJ(boson, jets, arbTrigCats, fsCat) 

        #add additional variables
        if fsCat==22:
            self.vjjEvent.fillPhotonExtraBranches(good_photons[0])

        #fill scale factors
        if isGoodV2J:

            self.histos['cutflow'].Fill(2)
            if len(trig_cats)>0 : self.histos['cutflow'].Fill(3)

            wgt_dict={}

            #photon efficiency
            if fsCat==22:

                trigWgt = (1.,0.)
                wgt_dict['trigWgt']   = trigWgt[0]
                wgt_dict['trigWgtUp'] = trigWgt[0]+trigWgt[1]
                wgt_dict['trigWgtDn'] = trigWgt[0]-trigWgt[1]

                trigWgt = (1.,0.)
                wgt_dict['trigHighPtWgt']   = trigWgt[0]
                wgt_dict['trigHighPtWgtUp'] = trigWgt[0]+trigWgt[1]
                wgt_dict['trigHighPtWgtDn'] = trigWgt[0]-trigWgt[1]

                wgt_dict['effWgt']   = event.vjj_photon_effWgt
                wgt_dict['effWgtUp'] = event.vjj_photon_effWgtUp
                wgt_dict['effWgtDn'] = event.vjj_photon_effWgtDn

            #dilepton efficiency
            if fsCat==11*11 or fsCat==13*13:
                wgt_dict['trigWgt']   = 1
                wgt_dict['trigWgtUp'] = 1
                wgt_dict['trigWgtDn'] = 1
                wgt_dict['trigHighPtWgt']  =1
                wgt_dict['trigHighPtWgtUp']=1
                wgt_dict['trigHighPtWgtDn']=1

                wgt_dict['effWgt']   = getattr( event , "vjj_{0}_effWgt".format( 'mu' if fsCat == 13*13 else "ele" ) )
                wgt_dict['effWgtUp'] = getattr( event , "vjj_{0}_effWgtUp".format( 'mu' if fsCat == 13*13 else "ele" ) )
                wgt_dict['effWgtDn'] = getattr( event , "vjj_{0}_effWgtDn".format( 'mu' if fsCat == 13*13 else "ele" ) )

            #quark gluon discriminator weights (tag jets only)
            wgt_dict['qglgWgt'] = event.vjj_qglgWgt_jets
            wgt_dict['qglqWgt'] = event.vjj_qglqWgt_jets

            self.vjjEvent.fillWeightBranches(wgt_dict)

        #all done here
        return isGoodV2J

        
# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed
vjjSkimmer2016data = lambda : VJJSelector(True , 2016) 
vjjSkimmer2016mc   = lambda : VJJSelector(False , 2016) 
vjjSkimmer2017data = lambda : VJJSelector(True , 2017) 
vjjSkimmer2017mc   = lambda : VJJSelector(False , 2017) 
vjjSkimmer2018data = lambda : VJJSelector(True , 2018) 
vjjSkimmer2018mc   = lambda : VJJSelector(False , 2018) 

