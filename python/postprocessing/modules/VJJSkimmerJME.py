'''
Adapted from VJJSkimmer.py code by Nicolas TONON (DESY)

Main functionalities:
- Compute high-level observables and store them in output GetTree
- Skim events based on final categories (-> produce lightweight ntuples)
- Handle JEC/JER/MET variations separately (must be chained to the nanoAOD jetmetHelperRun2 module -- see: https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/modules/jme/jetmetHelperRun2.py)
'''

# //--------------------------------------------
# //--------------------------------------------

import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
import os
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.output import *
from PhysicsTools.NanoAODTools.postprocessing.framework.branchselection import BranchSelection
from UserCode.VJJSkimmer.samples.Sample import Sample
from UserCode.VJJSkimmer.samples.campaigns.Manager import Manager as CampaignManager
from UserCode.VJJSkimmer.postprocessing.helpers.ColoredPrintout import *
from UserCode.VJJSkimmer.postprocessing.helpers.Helper import *
from ReadComputeObservables_VJJSkimmerJME import *
from BDTReader import *

# //--------------------------------------------
# //--------------------------------------------

class VJJSkimmerJME(Module):

    def __init__(self, sample, campaign, JMEvars=[], includeTotalJER=False):

        self.sample = Sample(sample)
        self.campaign = campaign

        self.isData           = self.sample.isData()
        self.era              = self.sample.year()

        self.JMEvars = [] if self.isData else JMEvars #[] <-> nominal only (default); else <-> in addition to nominal, also process corresponding JEC/JER/MET variations #Ignore variations for data
        self.includeTotalJER = includeTotalJER ##True <-> also process total Down/Up JER variations; False <-> do not consider JER variations

        self.allWeights       = self.campaign.get_allWeightIndices(sample)
        self.nWeights         = len(self.allWeights)
        self.lumiWeights      = self.campaign.get_lumi_weight(sample)
        self.xSection         = self.campaign.get_xsection(sample)

        '''
        #-- Try to load BDTReader class (implemented in VJJPlotter code) via python dictionaries
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
        '''

        #Try to load EventShapeVariables class via python dictionaries
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

        return


    def beginJob(self):
        pass


    def endJob(self):
        pass


# //--------------------------------------------
# //--------------------------------------------
########  ########  ######   #### ##    ## ######## #### ##       ########
##     ## ##       ##    ##   ##  ###   ## ##        ##  ##       ##
##     ## ##       ##         ##  ####  ## ##        ##  ##       ##
########  ######   ##   ####  ##  ## ## ## ######    ##  ##       ######
##     ## ##       ##    ##   ##  ##  #### ##        ##  ##       ##
##     ## ##       ##    ##   ##  ##   ### ##        ##  ##       ##
########  ########  ######   #### ##    ## ##       #### ######## ########
# //--------------------------------------------
# //--------------------------------------------

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        '''
        Init commands executed when opening file
        '''


  ####  ###### ##### #    # #####
 #      #        #   #    # #    #
  ####  #####    #   #    # #    #
      # #        #   #    # #####
 #    # #        #   #    # #
  ####  ######   #    ####  #

        #-- Add custom histo
        outputFile.cd()
        self.hTotals = ROOT.TH1D("TotalNumbers" , "" , self.nWeights , 0 , self.nWeights )
        nTotals          = self.campaign.get_allNTotals(self.sample.ds)
        for wid in range(self.nWeights):
            self.hTotals.SetBinContent( wid + 1 , nTotals[wid] )
            self.hTotals.GetXaxis().SetBinLabel( wid + 1 , self.allWeights[wid][0] )

        #-- Init BDTReader
        self.BDTReader = BDTReader()
        self.BDTReader.Setup()
        # self.BDTReader = ROOT.BDTReader(False, True, False) #Only consider 'AN2019' BDTs
        # self.BDTReader.Init(inputTree)

        #-- Create 'ReadComputeObservables' object (used to create/fill branches and compute relevant observables)
        self.obsMaker = ReadComputeObservables(self.sample, self.isData, self.era, self.allWeights, self.nWeights, self.lumiWeights, self.xSection, self.BDTReader.outputNames)


 #####  #####    ##   #    #  ####  #    # ######  ####
 #    # #    #  #  #  ##   # #    # #    # #      #
 #####  #    # #    # # #  # #      ###### #####   ####
 #    # #####  ###### #  # # #      #    # #           #
 #    # #   #  #    # #   ## #    # #    # #      #    #
 #####  #    # #    # #    #  ####  #    # ######  ####

        self.inputTree = inputTree #Input tree

        #-- Nominal output tree #Fill/Write operations handled internally by NanoAODTools framework
        self.nomOutput = wrappedOutputTree
        # self.nomOutput.tree().Print() #Print all branches

        #-- Create new branches for nominal output tree
        self.obsMaker.CreateAllBranches(self.nomOutput, isDefaultTree=True)

        #-- Keep/drop file to be used for JME trees only
        keep_drop_file_JMEvars = '{0}/python/UserCode/VJJSkimmer/postprocessing/etc/keep_and_drop_VJJSkimmerJME.txt'.format(os.getenv('CMSSW_BASE', '.'))
        self.branchsel = BranchSelection(keep_drop_file_JMEvars) #Define branch selection from file

        #-- Create new 'FullOutput' (and corresponding output TTree) objects -- 1 per JME variation <-> will be used to store events associated with each variation independently
        self.outputs_JMEvars = [] #FullOutput (see class: https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/framework/output.py)
        self.trees_JMEvars = [] #Corresponding TTree objects
        for ivar, JMEvar in enumerate(self.JMEvars):
            self.outputs_JMEvars.append(FullOutput(inputFile, inputTree, outputFile, outputbranchSelection=self.branchsel, fullClone=False, maxEntries=None))
            self.trees_JMEvars.append(self.outputs_JMEvars[ivar].tree())
            self.obsMaker.CreateAllBranches(self.outputs_JMEvars[ivar], isDefaultTree=False) #Create branches for variation output trees

        return


