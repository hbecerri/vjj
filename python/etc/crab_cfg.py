from WMCore.Configuration import Configuration
import os,sys
config = Configuration()

config.section_("General")
config.General.requestName = ''
config.General.workArea = ''
config.General.transferLogs=True
config.section_("Data")
config.Data.inputDataset = '/GJets_HT-40To100_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/RunIISummer16NanoAODv6-PUMoriond17_Nano25Oct2019_102X_mcRun2_asymptotic_v7-v1/NANOAODSIM'
config.Data.inputDBS = 'global'
config.Data.splitting = 'FileBased'
config.Data.unitsPerJob = 1

config.Data.outLFNDirBase = '/store/user/hbakhshi/SMP19005/June/'
config.Data.publication = False
config.section_("Site")
config.Site.storageSite = "T2_CH_CERN"

config.section_("JobType")
config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'PSet.py'
config.JobType.scriptExe = 'crab_script.sh'
config.JobType.inputFiles = ['{0}/src/PhysicsTools/NanoAODTools/scripts/haddnano.py'.format(os.environ['CMSSW_BASE'])] #hadd nano will not be needed once nano tools are in cmssw
config.JobType.sendPythonFolder	 = True
inputDsFromArg = [ arg for arg in sys.argv if arg.startswith( 'Data.inputDataset=' ) ][0].split( '=' )[-1]
config.JobType.scriptArgs = ["--inputfiles=crab", "--dataSet={0}".format(inputDsFromArg)]
