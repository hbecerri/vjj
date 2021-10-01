#! /usr/bin/env python
import os, sys
import ROOT
import argparse
ROOT.PyConfig.IgnoreCommandLineOptions = True
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import *
from UserCode.VJJSkimmer.postprocessing.modules.VJJSkimmerJME import *
from UserCode.VJJSkimmer.samples.campaigns.Manager import Manager as CampaignManager
from UserCode.VJJSkimmer.samples.Sample import Sample, SampleNameParser
from UserCode.VJJSkimmer.postprocessing.helpers.ColoredPrintout import *
from UserCode.VJJSkimmer.samples.Manager import currentSampleList as samples
from UserCode.VJJSkimmer.postprocessing.modules.JetSelector import *
from UserCode.VJJSkimmer.postprocessing.modules.VJJEvent import _defaultVjjSkimCfg

# //--------------------------------------------
# //--------------------------------------------
#-- DEFINE JEC/JER VARIATIONS
jec_sources = 'Total' #-- JES variations to process #Comma-separated list of variations #'' <-> only nominal / 'Total' <-> only total JES / 'FlavorPureCharm,FlavorPureBottom' <-> process these 2 variations only, ...

includeTotalJER = True #True <-> also process total Down/Up JER variations; False <-> do not consider JER variations
# //--------------------------------------------
# //--------------------------------------------


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

def PrintBanner():
    '''
    Print some info when starting this code
    '''

    print('\n' + colors.bg.orange + '                                           ' + colors.reset)
    print(colors.fg.orange + '\n--- Running VJJSkimmerJME (via vjj_VJJSkimmerJME_postproc.py) ---' + colors.reset + '\n')
    # print('* NB1: xxx')
    print(colors.bg.orange + '                                           ' + colors.reset + '\n')

    return


def make_hadd_fname(outdir, ds, nfilesperchunk, chunkindex, fromevent = None, nEvents = None):

    s = Sample(ds)
    outdir = '{0}/{1}/{2}/'.format(outdir , s.year() , s.makeUniqueName())
    if not os.path.exists(outdir): os.makedirs(outdir)

    if fromevent and nEvents: haddFileName = "{0}/Skimmed_{1}_{2}_f{3}_n{4}.root".format(outdir, nfilesperchunk, chunkindex, fromevent, nEvents)
    else: haddFileName = "{0}/Skimmed_{1}_{2}.root".format(outdir, nfilesperchunk, chunkindex)

    return haddFileName, os.path.exists(haddFileName)


def get_fileNames(campaign, ds, nfilesperchunk, chunkindex):

    all_inputFiles = campaign.get_dataset_info( ds )['files']
    chunks = [ all_inputFiles[a:a+nfilesperchunk] for a in range( 0 , len(all_inputFiles) , nfilesperchunk ) ]
    print(ds,nfilesperchunk,chunkindex,len(all_inputFiles) , len(chunks) )
    inputFiles = chunks[ chunkindex ]

    return inputFiles


def defineModules(year, isData, dataset, campaign, jme_vars):

    """
    Configures the modules to be run depending on the year and whether is data or MC
    Returns a list of modules
    """

    modules = []

    # modules.append(JetSelector(year, _defaultVjjSkimCfg['min_jetPt'], _defaultVjjSkimCfg['max_jetEta'], apply_id=True)) #Not needed

    if not isData and jec_sources != '':

        #-- Call NanoAODTools module to compute relevant JEC/JER/MET corrections and pass them to next modules
        jmeCorrections = createJMECorrector(isMC=True, dataYear=str(year), runPeriod="B", jesUncert=jec_sources, jetType="AK4PFchs", applySmearing=True, splitJER=False, applyHEMfix=False, saveMETUncs=[]) #saveMETUncs=['T1', 'T1Smear']
        modules.append(jmeCorrections())

        #-- Run JetSelector for each JEC/JER variation
        for var in jme_vars:
            modules.extend([JetSelector(year, _defaultVjjSkimCfg['min_jetPt'], _defaultVjjSkimCfg['max_jetEta'], apply_id=True, JMEvar=var)])

    #-- Skimmer code (run once for all variations -- recomputes necessary variables)
    modules.append(VJJSkimmerJME(dataset, campaign, JMEvars=jme_vars, includeTotalJER=includeTotalJER))

    return modules


# //--------------------------------------------
# //--------------------------------------------
##     ##    ###    #### ##    ##
###   ###   ## ##    ##  ###   ##
#### ####  ##   ##   ##  ####  ##
## ### ## ##     ##  ##  ## ## ##
##     ## #########  ##  ##  ####
##     ## ##     ##  ##  ##   ###
##     ## ##     ## #### ##    ##
# //--------------------------------------------
# //--------------------------------------------

