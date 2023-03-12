import ROOT
import copy
from VJJEvent import _defaultVjjCfg
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from UserCode.VJJSkimmer.postprocessing.helpers.Helper import *
from BDTReader import *

# //--------------------------------------------
# //--------------------------------------------

class ReadComputeObservables:
    '''
    Create/fill relevant branches, and recompute all jet-related observables
    '''


 ######  ######## ######## ##     ## ########
##    ## ##          ##    ##     ## ##     ##
##       ##          ##    ##     ## ##     ##
 ######  ######      ##    ##     ## ########
      ## ##          ##    ##     ## ##
##    ## ##          ##    ##     ## ##
 ######  ########    ##     #######  ##

    def __init__(self, sample, isData, era,finalState, allWeights, nWeights, lumiWeights, xSection, mva_names=[]):

        self.sample = sample
        self.isData = isData
        self.era = era
        self.allWeights = allWeights
        self.nWeights = nWeights
        self.lumiWeights = lumiWeights
        self.xSection = xSection
        self.fs = finalState

        self.pfix = 'vjj_' #Prefix define in VJJSelector
        self.categories = []
        self.photonExtra = []
        self.mva_names = mva_names
        self.selCfg = copy.deepcopy(_defaultVjjCfg)

        return


# //--------------------------------------------
# //--------------------------------------------
##     ## ######## ##       ########  ######## ########
##     ## ##       ##       ##     ## ##       ##     ##
##     ## ##       ##       ##     ## ##       ##     ##
######### ######   ##       ########  ######   ########
##     ## ##       ##       ##        ##       ##   ##
##     ## ##       ##       ##        ##       ##    ##
##     ## ######## ######## ##        ######## ##     ##
# //--------------------------------------------
# //--------------------------------------------

    def SelectTaggedJets(self, v, jets, printDebug=False):
        '''
        Select 'tagged' (= 2 hardest) jets
        '''

        #-- Clean jets (pt, eta, dR) and sort by decreasing pT
        cleanJets = [j for j in jets if j.DeltaR(v)>self.selCfg['min_jetdr2v'] and abs(j.eta)<self.selCfg['max_jetEta'] and j.pt>self.selCfg['min_jetPt'] ]
        cleanJets.sort(key = lambda x : x.pt, reverse=True)

        #-- Select tagged jets
        tagJets = [j for j in cleanJets if j.pt>self.selCfg['min_tagJetPt']]

        if printDebug:
            print('Nof tagged jets: ', len(tagJets))
            for jet in tagJets: print('- pt: ', jet.pt)

        #-- Event selection criteria
        if len(tagJets) < 2 : return False, None, None
        if tagJets[0].pt<self.selCfg['min_leadTagJetPt'] : return False, None, None

        #-- Extra radiation activity
        extraJets = [j for j in cleanJets if not j in tagJets]

        return True, tagJets, extraJets

# //--------------------------------------------
# //--------------------------------------------
 ######  ########  ########    ###    ######## ########    ########  ########     ###    ##    ##  ######  ##     ## ########  ######
##    ## ##     ## ##         ## ##      ##    ##          ##     ## ##     ##   ## ##   ###   ## ##    ## ##     ## ##       ##    ##
##       ##     ## ##        ##   ##     ##    ##          ##     ## ##     ##  ##   ##  ####  ## ##       ##     ## ##       ##
##       ########  ######   ##     ##    ##    ######      ########  ########  ##     ## ## ## ## ##       ######### ######    ######
##       ##   ##   ##       #########    ##    ##          ##     ## ##   ##   ######### ##  #### ##       ##     ## ##             ##
##    ## ##    ##  ##       ##     ##    ##    ##          ##     ## ##    ##  ##     ## ##   ### ##    ## ##     ## ##       ##    ##
 ######  ##     ## ######## ##     ##    ##    ########    ########  ##     ## ##     ## ##    ##  ######  ##     ## ########  ######
