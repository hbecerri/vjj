#See also:
#- https://root.cern.ch/doc/v614/ApplicationClassificationKeras_8py_source.html
#- https://aholzner.wordpress.com/2011/08/27/a-tmva-example-in-pyroot/

import os
from os.path import isfile
import math
from ROOT import TMVA, TFile, TString
from array import array
from subprocess import call
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection

from random import seed, random #For tests with random inputs
seed(1)


class BDTReader():


 # #    # # #####
 # ##   # #   #
 # # #  # #   #
 # #  # # #   #
 # #   ## #   #
 # #    # #   #

    def __init__(self):

        self.xmlDir = '{0}/src/UserCode/VJJPlotter/data/'.format(os.getenv('CMSSW_BASE', '.'))
        self.outputNames = []
        self.mvaValues = []
        self.readers = []
        self.branchNames_readers = []
        self.branches_readers = []
        self.prefix = 'vjj_'

        return


  ####  ###### ##### #    # #####
 #      #        #   #    # #    #
  ####  #####    #   #    # #    #
      # #        #   #    # #####
 #    # #        #   #    # #
  ####  ######   #    ####  #

    def Setup(self):

        print('Directory of XML files: ', self.xmlDir)

        for iname, name in enumerate(['HighVPt', 'LowVPt']):

            outputName  = "BDT_VBF0"+name
            self.outputNames.append(outputName)
            self.mvaValues.append(0)
            reader = TMVA.Reader("Color:!Silent")

            branchNames = []
            if name == 'LowVPt':

                branchNames = [self.prefix+'vjj_circularity',
                               self.prefix+'jj_m',
                               self.prefix+'jj_pt',
                               self.prefix+'jj_dphi',
                               self.prefix+'v_ystar',
                               self.prefix+'relbpt',
                               self.prefix+'jj_vdphi',
                               self.prefix+'lead_qgl',
                               self.prefix+'sublead_qgl',
                               self.prefix+'lead_dphivj',
                               self.prefix+'vjj_D']


            elif name == 'HighVPt':

                branchNames = [self.prefix+'sublead_pt',
                               self.prefix+'jj_m',
                               self.prefix+'jj_pt',
                               self.prefix+'jj_deta',
                               self.prefix+'jj_dphi',
                               self.prefix+'v_ystar',
                               self.prefix+'jj_vdphi',
                               self.prefix+'lead_qgl',
                               self.prefix+'sublead_qgl',
                               self.prefix+'lead_dphivj',
                               self.prefix+'sublead_dphivj',
                               self.prefix+'vjj_aplanarity',
                               self.prefix+'vjj_C']

            else: print('ERROR: wrong method name !')

            branches = []
            for ib, branchName in enumerate(branchNames):
                branches.append(array('f', [-999]))
                reader.AddVariable(self.ConvertVariableNameXML(branchName), branches[ib])

            self.branchNames_readers.append(branchNames)
            self.branches_readers.append(branches)

            weightFile = self.xmlDir +"/"+name+"_BDT_VBF0"+name+".weights.xml"
            reader.BookMVA(outputName, weightFile )
            self.readers.append(reader)

        return


  ####   ####  #    # #    # ###### #####  #####    #    #   ##   #    # ######
 #    # #    # ##   # #    # #      #    #   #      ##   #  #  #  ##  ## #
 #      #    # # #  # #    # #####  #    #   #      # #  # #    # # ## # #####
 #      #    # #  # # #    # #      #####    #      #  # # ###### #    # #
 #    # #    # #   ##  #  #  #      #   #    #      #   ## #    # #    # #
  ####   ####  #    #   ##   ###### #    #   #      #    # #    # #    # ######

    def ConvertVariableNameXML(self, varname):

        if varname == self.prefix+'vjj_circularity': return 'circularity'
        elif varname == self.prefix+'jj_m': return 'mjj'
        elif varname == self.prefix+'jj_pt': return 'jjpt'
        elif varname == self.prefix+'jj_dphi': return 'dphijj'
        elif varname == self.prefix+'v_ystar': return 'ystar'
        elif varname == self.prefix+'jj_vdphi': return 'dphibjj'
        elif varname == self.prefix+'lead_dphivj': return 'dphivj0'
        elif varname == self.prefix+'vjj_D': return 'D'
        elif varname == self.prefix+'lead_qgl': return 'j_qg[0]'
        elif varname == self.prefix+'sublead_qgl': return 'j_qg[1]'
        elif varname == self.prefix+'sublead_pt': return 'subleadj_pt'
        elif varname == self.prefix+'jj_deta': return 'detajj'
        elif varname == self.prefix+'sublead_dphivj': return 'dphivj1'
        elif varname == self.prefix+'vjj_aplanarity': return 'aplanarity'
        elif varname == self.prefix+'vjj_C': return 'C'
        elif varname == self.prefix+'relbpt': return 'relbpt'

        return varname


 ###### # #      #
 #      # #      #
 #####  # #      #
 #      # #      #
 #      # #      #
 #      # ###### ######

    def FillBranchValues(self, event):

        for ireader in range(len(self.readers)):

            for ib, branchName in enumerate(self.branchNames_readers[ireader]):

                #-- Hardcoded
                if branchName == self.prefix+'relbpt': self.branches_readers[ireader][ib][0] = event.vjj_jj_scalarht/event.vjj_v_pt
                elif branchName == self.prefix+'jj_vdphi': self.branches_readers[ireader][ib][0] = (event.vjj_jj_phi-event.vjj_v_phi)%(2*math.pi)
                elif branchName == self.prefix+'lead_dphivj': self.branches_readers[ireader][ib][0] = (event.vjj_lead_phi-event.vjj_v_phi)%(2*math.pi)
                elif branchName == self.prefix+'sublead_dphivj': self.branches_readers[ireader][ib][0] = (event.vjj_sublead_phi-event.vjj_v_phi)%(2*math.pi)

                else: self.branches_readers[ireader][ib][0] = eval('event.{}'.format(branchName))

                # if branchName == 'vjj_vjj_C': self.branches_readers[ireader][ib][0] = random()
                # if branchName == 'vjj_vjj_D': self.branches_readers[ireader][ib][0] = random()
                # if branchName == 'vjj_vjj_circularity': self.branches_readers[ireader][ib][0] = random()
                # if branchName == 'vjj_vjj_aplanarity': self.branches_readers[ireader][ib][0] = random() / 2
                # self.branches_readers[ireader][ib][0] = random()

                #-- Protection against NaNs (e.g. qgl variable has some NaNs already in NanoAOD files) #Disactivate for now for speedup, as this only affects few events
                # if math.isnan(self.branches_readers[ireader][ib][0]):
                #     self.branches_readers[ireader][ib][0] = 0
                #     print('The following branch value is NaN --> Setting it to 0: ', branchName)

        return


 ###### #    #   ##   #      #    #   ##   ##### ######
 #      #    #  #  #  #      #    #  #  #    #   #
 #####  #    # #    # #      #    # #    #   #   #####
 #      #    # ###### #      #    # ######   #   #
 #       #  #  #    # #      #    # #    #   #   #
 ######   ##   #    # ######  ####  #    #   #   ######

    def Evaluate(self, event):

        self.FillBranchValues(event)

        for ireader in range(len(self.readers)):
            # print(self.readers[ireader].DataInfo().GetNVariables())
            self.mvaValues.append(0) #Default output value
            output = self.readers[ireader].EvaluateMVA(self.outputNames[ireader])
            self.mvaValues[ireader] = output
            # print('--> output', output)

        return
