import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
import os
import copy
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from UserCode.VJJSkimmer.samples.Sample import Sample
from UserCode.VJJSkimmer.samples.campaigns.Manager import Manager as CampaignManager
from UserCode.VJJSkimmer.postprocessing.modules.VJJEvent import _defaultVjjSkimCfg


class VJJSkimmer(Module):

    """Implements a generic V+2j selection for VBF X studies"""

    def __init__(self, sample , campaign, finalState = 22, cfg=_defaultVjjSkimCfg):

        self.sample = Sample(sample)
        self.campaign = campaign

        self.isData           = self.sample.isData()
        self.era              = self.sample.year()

        self.allWeights       = self.campaign.get_allWeightIndices(sample)
        self.nWeights         = len(self.allWeights)
        self.lumiWeights      = self.campaign.get_lumi_weight(sample)
#        print("&&&&&&&&&&&&")
#        print(self.lumiWeights)
#        print("&&&&&&&&&&&&")
        self.xSection         = self.campaign.get_xsection(sample)
	self.selCfg = copy.deepCopy(cfg)
	self.fs = finalState
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
        #for mvavar_name in self.BDTReader.outputVarNames: #FIXME
        #    self.out.branch('vjj_{0}'.format(mvavar_name),'F')

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



    def Selection(self, event):
        '''
        Perform high-level event selection and final categorization
        '''

        #-- Check if event enters any category
        category = ""

        HighVPt_minVpt = self.selCfg['min_photonPt_HVPt16'] if self.era == 2016 else self.selCfg['min_photonPt_HVPt']

	basicSelection  = (event.vjj_isGood and event.vjj_jj_m> self.selCfg['min_mjj'] and event.vjj_lead_pt> self.selCfg['min_leadTagJetPt'] and  event.vjj_sublead_pt> self.selCfg['min_subleadTagJetPt'])
	lowVPtSelection = (event.vjj_v_pt> self.selCfg['min_photonPt_LVPt'] and abs(event.vjj_v_eta)<self.selCfg['max_photonEta_LVPt'] and abs(event.vjj_jj_deta) > self.selCfg['min_detajj_LVPt'] and event.vjj_jj_m > self.selCfg['min_mjj_LVPt'])

        #-- Assign events to SR/CR categories

	if basicSelection:
            if abs(self.fs) == 22 and abs(event.vjj_fs) == 22:
                if lowVPtSelection and event.vjj_trig != self.selCfg['HLT_photon']: category = "LowVPt"
                if category == "" and event.vjj_v_pt > HighVPt_minVpt and event.vjj_trig == self.selCfg['HLT_photon']: category = "HighVPt"
            else:
                pfx = 'mm' if self.fs == 169 else 'ee'
                if event.vjj_trig == self.selCfg['HLT_lepton'] and abs(self.fs) == abs(event.vjj_fs):
                    if lowVPtSelection: category = "LowVPt{0}".format(pfx)
                    if category == "" and event.vjj_v_pt> HighVPt_minVpt: category = "HighVPt{0}".format(pfx)
    
       

        #-- Trigger logic #Same data events may be found in multiple datasets --> Make sure that an event is only considered once
        # ee region <-> only DoubleEG, EGamma (2018)
        # mm region <-> only DoubleMuon
        # SR <-> only SinglePhoton, EGamma (2018)
        if self.isData:
            if 'ee' in category:
                if not any([substring in self.samplename for substring in ['DoubleEG','EGamma', 'SingleElectron']]): return ""
            elif 'mm' in category:
		if not any([substring in self.samplename for substring in ['DoubleMuon','SingleMuon']]): return ""
            else:
                if not any([substring in self.samplename for substring in ['SinglePhoton','EGamma']]): return ""
                
        return category


    def analyze(self, event):

        """
        process event, return True (go to next module) or False (fail, go to next event)
        """
        for b in ['LowVPt' , 'HighVPt' , 'HighVPtmm','LowVPtmm' ,'HighVPtee' ,'LowVPtee']:
            self.out.fillBranch('vjj_is{0}'.format( b ) , False)

        category = selection(event)


        if category == "":
            return False

        self.out.fillBranch('vjj_is{0}'.format( category ) , True)
        self.BDTReader.Process( event._entry )
        for i in range(self.BDTReader.outputNames.size()):
            mva_name = self.BDTReader.outputNames[i]
            self.out.fillBranch('vjj_mva_{0}'.format( mva_name ) , self.BDTReader.mvaValues[i] )



        if self.isData:
            pass
        else:
            print("HOLAAAAA")
            self.out.fillBranch('vjj_xsection',self.xSection)
            lumiweights = []
            for windex in range(self.nWeights):
                wid = self.allWeights[windex][1]
                print(event.genvjj_wgt[ wid ])
		print(self.lumiWeights[category][windex])
#aqui estaba el error
                lumiweights.append( event.genvjj_wgt[ wid ]*self.lumiWeights[category][windex] )
            self.out.fillBranch('vjj_lumiWeights' , lumiweights )
##aqui termina el error
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

            prefirew = event.L1PreFiringWeight_Nom if self.era != 2018 else 1

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

        