# //--------------------------------------------
# //--------------------------------------------
######## ##    ## ########  ######## #### ##       ########
##       ###   ## ##     ## ##        ##  ##       ##
##       ####  ## ##     ## ##        ##  ##       ##
######   ## ## ## ##     ## ######    ##  ##       ######
##       ##  #### ##     ## ##        ##  ##       ##
##       ##   ### ##     ## ##        ##  ##       ##
######## ##    ## ########  ##       #### ######## ########
# //--------------------------------------------
# //--------------------------------------------

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        '''
        Final commands executed when closing file --> Write to outfile
        '''

        outputFile.cd()

        #-- Write custom histogram
        self.hTotals.SetDirectory(outputFile)
        self.hTotals.Sumw2()
        self.hTotals.Write()

        #-- Manually write variation TTrees
        self.finaltrees_JMEvars = [] #Trick: as done in FullOutput::write(), must CopyTree to make the branch selection effective
        for ivar, JMEvar in enumerate(self.JMEvars):
            self.branchsel.selectBranches(self.trees_JMEvars[ivar]) #SetBranchStatus from keep_drop file
            copytree = self.trees_JMEvars[ivar].CopyTree('1', "", ROOT.TVirtualTreePlayer.kMaxEntries, 0) #Trick to keep only relevant branch as in nanoAOD
            self.finaltrees_JMEvars.append(copytree)

            treename_tmp = "Events_{}".format(JMEvar) #Unique output name
            print(colors.fg.orange + '... Writing output Tree: {} ...'.format(treename_tmp) + colors.reset + ' ({} entries)'.format(self.finaltrees_JMEvars[ivar].GetEntries()))
            self.finaltrees_JMEvars[ivar].Write(treename_tmp)

        return


# //--------------------------------------------
# //--------------------------------------------
   ###    ##    ##    ###    ##       ##    ## ######## ########
  ## ##   ###   ##   ## ##   ##        ##  ##       ##  ##
 ##   ##  ####  ##  ##   ##  ##         ####       ##   ##
