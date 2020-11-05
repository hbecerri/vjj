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
        self.campaign = campaign
        
        self.isData           = self.sample.isData()
        self.era              = self.sample.year()

        self.allWeights       = self.campaign.get_allWeightIndices(sample)        
        self.nWeights         = len(self.allWeights)
        self.lumiWeights      = self.campaign.get_lumi_weight(sample)
        self.xSection         = self.campaign.get_xsection(sample)
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
        self.hTotals = ROOT.TH1D("TotalNumbers" , "" , self.nWeights , 0 , self.nWeights )
        nTotals          = self.campaign.get_allNTotals(self.sample.ds)
        for wid in range(self.nWeights):
            self.hTotals.SetBinContent( wid + 1 , nTotals[wid] )
            self.hTotals.GetXaxis().SetBinLabel( wid + 1 , self.allWeights[wid][0] )

        self.BDTReader = ROOT.BDTReader(True,True,True)
        self.BDTReader.Init(inputTree._ttreereader.GetTree())
        
        #define output tree
        self.out = wrappedOutputTree
        self.out.branch('vjj_isHighVPt','O')
        self.out.branch('vjj_isLowVPt','O')
        self.out.branch('vjj_isHighVPtmm','O')
        self.out.branch('vjj_isLowVPtmm','O')
        self.out.branch('vjj_isHighVPtee','O')
        self.out.branch('vjj_isLowVPtee','O')
        for mva_name in self.BDTReader.outputNames:
            self.out.branch('vjj_mva_{0}'.format( mva_name ) , 'F' )

        if not self.isData:
            self.out.branch('vjj_photonIsMatched' , 'B' )
            self.out.branch('vjj_maxGenPhotonPt' , 'F' )

            self.out.branch('vjj_xsection' , 'F' )
            self.out.branch('vjj_lumiWeights' , 'F' , lenVar='vjj_nlumiWeights' )
            self.out.branch('vjj_weight' , 'F' )
        
            self.out.branch('vjj_sfweight_up' , 'F')
            self.out.branch('vjj_sfweight_down' , 'F')

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        outputFile.cd()
        self.hTotals.SetDirectory(outputFile)
        self.hTotals.Sumw2()
        self.hTotals.Write()
        pass

    def analyze(self, event):

        """
        process event, return True (go to next module) or False (fail, go to next event)
        """
        for b in ['LowVPt' , 'HighVPt' , 'HighVPtmm','LowVPtmm' ,'HighVPtee' ,'LowVPtee']:
            self.out.fillBranch('vjj_is{0}'.format( b ) , False)

        category = ""
        high_pt_lowerCut = 200 #175 if self.era == 2016 else 200
        if event.vjj_isGood and event.vjj_jj_m>200 and event.vjj_lead_pt>50 and  event.vjj_sublead_pt>50 and event.vjj_fs in [22,121,169]:
            isLow = False
            isHigh = False
            if event.vjj_v_pt>75 and abs(event.vjj_v_eta)<1.442 and abs(event.vjj_jj_deta) > 3.0 and event.vjj_jj_m > 500:
                if event.vjj_fs==22:
                    if event.vjj_trig != 2:
                        isLow = True
                elif event.vjj_trig == 3:
                    isLow = True
            if not isLow and event.vjj_v_pt>high_pt_lowerCut:
                if event.vjj_fs==22:
                    if event.vjj_trig == 2:
                        isHigh = True
                elif event.vjj_trig == 3:
                    isHigh = True
                    
            
            if isHigh:
                category = "HighVPt"
            elif isLow:
                category = "LowVPt"

            if category != '':
                if event.vjj_fs==22:
                    pass
                elif event.vjj_fs == 121:
                    category += 'ee'
                elif event.vjj_fs == 169:
                    category += 'mm'

                
        if category == "":
            return False

        self.out.fillBranch('vjj_is{0}'.format( category ) , True)
        self.BDTReader.Process( event._entry )
        for i in range(self.BDTReader.outputNames.size()):
            mva_name = self.BDTReader.outputNames[i]
            self.out.fillBranch('vjj_mva_{0}'.format( mva_name ) , self.BDTReader.mvaValues[i] )



        if self.isData:
            #self.out.fillBranch('vjj_weight' , 1 )
            pass
        else:
            self.out.fillBranch('vjj_xsection',self.xSection)
            lumiweights = []
            for windex in range(self.nWeights):
                wid = self.allWeights[windex][1]
                lumiweights.append( event.genvjj_wgt[ wid ]*self.lumiWeights[category][windex] )
            self.out.fillBranch('vjj_lumiWeights' , lumiweights )

            wsf = event.vjj_photon_effWgt
            wsf_up = event.vjj_photon_effWgtUp
            wsf_down = event.vjj_photon_effWgtDn
            if 'mm' in category:
                wsf = event.vjj_mu_effWgt
                wsf_up = event.vjj_mu_effWgtUp
                wsf_down = event.vjj_mu_effWgtDn
            elif 'ee' in category:
                wsf = event.vjj_ele_effWgt
                wsf_up = event.vjj_ele_effWgtUp
                wsf_down = event.vjj_ele_effWgtDn
                

            prefirew =  event.PrefireWeight if self.era != 2018 else 1
            self.out.fillBranch('vjj_weight' , wsf*event.puWeight*prefirew )
            self.out.fillBranch('vjj_sfweight_down' , wsf_down/wsf )
            self.out.fillBranch('vjj_sfweight_up' , wsf_up/wsf )

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
