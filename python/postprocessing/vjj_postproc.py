#! /usr/bin/env python
import os, sys
import ROOT
import optparse
ROOT.PyConfig.IgnoreCommandLineOptions = True
from importlib import import_module
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from UserCode.VJJSkimmer.postprocessing.modules.VJJSelector import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.PrefireCorr import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.puWeightProducer import *
from UserCode.VJJSkimmer.postprocessing.modules.MuonSelector import *
from UserCode.VJJSkimmer.postprocessing.modules.ElectronSelector import *
from UserCode.VJJSkimmer.postprocessing.modules.PhotonSelector import *
from UserCode.VJJSkimmer.postprocessing.modules.JetSelector import *

def testFiles(year, isData):
    rootxd = "root://cms-xrd-global.cern.ch/"
    if isData:
        if year == 2018:
            file = '/store/data/Run2018C/EGamma/NANOAOD/Nano25Oct2019-v1/40000/36E1B766-8D23-9C43-A06E-771AB4FCE27D.root'
        elif year == 2017:
            file = '/store/data/Run2017F/SinglePhoton/NANOAOD/Nano25Oct2019-v1/20000/EE1D34F5-77E3-2C4F-82A2-B42101279278.root'
        elif year==2016:
            file = '/store/data/Run2016G/SinglePhoton/NANOAOD/Nano25Oct2019-v1/40000/E51BF2EE-295E-C540-9A21-B3EE11B3A70D.root'
    else:
        if year == 2018:
            file = '/store/mc/RunIIAutumn18NanoAODv6/GJets_SM_5f_TuneCP5_EWK_13TeV-madgraph-pythia8/NANOAODSIM/Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/70000/F203F88E-4E04-ED48-8B71-610B696C894E.root'
        elif year == 2017:
            file = '/store/mc/RunIIFall17NanoAODv6/GJets_SM_5f_TuneCUETP8M1_EWKFOR17DATA_13TeV-madgraphMLM-pythia8/NANOAODSIM/PU2017_12Apr2018_Nano25Oct2019_ext_102X_mc2017_realistic_v7-v1/230000/1D712E02-0EED-7041-A17A-858A01783DA5.root'
        elif year==2016:
            file = '/store/mc/RunIISummer16NanoAODv6/GJets_Mjj-500_SM_5f_TuneCUETP8M1_EWK_13TeV-madgraph-pythia8/NANOAODSIM/Nano25Oct2019_102X_mcRun2_asymptotic_v7-v1/270000/6DCCCEA5-082C-8849-85F1-CE698EB2778F.root'

    return rootxd + file

def defineModules(year,isData):

    modules=[]
    if not isData:
        if year==2016:
            modules.append( puAutoWeight_2016() )
            modules.append( PrefCorr() )
            modules.append( PrefCorr(jetroot="L1prefiring_jetpt_2016BtoH.root",
                                     jetmapname="L1prefiring_jetpt_2016BtoH",
                                     photonroot="L1prefiring_photonpt_2016BtoH.root",
                                     photonmapname="L1prefiring_photonpt_2016BtoH.root") )
            modules.extend( [MuonSelector2016(), ElectronSelector2016(), PhotonSelector2016(), JetSelector2016() ])
            modules.append( vjjSkimmer2016mc() )
        if year==2017:
            modules.append( puAutoWeight_2017() )
            modules.append( PrefCorr(jetroot="L1prefiring_jetpt_2017BtoF.root",
                                     jetmapname="L1prefiring_jetpt_2017BtoF",
                                     photonroot="L1prefiring_photonpt_2017BtoF.root",
                                     photonmapname="L1prefiring_photonpt_2017BtoF") )
            modules.extend( [MuonSelector2017(), ElectronSelector2017(), PhotonSelector2017(), JetSelector2017() ])
            modules.append( vjjSkimmer2017mc() )
        if year==2018:
            modules.append( puAutoWeight_2018() )
            modules.extend( [MuonSelector2018(), ElectronSelector2018(), PhotonSelector2018(), JetSelector2018() ])
            modules.append( vjjSkimmer2018mc() )

    else:
        if year==2016:
            modules.extend( [MuonSelector2016(), ElectronSelector2016(), PhotonSelector2016(), JetSelector2016() ])
            modules.append( vjjSkimmer2016data() )
        if year==2017:
            modules.extend( [MuonSelector2017(), ElectronSelector2017(), PhotonSelector2017(), JetSelector2017() ])
            modules.append( vjjSkimmer2017data() )
        if year==2018:
            modules.extend( [MuonSelector2018(), ElectronSelector2018(), PhotonSelector2018(), JetSelector2018() ])
            modules.append( vjjSkimmer2018data() )

    return modules


def main():

    #parse command line
    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)
    parser.add_option('-y', '--year',       dest='year',   help='year [%default]',  default=2017,  type=int)
    parser.add_option(      '--isData',     dest='isData', help='data? [%default]', default=False, action='store_true')
    parser.add_option('-i', '--inputfiles', dest='inputFiles',   help='input [%default]', type='string',
                      default='TestInputFile')
    parser.add_option('-k', '--keep_and_drop', dest='keep_and_drop',   help='keep and drop [%default]', type='string',
                      default='python/postprocessing/etc/keep_and_drop.txt')
    parser.add_option('-N', '--maxEntries', dest='maxEntries',   help='max. entries to process [%default]', type=int,
                      default=None)
    parser.add_option('-f', '--firstEntry', dest='firstEntry',   help='first entry to process [%default]', type=int,
                      default=0)
    (opt, args) = parser.parse_args()

    if opt.inputFiles == "TestInputFile":
        opt.inputFiles = testFiles( opt.year , opt.isData )
        print( opt.inputFiles )
    #start by defining modules to run
    modules=defineModules(opt.year,opt.isData)

    #call post processor
    p=PostProcessor(outputDir=".",
                    inputFiles=opt.inputFiles.split(','),
                    cut=None,
                    branchsel=None,
                    modules=modules,
                    provenance=True,
                    justcount=False,
                    fwkJobReport=False,
                    noOut=False,
                    outputbranchsel = opt.keep_and_drop,
                    maxEntries=opt.maxEntries,
                    firstEntry=opt.firstEntry)

    p.run()



if __name__ == "__main__":
    main()
