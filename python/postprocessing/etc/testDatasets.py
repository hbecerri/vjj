#!/usr/bin/env python

import os

#this directory should have edit permissions for all members of the e-group
_testCIDir='/eos/user/c/cmsewvjj/data/CMSSW_10_2_13'

_testDatasets_v6={
    (2018,'data') : '/store/data/Run2018C/EGamma/NANOAOD/Nano25Oct2019-v1/40000/36E1B766-8D23-9C43-A06E-771AB4FCE27D.root',
    (2018,'mc')   : '/store/mc/RunIIAutumn18NanoAODv6/GJets_SM_5f_TuneCP5_EWK_13TeV-madgraph-pythia8/NANOAODSIM/Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/70000/F203F88E-4E04-ED48-8B71-610B696C894E.root',
    (2017,'data') : '/store/data/Run2017F/SinglePhoton/NANOAOD/Nano25Oct2019-v1/20000/EE1D34F5-77E3-2C4F-82A2-B42101279278.root',
    (2017,'mc')   : '/store/mc/RunIIFall17NanoAODv6/GJets_SM_5f_TuneCUETP8M1_EWKFOR17DATA_13TeV-madgraphMLM-pythia8/NANOAODSIM/PU2017_12Apr2018_Nano25Oct2019_ext_102X_mc2017_realistic_v7-v1/230000/1D712E02-0EED-7041-A17A-858A01783DA5.root',
    (2016,'data') : '/store/data/Run2016G/SinglePhoton/NANOAOD/Nano25Oct2019-v1/40000/E51BF2EE-295E-C540-9A21-B3EE11B3A70D.root',
    (2016,'mc')   : '/store/mc/RunIISummer16NanoAODv6/GJets_Mjj-500_SM_5f_TuneCUETP8M1_EWK_13TeV-madgraph-pythia8/NANOAODSIM/Nano25Oct2019_102X_mcRun2_asymptotic_v7-v1/270000/6DCCCEA5-082C-8849-85F1-CE698EB2778F.root',
}

_testDatasets_v7={
    (2018,'data') : '/store/data/Run2018D/EGamma/NANOAOD/02Apr2020-v1/240000/C33543B3-D425-E140-8989-C49187506D53.root',
    (2018,'mc')   : '/store/mc/RunIIAutumn18NanoAODv7/GJets_SM_5f_TuneCP5_EWK_13TeV-madgraph-pythia8/NANOAODSIM/Nano02Apr2020_102X_upgrade2018_realistic_v21-v1/60000/4A976057-5F72-254D-ACA6-7B6C0B4E6CCA.root',
    (2017,'data') : '/store/data/Run2017D/DoubleEG/NANOAOD/02Apr2020-v1/30000/833361DB-6434-0E49-B6DF-F9E19B07161E.root',
    (2017,'mc')   : '/store/mc/RunIIFall17NanoAODv7/GJets_SM_5f_TuneCP5_EWK_13TeV-madgraph-pythia8/NANOAODSIM/PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8_ext1-v1/100000/77320569-3F5E-F341-8AF3-E22692A69AF8.root',
    (2016,'data') : '/store/data/Run2016D/DoubleEG/NANOAOD/02Apr2020-v1/40000/0478D638-CA44-B549-ABCC-B014D513408C.root',
    (2016,'mc')   : '/store/mc/RunIISummer16NanoAODv7/GJets_SM_5f_TuneCUETP8M1_EWK_13TeV-madgraph-pythia8/NANOAODSIM/Nano02Apr2020_102X_mcRun2_asymptotic_v8-v1/60000/502E1C3B-8CA3-CC44-8BEA-B5D2FDF35844.root'
}

_testDatasets = _testDatasets_v7

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