##     ## ## ## ## ##     ## ##          ##       ##    ######
######### ##  #### ######### ##          ##      ##     ##
##     ## ##   ### ##     ## ##          ##     ##      ##
##     ## ##    ## ##     ## ########    ##    ######## ########
# //--------------------------------------------
# //--------------------------------------------

    def analyze(self, event):

        """
        Process each event --> return True (go to next module) or False (fail, go to next event)
        """

        #print('-- ENTRY: ' + str(event._entry) + ' // EVENT: ' + str(event.event))
        # if event._entry != 110: return False #Debug specific entry

        #-- Perform nominal event selection #Based on event variables computed in VJJSelector step
        category_nominal = self.Selection(event)

        #-- Need to redefine boson p4 for computations
        v = ROOT.TLorentzVector(); v.SetPtEtaPhiM(event.vjj_v_pt, event.vjj_v_eta, event.vjj_v_phi, event.vjj_v_m)

        #-- If nominal event is selected, recompute some necessary variables
        if category_nominal != "":

            #Reselect nominal tagged jets to compute global event observables
            #NB: these are already present in the input ntuples, but values appear to be bugged --> recompute here
            all_jets = Collection(event, "Jet")
            goodJets = [all_jets[i] for i in Convert_Chars_toIntegers(event.vjj_jets)] #Trick, cf. helper function comment
            hasGoodTagJets, tagJets, extraJets = self.obsMaker.SelectTaggedJets(v, goodJets)
            if hasGoodTagJets:
                self.obsMaker.FillEventShapeObservables(self.nomOutput, v, tagJets)

            #Compute MVA variables
            self.obsMaker.FillMVAObservables(self.nomOutput, event, self.BDTReader)


        #-- Loop on JEC variations
        for ivar, JMEvar in enumerate(self.JMEvars):

            allJets_JMEvar = Get_Updated_JetCollection_JMEvar(event, JMEvar)
            # allJets = Collection(event, "Jet") #Full jet collection (pt-sorted)
            # print('BEFORE: ', allJets[0].pt)
            # print('AFTER: ', allJets_JMEvar[0].pt)

            #-- Retrieve the good jet indices corresponding to the current variation (defined by JetSelector)
            jetsIdx_JMEvar = eval('event.vjj_jets_{}'.format(JMEvar))

            #-- Get list of selected jets (for current JME variation)
            goodJets_JMEvar = [allJets_JMEvar[i] for i in jetsIdx_JMEvar] #Define list of good jets

            #-- Debug printouts to compare nominal/JME
            # self.Debug_Printouts_JMEvar(event, JMEvar, allJets_JMEvar, Convert_Chars_toIntegers(event.vjj_jets), jetsIdx_JMEvar)

            hasGoodTagJets, tagJets, extraJets = self.obsMaker.SelectTaggedJets(v, goodJets_JMEvar)
            if hasGoodTagJets == False: continue

            #-- Recompute all relevant variables for current JME variation #Reject event if <2 tagged jets found
            if self.obsMaker.FillJMEObservables(self.outputs_JMEvars[ivar], v, tagJets, extraJets) == False: continue

            self.obsMaker.FillEventShapeObservables(self.outputs_JMEvars[ivar], v, tagJets)

            #-- Perform event selection for JME variation #Based on event variables computed above
            category_JMEvar = self.Selection(event)
            if category_JMEvar == "":
                continue
                #print('FAIL ', JMEvar)
            #print('PASS ', JMEvar)

            self.obsMaker.FillCategory(self.outputs_JMEvars[ivar], category_JMEvar) #Fill category flag branch

            #-- Compute MVA variables
            self.obsMaker.FillMVAObservables(self.outputs_JMEvars[ivar], event, self.BDTReader)

            #-- Manually fill the JME tree
            self.outputs_JMEvars[ivar].fill()

        #-- Retain/reject event based on nominal case (must pass to next functions to fill nominal tree) #NB: JME trees were already filled manually above
        if category_nominal == "": return False #Reject event (for nominal case)

        #-- If event is selected, fill categ/weight/MVA variables
        self.obsMaker.FillCategory(self.nomOutput, category_nominal)
        self.obsMaker.FillWeights(self.nomOutput, event, category_nominal)

        return True #Select event, will pass to next module / write entry to output


# //--------------------------------------------
# //--------------------------------------------
 ######  ######## ##       ########  ######  ######## ####  #######  ##    ##
##    ## ##       ##       ##       ##    ##    ##     ##  ##     ## ###   ##
##       ##       ##       ##       ##          ##     ##  ##     ## ####  ##
 ######  ######   ##       ######   ##          ##     ##  ##     ## ## ## ##
      ## ##       ##       ##       ##          ##     ##  ##     ## ##  ####
