#this fake PSET is needed for local test and for crab to figure the output filename
#you do not need to edit it unless you want to do a local test using a different input file than
#the one marked below
import FWCore.ParameterSet.Config as cms
process = cms.Process('NANO')
process.source = cms.Source("PoolSource", fileNames = cms.untracked.vstring(),
#	lumisToProcess=cms.untracked.VLuminosityBlockRange("254231:1-254231:24")
)
process.source.fileNames = [
    '/store/mc/RunIIAutumn18NanoAODv6/GJets_SM_5f_TuneCP5_EWK_13TeV-madgraph-pythia8/NANOAODSIM/Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/70000/F203F88E-4E04-ED48-8B71-610B696C894E.\
root'
]
process.maxEvents = cms.untracked.PSet(input = cms.untracked.int32(-1))
process.output = cms.OutputModule("PoolOutputModule", fileName = cms.untracked.string('out.root'))
process.out = cms.EndPath(process.output)
