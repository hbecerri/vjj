import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
import os
import copy
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection 
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from UserCode.VJJSkimmer.samples.Sample import Sample
from UserCode.VJJSkimmer.samples.campaign.Manager import Manager as CampaignManager

class VJJSkimmer(Module):

    """Implements a generic V+2j selection for VBF X studies"""

    def __init__(self, sample , campaign):

        self.sample = Sample(sample)
        self.campaign = CampaignManager( campaign )
        
        self.isData           = self.Sample.isData()
        self.era              = self.Sample.year()

        self.xSection         = self.campaign.get_xsection(sample)
        self.nTotal           = self.campaign.get_nTotal(sample)
        self.lumiWeights      = self.campaign.get_lumi_weight(sample)
        #Try to load module via python dictionaries
        try:
            ROOT.gSystem.Load("libUserCodeVJJPlotter")
            dummy = ROOT.BDTReader()
            #Load it via ROOT ACLIC. NB: this creates the object file in the CMSSW directory,
            #causing problems if many jobs are working from the same CMSSW directory
        except Exception as e:
            print "Could not load module via python, trying via ROOT", e
            if "/BDTReader_cc.so" not in ROOT.gSystem.GetLibraries():
                print "Load C++ Worker"
                if 'CMSSW_BASE' in os.environ:
                    ROOT.gROOT.ProcessLine(".L %s/src/UserCode/VJJPlotter/src/BDTReader.cc++" % os.environ['CMSSW_BASE'])
                else:
                    ROOT.gROOT.ProcessLine(".L ../../VJJPlotter/src/BDTReader.cc++")
            dummy = ROOT.BDTReader()
        self.BDTReader()
    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):

        outputFile.cd()
        self.BDTReader.Init(inputTree)
        
        #define output tree
        self.out = wrappedOutputTree
        self.out.branch('vjj_isHighAPt','O')
        self.out.branch('vjj_isLowAPt','O')
        self.out.branch('vjj_isZmm','O')
        self.out.branch('vjj_isZee','O')
        for mva_name in self.BDTReader.methodNames:
            self.out.branch('vjj_mva_{0}'.format( mva_name ) , 'F' )
        self.out.branch('vjj_xsection' , 'F' )
        self.out.branch('vjj_nTotal' , 'F' )
        self.out.branch('vjj_lumiWeight' , 'F' )
        self.out.branch('vjj_weight' , 'F' )

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):

        """
        process event, return True (go to next module) or False (fail, go to next event)
        """
        for b in ['LowAPt' , 'HighAPt' , 'Zmm' , 'Zee']:
            self.out.fillBranch('vjj_is{0}'.format( b ) , False)

        category = ""
        if event.vjj_isGood and event.vjj_jj_m>200 and event.vjj_lead_pt>50 and event.vjj_sublead_pt>50:
            if event.vjj_fs==22:
                high_pt_lowerCut = 175 if self.era == 2016 else 200
                if event.vjj_trig==2 and event.vjj_v_pt>high_pt_lowerCut:
                    category = 'HighAPt'
                else if event.vjj_trig!=2 and event.vjj_v_pt>75:
                    category = 'LowAPt'
            elif event.vjj_fs == 121 and event.vjj_trig==3:
                category = 'Zee'
            elif event.vjj_fs == 169 and event.vjj_trig==3:
                category = 'Zmm'

        if category == "":
            return False

        self.out.fillBranch('vjj_is{0}'.format( category ) , True)
        self.out.fillBranch('vjj_xsection',self.xSection)
        self.out.fillBranch('vjj_nTotal' , self.nTotal)
        self.out.fillBranch('vjj_lumiWeight' , self.lumiWeights[category])

        self.BDTReader.Process( event._entry )
        for i,mva_name in self.BDTReader.methodNames.items():
            self.out.fillBranch('vjj_mva_{0}'.format( mva_name ) , self.BDTReader.mvaValues[i] )

        if self.isData:
            self.out.fillBranch('vjj_weight' , 1 )
        else:
            prefirew =  event.PrefireWeight if self.era != 2018 else 1
            self.out.fillBranch('vjj_weight' , event.vjj_mu_effWgt*event.Generator_weight*event.puWeight*prefirew )

