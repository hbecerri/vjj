import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
import os
import copy
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection 
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from UserCode.VJJSkimmer.samples.Sample import Sample
from UserCode.VJJSkimmer.samples.campaigns.Manager import Manager as CampaignManager

class VJJSkimmer(Module):

    """Implements a generic V+2j selection for VBF X studies"""

    def __init__(self, sample , campaign):

        self.sample = Sample(sample)
        self.campaign = CampaignManager( campaign )
        
        self.isData           = self.sample.isData()
        self.era              = self.sample.year()

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
        
    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):

        outputFile.cd()
        self.BDTReader = ROOT.BDTReader(True,True,True)
        self.BDTReader.Init(inputTree._ttreereader.GetTree())
        
        #define output tree
        self.out = wrappedOutputTree
        self.out.branch('vjj_isHighAPt','O')
        self.out.branch('vjj_isLowAPt','O')
        self.out.branch('vjj_isHighZmm','O')
        self.out.branch('vjj_isLowZmm','O')
        self.out.branch('vjj_isHighZee','O')
        self.out.branch('vjj_isLowZee','O')
        for mva_name in self.BDTReader.methodNames:
            self.out.branch('vjj_mva_{0}'.format( mva_name ) , 'F' )
        self.out.branch('vjj_xsection' , 'F' )
        self.out.branch('vjj_nTotal' , 'F' )
        self.out.branch('vjj_lumiWeight' , 'F' )
        self.out.branch('vjj_weight' , 'F' )

        if not self.isData:
            self.out.branch('vjj_photonIsMatched' , 'B' )
            self.out.branch('vjj_maxGenPhotonPt' , 'F' )
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):

        """
        process event, return True (go to next module) or False (fail, go to next event)
        """
        for b in ['LowAPt' , 'HighAPt' , 'HighZmm','LowZmm' ,'HighZee' ,'LowZee']:
            self.out.fillBranch('vjj_is{0}'.format( b ) , False)

        category = ""
        if event.vjj_isGood and event.vjj_jj_m>200 and event.vjj_lead_pt>50 and  event.vjj_sublead_pt>50:
            if event.vjj_fs==22:
                high_pt_lowerCut = 175 if self.era == 2016 else 200
                if event.vjj_trig==2 and event.vjj_v_pt>high_pt_lowerCut:
                    category = 'HighAPt'
                elif event.vjj_trig!=2 and event.vjj_v_pt>75 and abs(event.vjj_v_eta)<1.442:
                    category = 'LowAPt'
                elif event.vjj_fs == 121 and event.vjj_trig==3 and event.vjj_v_pt>high_pt_lowerCut:
                    category = 'HighZee'
                elif event.vjj_fs == 121 and event.vjj_trig==3 and event.vjj_v_pt>75 and abs(event.vjj_v_eta)<1.442:
                    category = 'LowZee'
                elif event.vjj_fs == 169 and event.vjj_trig==3 and event.vjj_v_pt>high_pt_lowerCut:
                    category = 'HighZmm'
                elif event.vjj_fs == 121 and event.vjj_trig==3 and event.vjj_v_pt>75 and abs(event.vjj_v_eta)<1.442:
                    category = 'LowZmm'
                
        if category == "":
            return False

        self.out.fillBranch('vjj_is{0}'.format( category ) , True)
        self.out.fillBranch('vjj_xsection',self.xSection)
        self.out.fillBranch('vjj_nTotal' , self.nTotal)
        self.out.fillBranch('vjj_lumiWeight' , self.lumiWeights[category if category in ['LowAPt' , 'HighAPt'] else category[1:] ])

        self.BDTReader.Process( event._entry )
        for i in range(self.BDTReader.methodNames.size()):
            mva_name = self.BDTReader.methodNames[i]
            self.out.fillBranch('vjj_mva_{0}'.format( mva_name ) , self.BDTReader.mvaValues[i] )

        if self.isData:
            self.out.fillBranch('vjj_weight' , 1 )
        else:
            prefirew =  event.PrefireWeight if self.era != 2018 else 1
            self.out.fillBranch('vjj_weight' , event.Generator_weight*event.puWeight*prefirew )
            
            genParts = Collection(event , "GenPart")
            vjjPhotons = Collection(event , "vjj_photons" , 'vjj_nphotons')
            if event.vjj_nphotons > 0:
                photons = Collection(event, "Photon" )
                selectedPhotonIndex = ord(event.vjj_photons[0])
                photon_genPartIdx = photons[selectedPhotonIndex].genPartIdx
                if photon_genPartIdx > -1:
                    self.out.fillBranch( 'vjj_photonIsMatched' , genParts[photon_genPartIdx].statusFlags & 1 )
                else: self.out.fillBranch( 'vjj_photonIsMatched' , -10 )
            else: self.out.fillBranch( 'vjj_photonIsMatched' , -20 )

            maxGenPhotonPt = -1
            for genPart in genParts:
                if genPart.pdgId == 22:
                    if genPart.statusFlags & 1 :
                        if genPart.pt > maxGenPhotonPt :
                            maxGenPhotonPt = genPart.pt
            self.out.fillBranch( 'vjj_maxGenPhotonPt' , maxGenPhotonPt )
        return True
