import ROOT
from abc import ABCMeta, abstractproperty, abstractmethod
ROOT.PyConfig.IgnoreCommandLineOptions = True
import os
import copy
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection 
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from VJJEvent import VJJEvent,_defaultVjjCfg,_defaultGenVjjCfg,_defaultVjjSkimCfg
import numpy as np
from TriggerLists import defineTriggerList
from PhysicsTools.NanoAODTools.postprocessing.modules.common.muonScaleResProducer import *


class VJJSelector(Module):

    """Implements a generic V+2j selection for VBF X studies"""
    """Regions are MM, EE, A, Af"""
    def __init__(self, isData, era, signal=False, finalState = 22):
        self.isData           = isData
        self.era              = era
        self.bypassSelFilters = signal
        #self.sampleTag        = sampleTag
        self.vjjEvent         = VJJEvent(_defaultVjjCfg,finalState)
        self.gen_vjjEvent     = None 
        if not isData:# and signal:
            self.gen_vjjEvent=VJJEvent(_defaultGenVjjCfg,finalState)
 
        self.histos={}

        #get trigger list for this year
        self.trig_dict,self.ctrl_trig_dict = defineTriggerList(self.era)
        print('Will use the following set of triggers',self.trig_dict, self.ctrl_trig_dict)

        self.fs = finalState
        #category codes
        self.triggerCatCode={'ajj':[22,-22], 'highpta':[22,-22], 'ee':[121], 'mm':[169]}
        self.hltCats = []
        for cat, idc in self.triggerCatCode.items():
            for id_ in idc:
                if id_ == self.fs: self.hltCats.append(cat)

        #Try to load module via python dictionaries
        try:
            ROOT.gSystem.Load("libUserCodeVJJSkimmer")
            dummy = ROOT.EventShapeVariables
            #Load it via ROOT ACLIC. NB: this creates the object file in the CMSSW directory,
            #causing problems if many jobs are working from the same CMSSW directory
        except Exception as e:
            print "Could not load module via python, trying via ROOT", e
            if "/EventShapeVariables_cc.so" not in ROOT.gSystem.GetLibraries():
                print "Load C++ Worker"
                ROOT.gROOT.ProcessLine(".L %s/src/UserCode/VJJSkimmer/src/EventShapeVariables.cc++" % os.environ['CMSSW_BASE'])
            dummy = ROOT.EventShapeVariables
            
    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):

        outputFile.cd()

        #book aux histos (wgtSum is instantiated on the fly, first time weights are read)
        self.histos={
            'nwgts'   : ROOT.TH1D("nwgts",  ";Number of weights;",3,0,3),
            'cutflow' : ROOT.TH1F('cutflow',';Selection step; Events',8,-4,4)
        }

        #define output tree
        self.out = wrappedOutputTree
        self.vjjEvent.makeBranches( self.out )
        self.out.branch('vjj_isGood','O')

        if self.gen_vjjEvent:
            self.gen_vjjEvent.makeBranches(self.out,isGen=True)
            self.out.branch('genvjj_isGood','O')
            self.out.branch('genvjj_hasPromptPhoton','O')
            if abs(self.fs) != 22:
                self.out.branch('genvjj_leadlep_pt','F')
                self.out.branch('genvjj_subleadlep_pt','F')
                self.out.branch('genvjj_leadlep_eta','F')
                self.out.branch('genvjj_subleadlep_eta','F')
                self.out.branch('genvjj_leadlep_phi','F')
                self.out.branch('genvjj_subleadlep_phi','F')
        
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):

        #write histos to output file
        outputFile.cd()
        for _,h in self.histos.items():
            h.SetDirectory(outputFile)
            h.Sumw2()
            h.Write()


    def TriggerSelection(self,event):
        """ decide on trigger based on final state 22, -22, 169, 121 """
        trid_dict_items = self.trig_dict.items()
        if self.fs == -22: trid_dict_items = self.ctrl_trig_dict.items()
        trig_cats=[]
        for cat,tlist in self.trig_dict.items():
            if cat in self.hltCats:
                tbits=[ getattr(event,t) if hasattr(event,t) else False for t in tlist ]
                if tbits.count(1)==0: continue
                trig_cats.append(cat)
        return trig_cats

    def BosonSelection(self, good_objs, fs, trig_cats=None):
        """ Select Z or photon candidate. Check with trigger for Z """
        if abs(fs) != 22:
            if len(good_objs)>=2:
                v4=good_objs[0].p4()+good_objs[1].p4()
                goodZ=(abs(v4.M()-91)<15)            
                if trig_cats and trig_cats.count(self.hltCats[0])==0:
                    goodZ=False
                if goodZ:
                    return self.fs,[1,1],v4
        else:
            if len(good_objs)>0:
                isAjj     = 1 if (trig_cats and trig_cats.count('ajj')>0)     else 0
                isHighPtA = 1 if (trig_cats and trig_cats.count('highpta')>0) else 0
                return self.fs,[isAjj,isHighPtA],good_objs[0].p4()
        return None


    def isGoodGenParticle(self,p,pid):
        if abs(p.pdgId)!=pid                   : return False
        if abs(pid) == 22:
            if p.status!=1                                           : return False
            if (p.statusFlags & 0x1)==0                              : return False
            if p.pt< self.gen_vjjEvent.selCfg['min_photonPt']        : return False
            if abs(p.eta)> self.gen_vjjEvent.selCfg['max_photonEta'] : return False
        else:
             if p.pt < self.gen_vjjEvent.selCfg['min_leptonPt']       : return False
             if abs(p.eta) > self.gen_vjjEvent.selCfg['max_leptonEta']: return False
        return True

    def isGoodGenJet(self,p,vetoObjs):
        if p.pt < self.gen_vjjEvent.selCfg['min_jetPt']        : return False
        if abs(p.eta) > self.gen_vjjEvent.selCfg['max_jetEta'] : return False
        min_dr = min([obj.DeltaR(p) for obj in vetoObjs] or [2*self.gen_vjjEvent.selCfg['min_jetdr2v']])
        if min_dr < self.gen_vjjEvent.selCfg['min_jetdr2v']    : return False
        return True

    def analyze(self, event):

        """
        process event, return True (go to next module) or False (fail, go to next event)
        in case self.bypassSelFilters is configured as True, it will always accept the event
        """

        isGoodForReco=self.reco_analyze(event)
        self.out.fillBranch('vjj_isGood',isGoodForReco)
        
        isGoodForGen=False
        if self.gen_vjjEvent:
            isGoodForGen=self.gen_analyze(event)
            self.out.fillBranch('genvjj_isGood',isGoodForGen)
        
        return isGoodForGen or isGoodForReco or self.bypassSelFilters



    def gen_analyze(self,event):

        """generator-level specific analysis"""

        if self.isData : return False

        self.gen_vjjEvent.resetOutVars()

        #event weights (for additional weights we divide by the nominal one)
        wgts=[ getattr(event,'Generator_weight',1.0) ]
            
        npswgts=getattr(event,'nPSWeight', 0)
        self.histos['nwgts'].SetBinContent(1,npswgts)
        for i in range( npswgts ):
            wgts.append( wgts[0]*np.divide(event.PSWeight[i],event.PSWeight[0]) )

        nscalewgts=getattr(event, 'nLHEScaleWeight', 0) if hasattr( event , 'nLHEScaleWeight' ) else 0
        self.histos['nwgts'].SetBinContent(2,nscalewgts)
        for i in range( nscalewgts ):
            wgts.append( wgts[0]*np.divide(event.LHEScaleWeight[i],event.LHEScaleWeight[0]) )

        nlherwgwgts=getattr(event, 'nLHEReweightingWeight', 0) if hasattr( event , 'nLHEReweightingWeight' ) else 0
        self.histos['nwgts'].SetBinContent(3,nlherwgwgts)
        for i in range( nlherwgwgts ):
            wgts.append( wgts[0]*np.divide(event.LHEReweightingWeight[i],event.LHEReweightingWeight[0]) )

        npdfwgts=getattr(event,'nLHEPdfWeight',0 ) if hasattr( event , 'nLHEPdfWeight' ) else 0
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
        #fill based on final state

        all_obj  = []
        good_obj = []

        if abs(self.fs) != 22:
            pid = 13 if self.fs == 169 else 11
            all_obj = Collection(event,'GenDressedLepton')
        else:
            pid = 22
            all_obj = Collection(event,'GenPart')

        good_obj = [p for p in all_obj if self.isGoodGenParticle(p,pid)]


        #call boson candidate arbitration

        bosonArbitration = self.BosonSelection(good_obj,self.fs,self.hltCats)
        if bosonArbitration is None:
            return False
        fsCat,arbTrigCats,boson=bosonArbitration

        #add MC information for final states
        if abs(self.fs) == 22:    
            self.out.fillBranch('genvjj_hasPromptPhoton',True if len(good_obj)>0 else False)
        else: 
            self.gen_vjjEvent.fillZextraBranches(good_obj)

        #jet selection
        all_genJets = Collection(event,'GenJet')
        jets = [ j for j in all_genJets if self.isGoodGenJet(j,good_obj)]

        #analyze v+2j event candidate
        isGoodV2J =  self.gen_vjjEvent.isGoodVJJ( boson, jets, arbTrigCats, fsCat ) 
            
        return isGoodV2J



    def reco_analyze(self,event):
       

        """reco-level specific analysis"""
 
        self.vjjEvent.resetOutVars()

        self.histos['cutflow'].Fill(0)

        #start possible event categories by checking the triggers that fired
        trig_cats = self.TriggerSelection(event)

        #boson selection
        all_pho        = Collection(event, "Photon")
        good_phoIdx    = event.vjj_photons 
        if self.fs == -22:  good_phoIdx  = event.vjj_loosePhotons
        if self.fs == -22:  jetsIdx  = event.vjj_looseJets

        all_muo        = Collection(event, "Muon")
        good_muoIdx    = event.vjj_mus

        all_ele        = Collection(event, "Electron")
        good_eleIdx    = event.vjj_eles

        good_obj       = []
        

        if self.fs == 169:
            good_obj  = [all_muo[i] for i in good_muoIdx]       
            if(len(good_obj)>0):
                for i in range(0,len(good_obj)):
                    good_obj[i].pt = good_obj[i].corrected_pt
        elif self.fs == 121:
            good_obj  = [all_ele[i] for i in good_eleIdx]       
        elif abs(self.fs) == 22:
            if len( good_phoIdx) > 0:
                good_obj  = [all_pho[i] for i in [good_phoIdx[0]]]
        
        bosonArbitration = self.BosonSelection(good_obj,self.fs,trig_cats)

        if bosonArbitration is None:
            return False

        #Signal and other CR VJJ's have no overlap

        if self.fs == 169 and (len(good_eleIdx) > 0 or len(good_phoIdx) > 0): return False
        elif self.fs == 121 and (len(good_muoIdx) > 0 or len(good_phoIdx) > 0): return False
        elif self.fs == 22 and (len(good_eleIdx) > 0 or len(good_muoIdx) > 0): return False

        fsCat,arbTrigCats,boson=bosonArbitration

        if fsCat != self.fs: 
            return False

        self.histos['cutflow'].Fill(np.sign(fsCat)*1)

        #jet selection
        all_jets = Collection(event, "Jet")
        jetsIdx  =  event.vjj_jets
        jets     = [all_jets[i] for i in jetsIdx]
        cleanJets= []
        
        #### make the CR similar with the SR
        for j in jets:
            if j.DeltaR(boson) < self.vjjEvent.selCfg['min_jetdr2v']: continue
            cleanJets.append(j)
        ####
         
        #analyze v+2j event candidate
        isGoodV2J =  self.vjjEvent.isGoodVJJ(boson, cleanJets, arbTrigCats, fsCat) 
 
        #add additional variables
        if abs(fsCat) == 22:
            self.vjjEvent.fillPhotonExtraBranches(good_obj[0])
        else:
            self.vjjEvent.fillZextraBranches(good_obj)

        #fill scale factors
        if isGoodV2J:

            self.histos['cutflow'].Fill(np.sign(fsCat)*2)
            if len(trig_cats)>0 : self.histos['cutflow'].Fill(np.sign(fsCat)*3)

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

                SFs={'id':[],'pxseed':[]}