# //--------------------------------------------
# //--------------------------------------------


   ##   #      #
  #  #  #      #
 #    # #      #
 ###### #      #
 #    # #      #
 #    # ###### ######

    def CreateAllBranches(self, out, isDefaultTree=True):
        '''
        Prepare all relevant branches
        '''

        #-- Not needed for nominal (read directly from input tree)
        if not isDefaultTree:
            self.CreateVJJBranches(out)

        #-- Will recompute event shape observables (bugged in nom) and MVA for both nominal & JME variations
        self.CreateEventShapeBranches(out)
        self.CreateMVABranches(out)

        #-- Create/fill these new branches for both nominal & JME variations
        self.CreateCategBranches(out)

        if not self.isData:
            self.CreateGenBranches(out)
            self.CreateWeightBranches(out)

        return


 #     #       #       #
 #     #       #       #
 #     #       #       #
 #     #       #       #
  #   #  #     # #     #
   # #   #     # #     #
    #     #####   #####

    def CreateVJJBranches(self, out):
        '''
        Prepare the 'vjj_x' branches
        NB: for nominal scenario, can directly read these branches from input tree; but must be recomputed for JME variations
        '''

        #NB: could use VJJEvent function directly (but better to control here the list of vars)
        # self.vjjEvent.makeBranches(out, False)
        # self.vjjEvent.resetOutVars()

        #-- Floating point variables
        for v in ['v_ystar',
                  'lead_pt', 'lead_eta', 'lead_phi', 'lead_m', 'lead_qgl', 'lead_dr2v','lead_dphiv','lead_detav',
                  'sublead_pt','sublead_eta','sublead_phi', 'sublead_m', 'sublead_qgl', 'sublead_dr2v','sublead_dphiv','sublead_detav',
                  'j_maxAbsEta','j_minAbsEta',
                  'jj_pt','jj_eta','jj_phi','jj_m','jj_dr2v','jj_scalarht','jj_deta','jj_dphi','jj_sumabseta',
                  'vjj_pt', 'vjj_eta', 'vjj_phi', 'vjj_m', 'vjj_dphi' ,'vjj_deta',
                  'vjj_scalarht', 'centj_pt', 'centj_eta', 'centj_phi', 'centj_m', 'centj_ystar', 'centj_dr2v',
                  'htsoft','centhtsoft']:
            out.branch(self.pfix+v, 'F', limitedPrecision=False)

        #-- Integer variables
        for v in ['nextraj','ncentj', 'lead_flav', 'sublead_flav']:
            out.branch(self.pfix+v, 'I')

        #-- Arrays
        #out.branch(self.pfix+"wgt", "F", lenVar="nwgt" ,  limitedPrecision=False)

        return

 ###### #    # ###### #    # #####     ####  #    #   ##   #####  ######
 #      #    # #      ##   #   #      #      #    #  #  #  #    # #
 #####  #    # #####  # #  #   #       ####  ###### #    # #    # #####
 #      #    # #      #  # #   #           # #    # ###### #####  #
 #       #  #  #      #   ##   #      #    # #    # #    # #      #
 ######   ##   ###### #    #   #       ####  #    # #    # #      ######

    def CreateEventShapeBranches(self, out):
        '''
        Prepare the category flag branches
        '''

        #-- By default, set all category flags to False
        for obs in ['vjj_isotropy','vjj_circularity','vjj_sphericity','vjj_aplanarity','vjj_C','vjj_D']:
            out.branch(self.pfix+obs, 'F', limitedPrecision=False)

        return


  ####    ##   ##### ######  ####
 #    #  #  #    #   #      #    #
 #      #    #   #   #####  #
 #      ######   #   #      #  ###
 #    # #    #   #   #      #    #
  ####  #    #   #   ######  ####

    def CreateCategBranches(self, out):
        '''
        Prepare the category flag branches
        '''

        #-- By default, set all category flags to False
        for cat in ['LowVPt' , 'HighVPt' , 'HighVPtmm','LowVPtmm' ,'HighVPtee' ,'LowVPtee']:
            out.branch('{0}is{1}'.format(self.pfix, cat), 'O')
            self.categories.append(cat)

        return


 #    # #    #   ##
 ##  ## #    #  #  #
 # ## # #    # #    #
 #    # #    # ######
 #    #  #  #  #    #
 #    #   ##   #    #

    def CreateMVABranches(self, out):
        '''
        Prepare the MVA branches
        '''

        for mva_name in self.mva_names:
            out.branch('vjj_mva_{0}'.format(mva_name), 'F')

        return


  ####  ###### #    #
 #    # #      ##   #
 #      #####  # #  #
 #  ### #      #  # #
 #    # #      #   ##
  ####  ###### #    #

    def CreateGenBranches(self, out):
        '''
        Prepare the GEN branches
        '''

        out.branch('vjj_photonIsMatched' , 'B' )
        out.branch('vjj_maxGenPhotonPt' , 'F' )

        return


 #    # ###### #  ####  #    # #####  ####
 #    # #      # #    # #    #   #   #
 #    # #####  # #      ######   #    ####
 # ## # #      # #  ### #    #   #        #
 ##  ## #      # #    # #    #   #   #    #
 #    # ###### #  ####  #    #   #    ####

    def CreateWeightBranches(self, out):
        '''
        Prepare the weight info branches
        '''

        out.branch('vjj_xsection' , 'F' )
        out.branch('vjj_lumiWeights' , 'F' , lenVar='vjj_nlumiWeights' )
        out.branch('vjj_weight' , 'F' )
        out.branch('vjj_pileup_up' , 'F')
        out.branch('vjj_pileup_down' , 'F')
        out.branch('vjj_L1PreFiring_up' , 'F')
        out.branch('vjj_L1PreFiring_down' , 'F')
        out.branch('vjj_particleid_up' , 'F')
        out.branch('vjj_particleid_down' , 'F')
        out.branch('vjj_particlerec_up' , 'F')
        out.branch('vjj_particlerec_down' , 'F')

        return