def main():

    #-- Parse command line
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-N', '--maxEntries', dest='maxEntries',   help='max. entries to process', type=int, default=None)
    parser.add_argument('-d', '--dataSet',     dest='dataSet',   help='dataset name to skim',  default=None, type=str)
    parser.add_argument('-c', '--campaign',     dest='campaign',   help='campaign',  default=None, type=str)
    parser.add_argument('--chunkindex',     dest='chunkindex',   help='chunk the file list into sub-lists with size=nfilesperchunk and selects #chunkindex to run on',  default = None, type=int)
    parser.add_argument('--nfilesperchunk',     dest='nfilesperchunk',   help='number of files to run on',  default=1, type=int)
    parser.add_argument('--workingdir',     dest='workingdir',   help='where to store individual files',  default='./', type=str)
    parser.add_argument('-o' , '--outdir',     dest='outdir',   help='output directory',  default='./', type=str)
    parser.add_argument('-f', '--firstEntry', dest='firstEntry',   help='first entry to process', type=int, default=0)

    opt, unknownargs = parser.parse_known_args()

    if not opt.dataSet: raise ValueError('Please specify dataset name using -d option')

    PrintBanner() #Print banner in terminal

    s = SampleNameParser()
    _, info = s.parse(opt.dataSet)
    if 'year' in info.keys():
        opt.year = 2000 + int(info['year'])
        opt.isData = 'isData' in info.keys()
        opt.isSignal = samples.is_signal(opt.dataSet)
        print('dataset name is {0}'.format(opt.dataSet))
        print('year, isData and isSignal are set from the dataset name to {0}, {1} and {2}'.format(opt.year, opt.isData, opt.isSignal))
    else: raise ValueError( 'dataSet name seems inconsistent: {0}'.format(opt.dataSet))
    if opt.isData and opt.isSignal: raise ValueError(colors.fb.red + 'ERROR: isData and isSignal can not be True at the same time' + colors.reset)

    #-- Define keep/drop filepath for nominal scenario (can specific independent keep/drop file for JME variations in VJJSkimmerJME.py)
    keep_drop = '{0}/python/UserCode/VJJSkimmer/postprocessing/etc/skimmer_keep_and_drop.txt'.format( os.getenv('CMSSW_BASE' , '.') )

    campaign = None
    if opt.campaign: campaign = CampaignManager(opt.campaign)
    else: raise ValueError('Please specify campaign name you want to run using -c option')
    print(campaign.AllInfo[opt.year].keys())

    #-- Set input files
    inputFiles = get_fileNames(campaign, opt.dataSet, opt.nfilesperchunk, opt.chunkindex)
    print(colors.fg.lightblue + '\n== Processing following files:' + colors.reset)
    for i in inputFiles: print(i)

    #-- Translate JEC sources into actual Up/Down variations
    jme_vars = []
    if jec_sources != '':
        for jec_source in jec_sources.split(','):
            for shift in ['Up','Down']:
                jme_vars.append(jec_source+shift)
            if includeTotalJER:
                jme_vars.append('JERUp')
                jme_vars.append('JERDown')
        print(colors.fg.lightblue + '\n== JEC variations: ' + colors.reset); print(jme_vars); print('')

    #-- Set chain of modules to be run
    mymodules = defineModules(opt.year, opt.isData, opt.dataSet, campaign, jme_vars)
    # mymodules = [VJJSkimmerJME(opt.dataSet, campaign)]
    print('My modules: ', mymodules)

    #-- Set output
    if opt.firstEntry : haddFileName, exists = make_hadd_fname(opt.outdir, opt.dataSet, opt.nfilesperchunk, opt.chunkindex, opt.firstEntry, opt.maxEntries)
    else: haddFileName, exists = make_hadd_fname(opt.outdir, opt.dataSet, opt.nfilesperchunk, opt.chunkindex)
    print(colors.fg.lightblue + '\n== Creating output file:' + colors.reset)
    print(haddFileName + '\n')
    if exists: print(colors.fg.red + "The output file already exists, it will be overwritten : {0}\n".format(haddFileName) + colors.reset)

    #-- Cut formula for event preselection (do not process further uninteresting events) #Do not use, cf. below
    # cut = None
    cut = 'vjj_isGood && vjj_looseJets>=2 && vjj_fs!=0' #NB: supposed to speed up the processing by preskimming events; but creates problems in BDTReader (entry number not synchronized anymore) #Also 'vjj_trig>0' ?

    #-- Call post-processor
    p = PostProcessor(outputDir=opt.workingdir,
                    inputFiles=inputFiles,
                    cut=cut,
                    branchsel=None,
                    modules=mymodules,
                    provenance=True,
                    justcount=False,
                    fwkJobReport=False,
                    noOut=False,
                    outputbranchsel=keep_drop,
                    firstEntry=opt.firstEntry,
                    maxEntries=opt.maxEntries,
                    haddFileName=haddFileName)

    p.run() #Run the PostProcessor code

    print(colors.bold + colors.fg.orange + '\n... DONE !' + colors.reset)

    return


# //--------------------------------------------
# //--------------------------------------------

if __name__ == "__main__":

    #print(sys.argv)

    main()
