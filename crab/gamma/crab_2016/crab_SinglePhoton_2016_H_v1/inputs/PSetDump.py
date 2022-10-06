import FWCore.ParameterSet.Config as cms

process = cms.Process("NANO")

process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring('/store/mc/RunIIAutumn18NanoAODv6/GJets_SM_5f_TuneCP5_EWK_13TeV-madgraph-pythia8/NANOAODSIM/Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/70000/F203F88E-4E04-ED48-8B71-610B696C894E.root')
)
process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(-1)
)

process.output = cms.OutputModule("PoolOutputModule",
    fileName = cms.untracked.string('out.root')
)


process.out = cms.EndPath(process.output)