##    ## ##       ##       ##       ##    ##    ##     ##  ##     ## ##   ###
 ######  ######## ######## ########  ######     ##    ####  #######  ##    ##
# //--------------------------------------------
# //--------------------------------------------

    def Selection(self, event):
        '''
        Perform high-level event selection and final categorization
        '''

        #-- Check if event enters any category
        category = ""
        isLow = False
        isHigh = False
        high_pt_lowerCut = 175 if self.era == 2016 else 200 #FIXME check
        min_vjj_jj_m = 200; min_v_pt = 75; vjj_lead_ptCut = 50; vjj_sublead_ptCut = 50
        vjj_v_etaCut = 1.442; vjj_jj_detaCut = 3.0

        #-- Assign events to SR/CR categories
        if event.vjj_isGood and event.vjj_jj_m > min_vjj_jj_m and event.vjj_lead_pt > vjj_lead_ptCut and event.vjj_sublead_pt > vjj_sublead_ptCut and event.vjj_fs in [22,121,169]:

            lowPtCuts = (event.vjj_v_pt > min_v_pt and abs(event.vjj_v_eta) < vjj_v_etaCut and abs(event.vjj_jj_deta) > vjj_jj_detaCut and event.vjj_jj_m > 500)

            #LowVPt
            if lowPtCuts:
                if event.vjj_fs == 22:
                    if event.vjj_trig != 2: isLow = True
                elif event.vjj_trig == 3: isLow = True

            #HighVPt
            if event.vjj_v_pt>high_pt_lowerCut:
                if event.vjj_fs == 22:
                    if (lowPtCuts == False and event.vjj_trig == 3) or event.vjj_trig == 2: isHigh = True
                elif lowPtCuts == False and event.vjj_trig == 3: isHigh = True

            #Set category name
            if isHigh: category = "HighVPt"
            elif isLow: category = "LowVPt"

            #Update category name
            if category != '':
                if event.vjj_fs == 22: pass 
                elif event.vjj_fs == 121: category += 'ee'
                elif event.vjj_fs == 169: category += 'mm'

        return category


# //--------------------------------------------
# //--------------------------------------------
########  ######## ########  ##     ##  ######
##     ## ##       ##     ## ##     ## ##    ##
##     ## ##       ##     ## ##     ## ##
##     ## ######   ########  ##     ## ##   ####
##     ## ##       ##     ## ##     ## ##    ##
##     ## ##       ##     ## ##     ## ##    ##
########  ######## ########   #######   ######
# //--------------------------------------------
# //--------------------------------------------

#-- DEBUGGING TIPS:
#To printout line number, can use: print(colors.bg.lightgrey + '-- Line ' + str(lineno()) + colors.reset)
#To printout script name, can use: print(__file__)

    def Debug_Printouts_JMEvar(self, event, JMEvar, allJets_JMEvar, jetsIdxNom, jetsIdxJMEvar):
        '''
        Printout lines in terminal for debugging (nom/JEC comparisons, etc.)
        '''

        print('') #Empty line
        allJetsNom = Collection(event, "Jet") #Get original jet collection

        print(colors.fg.lightred + '\n== Debugging entry ' + str(event._entry) + ' ==' + colors.reset)
        print(colors.fg.lightred + '-- NOMINAL:' + colors.reset)
        print('Jets pt: ', [j.pt for j in allJetsNom])
        print('Jets eta: ', [j.eta for j in allJetsNom])
        print('Good jet idx: ', jetsIdxNom)

        print(colors.fg.lightred + '-- JME variation {}:'.format(JMEvar) + colors.reset)
        print('Jets pt: ', [j.pt for j in allJets_JMEvar])
        print('Jets eta: ', [j.eta for j in allJets_JMEvar])
        print('Good jet idx: ', jetsIdxJMEvar)

        #-- Other printouts
        # print('JEC', event.Jet_corr_JEC)
        # print('Jet_pt_jesTotalUp', event.Jet_pt_jesTotalUp)
        # print('Jet_mass_nom', event.Jet_mass_nom)
        # print('Jet_mass_jesTotalUp', event.Jet_mass_jesTotalUp)
        # print('Jet_pt_jerUp', event.Jet_pt_jerUp)

        print('') #Empty line
        return
