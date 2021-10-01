#!/usr/bin/env python

import os
from ROOT import TMVA, TFile, TString
from array import array
from subprocess import call
from os.path import isfile
import math
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection

#FIXME
from random import seed, random
seed(1)

class BDTReader():

    def __init__(self):

        self.xmlDir = '{0}/src/UserCode/VJJPlotter/data/'.format(os.getenv('CMSSW_BASE', '.'))
        self.methodNames = []
        self.mvaValues = []
        self.readers = []
        # self.branchNames_readers = {}
        self.branchNames_readers = []
        self.branches_readers = [{}, {}]
        # self.branches_readers = []
        self.prefix = 'vjj_'

        self.var0 = array('f', [-999])
        self.var1 = array('f', [-999])

        return


    def Init(self):

        print('Directory of XML files: ', self.xmlDir)

        for iname, name in enumerate(['HighVPt', 'LowVPt']):

            methodName  = "BDT_VBF0"+name
            self.methodNames.append(methodName)
            self.mvaValues.append(0)
            reader = TMVA.Reader("Color:!Silent")

            branchNames = []
            if name == 'LowVPt':

                branchNames = [self.prefix+'vjj_circularity',
                               self.prefix+'jj_m',
                               self.prefix+'jj_pt',
                               self.prefix+'jj_dphi',
                               self.prefix+'v_ystar',
                               self.prefix+'relbpt', #FIXME
                               self.prefix+'jj_vdphi', #FIXME
                               self.prefix+'lead_qgl',
                               self.prefix+'sublead_qgl',
                               self.prefix+'lead_dphivj', #FIXME
                               self.prefix+'vjj_D']


            elif name == 'HighVPt':

                branchNames = [self.prefix+'sublead_pt',
                               self.prefix+'jj_m',
                               self.prefix+'jj_pt',
                               self.prefix+'jj_deta',
                               self.prefix+'jj_dphi',
                               self.prefix+'v_ystar',
                               self.prefix+'jj_vdphi', #FIXME
                               self.prefix+'lead_qgl',
                               self.prefix+'sublead_qgl',
                               self.prefix+'lead_dphivj', #FIXME
                               self.prefix+'sublead_dphivj', #FIXME
                               self.prefix+'vjj_aplanarity',
                               self.prefix+'vjj_C']

            else: print('ERROR: wrong name !')

            branches = {}
            for ib, branchName in enumerate(branchNames):
                # branches.append(array('f', [-999]))
                # branches[branchName] = array('f', [-999])
                # self.branches_readers[iname][branchName] = array('f', [-999])
                self.branches_readers[iname][branchName] = array('f', [-999])

                #FIXME
                # if ib==0: branches[0] = self.var0
                # elif ib==1: branches[1] = self.var1

                reader.AddVariable(self.ConvertVariableNameXML(branchName), self.branches_readers[iname][branchName])
                # reader.AddVariable(self.ConvertVariableNameXML(branchName), branches[branchName])
                # reader.AddVariable(self.ConvertVariableNameXML(branchName), branches[branchName])
                # reader.AddVariable(self.ConvertVariableNameXML(branchName), branches[ib])
                # print('reader.AddVariable({})'.format(branchName))

            self.branchNames_readers.append(branchNames)
            # self.branches_readers.append(branches)

            weightFile = self.xmlDir +"/"+name+"_BDT_VBF0"+name+".weights.xml"
            reader.BookMVA(methodName, weightFile )
            self.readers.append(reader)

        return


    def FillBranchValues(self, event):

        for ireader in range(len(self.readers)):
            for ib, branchName in enumerate(self.branchNames_readers[ireader]):

                #-- Hardcoded
                # if branchName == self.prefix+'relbpt': self.branches_readers[ireader][ib][0] = event.vjj_jj_scalarht/event.vjj_v_pt
                # elif branchName == self.prefix+'jj_vdphi': self.branches_readers[ireader][ib][0] = (event.vjj_jj_phi/event.vjj_v_phi)%2*math.pi #FIXME
                # elif branchName == self.prefix+'lead_dphivj': self.branches_readers[ireader][ib][0] = (event.vjj_lead_phi/event.vjj_v_phi)%2*math.pi #FIXME
                # elif branchName == self.prefix+'sublead_dphivj': self.branches_readers[ireader][ib][0] = (event.vjj_sublead_phi/event.vjj_v_phi)%2*math.pi #FIXME
                # else: self.branches_readers[ireader][ib][0] = eval('event.{}'.format(branchName))

                if branchName == self.prefix+'relbpt': self.branches_readers[ireader][branchName][0] = event.vjj_jj_scalarht/event.vjj_v_pt
                elif branchName == self.prefix+'jj_vdphi': self.branches_readers[ireader][branchName][0] = (event.vjj_jj_phi-event.vjj_v_phi)%2*math.pi #FIXME
                elif branchName == self.prefix+'lead_dphivj': self.branches_readers[ireader][branchName][0] = (event.vjj_lead_phi-event.vjj_v_phi)%2*math.pi #FIXME
                elif branchName == self.prefix+'sublead_dphivj': self.branches_readers[ireader][branchName][0] = (event.vjj_sublead_phi-event.vjj_v_phi)%2*math.pi #FIXME
                elif branchName=='vjj_vjj_C' or branchName=='vjj_vjj_D': continue
                else:
                    self.branches_readers[ireader][branchName][0] = eval('event.{}'.format(branchName))
                    print(branchName, ' ', eval('event.{}'.format(branchName))) #FIXME

                if branchName not in self.branches_readers[ireader]: print('ERROR ! Unknown branchname' , branchname)

                # if branchName=='vjj_vjj_C': self.branches_readers[ireader][branchName][0] = 55232.6484375
                # if branchName=='vjj_vjj_D': self.branches_readers[ireader][branchName][0] = 2495826.25

                #FIXME
                # print(self.branches_readers[ireader][ib][0])
                self.branches_readers[ireader][branchName][0] = random()
                # self.var0 = random()
                # self.var1 = random()

                # print(self.branchNames_readers[ireader][ib], ' --> ', self.branches_readers[ireader][branchName]) #FIXME
                # print(self.branchNames_readers[ireader][ib], ' --> ', self.branches_readers[ireader][ib]) #FIXME

        return


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


    def Process(self, event):

        self.FillBranchValues(event)

        for ireader in range(len(self.readers)):
            #FIXME
            print(self.readers[ireader].DataInfo().GetNVariables())
            self.mvaValues.append(0) #Default
            output = self.readers[ireader].EvaluateMVA(self.methodNames[ireader])
            self.mvaValues[ireader] = output
            print('--> output', output) #FIXME

        return