# //--------------------------------------------
# //--------------------------------------------
######## #### ##       ##          ##     ##    ###    ########  ####    ###    ########  ##       ########  ######
##        ##  ##       ##          ##     ##   ## ##   ##     ##  ##    ## ##   ##     ## ##       ##       ##    ##
##        ##  ##       ##          ##     ##  ##   ##  ##     ##  ##   ##   ##  ##     ## ##       ##       ##
######    ##  ##       ##          ##     ## ##     ## ########   ##  ##     ## ########  ##       ######    ######
##        ##  ##       ##           ##   ##  ######### ##   ##    ##  ######### ##     ## ##       ##             ##
##        ##  ##       ##            ## ##   ##     ## ##    ##   ##  ##     ## ##     ## ##       ##       ##    ##
##       #### ######## ########       ###    ##     ## ##     ## #### ##     ## ########  ######## ########  ######
# //--------------------------------------------
# //--------------------------------------------


 #####  ######  ####  ###### #####
 #    # #      #      #        #
 #    # #####   ####  #####    #
 #####  #           # #        #
 #   #  #      #    # #        #
 #    # ######  ####  ######   #

    def ResetCategories(self, out):

        for cat in self.categories:
            out.fillBranch('{0}is{1}'.format(self.pfix, cat), False)

        return


      # #    # ######
      # ##  ## #
      # # ## # #####
      # #    # #
 #    # #    # #
  ####  #    # ######

    def FillJMEObservables(self, out, v, tagJets, extraJets):
        '''
        Re-compute relevant jet-related observables
        '''

        #-- Dijet system #NB: compute this first to reject events mjj<cut
        jj=tagJets[0].p4()+tagJets[1].p4()
        jj_m=jj.M()
        if(jj_m<self.selCfg['min_mjj']) : return False
        out.fillBranch(self.pfix+'jj_m',    jj_m)
        out.fillBranch(self.pfix+'jj_pt',   jj.Pt())
        out.fillBranch(self.pfix+'jj_eta',  jj.Eta())
        out.fillBranch(self.pfix+'jj_phi',  jj.Phi())
        out.fillBranch(self.pfix+'jj_dr2v', jj.DeltaR(v))
        jj_scalarht=tagJets[0].pt+tagJets[1].pt
        out.fillBranch(self.pfix+'jj_scalarht',jj_scalarht)
        etaList=[tagJets[0].eta,tagJets[1].eta]
        maxEta=max(etaList)
        minEta=min(etaList)
        etaAbsList=[abs(x) for x in etaList]
        out.fillBranch(self.pfix+'j_maxAbsEta', max(etaAbsList))
        out.fillBranch(self.pfix+'j_minAbsEta', min(etaAbsList))
        jj_sumabseta=sum(etaAbsList)
        out.fillBranch(self.pfix+'jj_deta', abs(maxEta-minEta))
        out.fillBranch(self.pfix+'jj_sumabseta', jj_sumabseta)
        out.fillBranch(self.pfix+'jj_dphi', tagJets[0].p4().DeltaPhi(tagJets[1].p4()))
        out.fillBranch(self.pfix+'v_ystar', v.Eta()-0.5*jj.Eta())

        #-- Leading/subleading tagged jet
        out.fillBranch(self.pfix+'lead_pt',      tagJets[0].pt)
        out.fillBranch(self.pfix+'lead_eta',     tagJets[0].eta)
        out.fillBranch(self.pfix+'lead_phi',     tagJets[0].phi)
        out.fillBranch(self.pfix+'lead_m',       tagJets[0].mass)
        out.fillBranch(self.pfix+'lead_dr2v',    tagJets[0].DeltaR(v))
        out.fillBranch(self.pfix+'lead_dphiv',   tagJets[0].p4().DeltaPhi(v))
        out.fillBranch(self.pfix+'lead_detav',   abs(tagJets[0].eta-v.Eta()))
        if hasattr(tagJets[0],'partonFlavour'): out.fillBranch(self.pfix+'lead_flav', tagJets[0].partonFlavour)
        out.fillBranch(self.pfix+'sublead_pt',   tagJets[1].pt)
        out.fillBranch(self.pfix+'sublead_eta',  tagJets[1].eta)
        out.fillBranch(self.pfix+'sublead_phi',  tagJets[1].phi)
        out.fillBranch(self.pfix+'sublead_m',    tagJets[1].mass)
        out.fillBranch(self.pfix+'sublead_dr2v', tagJets[1].DeltaR(v))
        out.fillBranch(self.pfix+'sublead_dphiv',   tagJets[1].p4().DeltaPhi(v))
        out.fillBranch(self.pfix+'sublead_detav',   abs(tagJets[1].eta-v.Eta()))
        if hasattr(tagJets[1],'partonFlavour'): out.fillBranch(self.pfix+'sublead_flav', tagJets[1].partonFlavour)

        try:
            out.fillBranch(self.pfix+'lead_qgl',      tagJets[0].qgl)
            out.fillBranch(self.pfix+'sublead_qgl',   tagJets[1].qgl)
        except:
            pass

        #-- Hard-process object candidates
        vjj=v+jj;
        out.fillBranch(self.pfix+'vjj_pt', vjj.Pt())
        out.fillBranch(self.pfix+'vjj_eta',vjj.Eta())
        out.fillBranch(self.pfix+'vjj_phi',vjj.Phi())
        out.fillBranch(self.pfix+'vjj_m', vjj.M())
        out.fillBranch(self.pfix+'vjj_scalarht',v.Pt()+jj_scalarht)
        out.fillBranch(self.pfix+'vjj_dphi',v.DeltaPhi(tagJets[0].p4()+tagJets[1].p4()))
        out.fillBranch(self.pfix+'vjj_deta',abs(v.Eta()-jj.Eta()))

        #-- Extra radiation activity
        # extraJets=[j for j in cleanJets if not j in tagJets]
        nextraj,ncentj=len(extraJets),0
        htsoft,centhtsoft=0.,0.
        minEtaStar=minEta+0.2
        maxEtaStar=maxEta-0.2
        for j in extraJets:
            htsoft+=j.pt
            if j.eta<minEtaStar : continue
            if j.eta>maxEtaStar : continue
            ncentj+=1
            centhtsoft+=j.pt
            if ncentj>1 : continue
            out.fillBranch(self.pfix+'centj_pt',j.pt)
            out.fillBranch(self.pfix+'centj_eta',j.eta)
            out.fillBranch(self.pfix+'centj_phi',j.phi)
            out.fillBranch(self.pfix+'centj_m',  j.mass)
            out.fillBranch(self.pfix+'centj_ystar',j.eta-0.5*jj.Eta() )
            out.fillBranch(self.pfix+'centj_dr2v',j.DeltaR(v))
        out.fillBranch(self.pfix+'ncentj',ncentj)
        out.fillBranch(self.pfix+'centhtsoft',centhtsoft)
        out.fillBranch(self.pfix+'nextraj',nextraj)
        out.fillBranch(self.pfix+'htsoft',htsoft)

        return True

 ###### #    # ###### #    # #####     ####  #    #   ##   #####  ######
 #      #    # #      ##   #   #      #      #    #  #  #  #    # #
 #####  #    # #####  # #  #   #       ####  ###### #    # #    # #####
 #      #    # #      #  # #   #           # #    # ###### #####  #
 #       #  #  #      #   ##   #      #    # #    # #    # #      #
 ######   ##   ###### #    #   #       ####  #    # #    # #      ######

    def FillEventShapeObservables(self, out, v, tagJets):
        '''
        Re-compute global event observables
        '''

        #-- Event variables
        eventShape = ROOT.EventShapeVariables() #C++ dict loaded in skimmer code
        eventShape.addObject(v)
        eventShape.addObject(tagJets[0].p4())
        eventShape.addObject(tagJets[1].p4())
        out.fillBranch(self.pfix+"vjj_isotropy",    eventShape.isotropy())
        out.fillBranch(self.pfix+"vjj_circularity", eventShape.circularity())
        out.fillBranch(self.pfix+"vjj_sphericity",  eventShape.sphericity())
        out.fillBranch(self.pfix+"vjj_aplanarity",  eventShape.aplanarity())
        out.fillBranch(self.pfix+"vjj_C",           eventShape.C())
        out.fillBranch(self.pfix+"vjj_D",           eventShape.D())
        del eventShape

        return


  ####    ##   ##### ######  ####
 #    #  #  #    #   #      #    #
 #      #    #   #   #####  #
 #      ######   #   #      #  ###
 #    # #    #   #   #      #    #
  ####  #    #   #   ######  ####

    def FillCategory(self, out, category):
        '''
        Set category flag
        '''

        #-- By default, reset all categories to False
        self.ResetCategories(out)

        #-- Set relevant category to True
        out.fillBranch('{0}is{1}'.format(self.pfix, category), True) #Update category flag

        return


 #    # ###### #  ####  #    # #####  ####
 #    # #      # #    # #    #   #   #
 #    # #####  # #      ######   #    ####
 # ## # #      # #  ### #    #   #        #
 ##  ## #      # #    # #    #   #   #    #
 #    # ###### #  ####  #    #   #    ####

    def FillWeights(self, out, event, category):
        '''
        Set weight info
        '''

        #-- Write MC weight infos to output
        if not self.isData:

            #Xsec
            out.fillBranch('vjj_xsection', self.xSection)

            #Theory weights
            lumiweights = []
            for windex in range(self.nWeights):
                wid = self.allWeights[windex][1]
                lumiweights.append(event.genvjj_wgt[wid]*self.lumiWeights[category][windex])
            out.fillBranch('vjj_lumiWeights', lumiweights)
            wsf={'nom':1}
            SFs={'id':1,'pxseed':1}
            wsf['nom']=event.vjj_photonid_effWgt*event.vjj_photonpxseed_effWgt
            for k in SFs:
                for tag in ['Up','Dn']:
                    corr_type=k if k=='id' else 'rec'
                    wsf[corr_type+tag]=wsf['nom']/getattr( event , "vjj_photon{0}_effWgt".format( k ) ) * getattr( event , "vjj_photon{0}_effWgt{1}".format( k,tag ) )
            if 'mm' in category:
                wsf['nom']=event.vjj_muid_effWgt*event.vjj_muiso_effWgt
                SFs={'id':1,'iso':1}
                for k in SFs:
                    corr_type=k if k=='id' else 'rec'
                    for tag in ['Up','Dn']:
                        wsf[corr_type+tag]=wsf['nom']/getattr( event , "vjj_mu{0}_effWgt".format( k ) ) * getattr( event , "vjj_mu{0}_effWgt{1}".format( k,tag ) )
            elif 'ee' in category:
                wsf['nom']=event.vjj_eleid_effWgt*event.vjj_elerec_effWgt
                SFs={'id':1,'rec':1}
                for k in SFs:
                    for tag in ['Up','Dn']:
                        wsf[k+tag]=wsf['nom']/getattr( event , "vjj_ele{0}_effWgt".format( k ) ) * getattr( event , "vjj_ele{0}_effWgt{1}".format( k,tag ) )

            #Prefire
            prefirew = event.L1PreFiringWeight_Nom if self.era != 2018 else 1
            prefirew_up = event.L1PreFiringWeight_Up if self.era != 2018 else 1
            prefirew_down = event.L1PreFiringWeight_Dn if self.era != 2018 else 1

            out.fillBranch('vjj_L1PreFiring_up' ,wsf['nom']*event.puWeight*prefirew_up)
            out.fillBranch('vjj_L1PreFiring_down' ,wsf['nom']*event.puWeight*prefirew_down)
            out.fillBranch('vjj_pileup_down' , wsf['nom']*event.puWeightUp*prefirew )
            out.fillBranch('vjj_pileup_up' , wsf['nom']*event.puWeightDown*prefirew )

            #Object SFs
            out.fillBranch('vjj_weight' , wsf['nom']*event.puWeight*prefirew )
            out.fillBranch('vjj_particleid_up' , wsf['idUp']*event.puWeight*prefirew)
            out.fillBranch('vjj_particleid_down' , wsf['idDn']*event.puWeight*prefirew)
            out.fillBranch('vjj_particlerec_up' , wsf['recUp']*event.puWeight*prefirew)
            out.fillBranch('vjj_particlerec_down' , wsf['recDn']*event.puWeight*prefirew)

            #Gen-level info
            genParts = Collection(event, "GenPart")
	    photons = Collection(event, "Photon" )
            if event.vjj_nloosePhotons > 0:

                if self.fs == 22 and event.vjj_nphotons > 0:
                   selectedPhotonIndex = ord(event.vjj_photons[0])
                   photon_genPartIdx = photons[selectedPhotonIndex].genPartIdx
	        elif self.fs == -22:
                   selectedPhotonIndex = ord(event.vjj_loosePhotons[0])
                   photon_genPartIdx = photons[selectedPhotonIndex].genPartIdx
                else:
                   photon_genPartIdx = -10

                if photon_genPartIdx > -1:
                   if photons[selectedPhotonIndex].DeltaR(genParts[photon_genPartIdx])<0.3 and abs(genParts[photon_genPartIdx].pdgId) == 22 and ( (genParts[photon_genPartIdx].statusFlags & (1 << 0) == (1 << 0) ) or (genParts[photon_genPartIdx].statusFlags & (1 << 8) == (1 << 8) ) ):
                      out.fillBranch( 'vjj_photonIsMatched' , 1 )
                   else: out.fillBranch( 'vjj_photonIsMatched' , -10 )
                else: out.fillBranch( 'vjj_photonIsMatched' , -15 )
            else: out.fillBranch( 'vjj_photonIsMatched' , -20 )

            maxGenPhotonPt = -1
            for genPart in genParts:
                if genPart.pdgId == 22:
                    if genPart.statusFlags & 1 :
                        if genPart.pt > maxGenPhotonPt :
                            maxGenPhotonPt = genPart.pt
            out.fillBranch( 'vjj_maxGenPhotonPt' , maxGenPhotonPt )

        return


 #    # #    #   ##
 ##  ## #    #  #  #
 # ## # #    # #    #
 #    # #    # ######
 #    #  #  #  #    #
 #    #   ##   #    #

    def FillMVAObservables(self, out, event, BDTReader):
        '''
        Compute and fill MVA variables
        '''

        BDTReader.Evaluate(event)

        for i in range(len(BDTReader.outputNames)): #Write all selected MVAs to output
            mva_name = BDTReader.outputNames[i]
            out.fillBranch('{0}mva_{1}'.format(self.pfix, mva_name), BDTReader.mvaValues[i])
            #print('{0}mva_{1}'.format(self.pfix, mva_name), ' --> ', BDTReader.mvaValues[i])

        '''
        BDTReader.Process(event._entry) #Process entry

        # print('len(BDTReader.outputNames)', len(BDTReader.outputNames))
        for i in range(len(BDTReader.outputNames)): #Write all selected MVAs to output
        # for i in range(BDTReader.outputNames.size()): #Write all selected MVAs to output
            mva_name = BDTReader.outputNames[i]
            out.fillBranch('{0}mva_{1}'.format(self.pfix, mva_name), BDTReader.mvaValues[i])
        '''

        return