#                print('fs:',self.fs)
#                print('id:',good_obj[0].cutBased)

                for k in SFs:
                    if self.fs ==22:
                       wgt_dict['effWgt']   = getattr( event , "vjj_{0}{1}_effWgt".format( 'photon',k  ) )
                       wgt_dict['effWgtUp'] = getattr( event , "vjj_{0}{1}_effWgtUp".format( 'photon',k  ) )
                       wgt_dict['effWgtDn'] = getattr( event , "vjj_{0}{1}_effWgtDn".format( 'photon',k  ) )
                    elif self.fs==-22:
                         wgt_dict['effWgt']   = getattr( event , "vjj_{0}{1}_effWgt".format(   'loosePhoton',k  ) )
                         wgt_dict['effWgtUp'] = getattr( event , "vjj_{0}{1}_effWgtUp".format( 'loosePhoton',k  ) )
                         wgt_dict['effWgtDn'] = getattr( event , "vjj_{0}{1}_effWgtDn".format( 'loosePhoton',k  ) )
#                wgt_dict['effWgt']   = event.vjj_photon_effWgt
#                wgt_dict['effWgtUp'] = event.vjj_photon_effWgtUp
#                wgt_dict['effWgtDn'] = event.vjj_photon_effWgtDn

            #dilepton efficiency
            if fsCat==121 or fsCat==169:
                wgt_dict['trigWgt']   = 1
                wgt_dict['trigWgtUp'] = 1
                wgt_dict['trigWgtDn'] = 1
                wgt_dict['trigHighPtWgt']  =1
                wgt_dict['trigHighPtWgtUp']=1
                wgt_dict['trigHighPtWgtDn']=1

                SFs={'id':[],'iso':[]} if fsCat==169 else {'id':[],'rec':[]}
                for k in SFs:
                    wgt_dict['effWgt']   = getattr( event , "vjj_{0}{1}_effWgt".format( 'mu' if fsCat == 169 else "ele",k ) )
                    wgt_dict['effWgtUp'] = getattr( event , "vjj_{0}{1}_effWgtUp".format( 'mu' if fsCat == 169 else "ele",k ) )
                    wgt_dict['effWgtDn'] = getattr( event , "vjj_{0}{1}_effWgtDn".format( 'mu' if fsCat == 169 else "ele",k ) )

            #quark gluon discriminator weights (tag jets only) #Removed '_jets' suffix (obsolete?)
            wgt_dict['qglgWgt'] = event.vjj_qglgWgt
            wgt_dict['qglqWgt'] = event.vjj_qglqWgt

            self.vjjEvent.fillWeightBranches(wgt_dict)

        #all done here
        return isGoodV2J

        
# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed
vjjSelector2016data   = lambda myFs = 22: VJJSelector(True , 2016, False, finalState = myFs) 
vjjSelector2016mc     = lambda signal=False, myFs = 22: VJJSelector(False , 2016 , bypassSelFilters=signal, finalState = myFs) 
vjjSelector2017data   = lambda myFs = 22: VJJSelector(True , 2017, finalState = myFs) 
vjjSelector2017mc     = lambda signal=False, myFs = 22: VJJSelector(False , 2017, bypassSelFilters=signal, finalState = myFs) 
vjjSelector2018data   = lambda myFs = 22: VJJSelector(True , 2018, finalState = myFs) 
vjjSelector2018mc     = lambda signal=False, myFs = 22: VJJSelector(False , 2018 , bypassSelFilters=signal, finalState = myFs) 
