#!/usr/bin/env python

import os

#this directory should have edit permissions for all members of the e-group
_testCIDir='/eos/user/c/cmsewvjj/data/CMSSW_10_2_13'

_testDatasets={
    (2018,'data') : '/store/data/Run2018C/EGamma/NANOAOD/Nano25Oct2019-v1/40000/36E1B766-8D23-9C43-A06E-771AB4FCE27D.root',
    (2018,'mc')   : '/store/mc/RunIIAutumn18NanoAODv6/GJets_SM_5f_TuneCP5_EWK_13TeV-madgraph-pythia8/NANOAODSIM/Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/70000/F203F88E-4E04-ED48-8B71-610B696C894E.root',
    (2017,'data') : '/store/data/Run2017F/SinglePhoton/NANOAOD/Nano25Oct2019-v1/20000/EE1D34F5-77E3-2C4F-82A2-B42101279278.root',
    (2017,'mc')   : '/store/mc/RunIIFall17NanoAODv6/GJets_SM_5f_TuneCUETP8M1_EWKFOR17DATA_13TeV-madgraphMLM-pythia8/NANOAODSIM/PU2017_12Apr2018_Nano25Oct2019_ext_102X_mc2017_realistic_v7-v1/230000/1D712E02-0EED-7041-A17A-858A01783DA5.root',
    (2016,'data') : '/store/data/Run2016G/SinglePhoton/NANOAOD/Nano25Oct2019-v1/40000/E51BF2EE-295E-C540-9A21-B3EE11B3A70D.root',
    (2016,'mc')   : '/store/mc/RunIISummer16NanoAODv6/GJets_Mjj-500_SM_5f_TuneCUETP8M1_EWK_13TeV-madgraph-pythia8/NANOAODSIM/Nano25Oct2019_102X_mcRun2_asymptotic_v7-v1/270000/6DCCCEA5-082C-8849-85F1-CE698EB2778F.root',
}

def getTestCIDir():
    return _testCIDir

def getTestDataset(year,isData,fromLocalCIDir=None):

    """
    uses the default dict of test datasets to return a file for testing
    if a fromLocalCIDir directory is passed, the base directory is fully substituted by the 
    directory used for cont. integration in gitlab
    """

    key=(year,'data' if isData else 'mc')
    url=_testDatasets[key]

    if not fromLocalCIDir:
        url=os.path.join("root://cms-xrd-global.cern.ch/",url)
    else:
        url=os.path.join(fromLocalCIDir,os.path.basename(url))

    return url
