#! /usr/bin/env python
import os, sys
import ROOT
import argparse
ROOT.PyConfig.IgnoreCommandLineOptions = True
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import *
from UserCode.VJJSkimmer.postprocessing.modules.SkimEventsAndComputeObservables import *
from UserCode.VJJSkimmer.samples.campaigns.Manager import Manager as CampaignManager
from UserCode.VJJSkimmer.samples.Sample import Sample, SampleNameParser
from UserCode.VJJSkimmer.postprocessing.helpers.ColoredPrintout import *
from UserCode.VJJSkimmer.samples.Manager import currentSampleList as samples
from UserCode.VJJSkimmer.postprocessing.modules.JetSelector import *
from UserCode.VJJSkimmer.postprocessing.modules.VJJEvent import _defaultVjjSkimCfg


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
    print(colors.fg.orange + '\n--- Running SkimEventsAndComputeObservables (via vjj_skimCompute_postproc.py) ---' + colors.reset + '\n')
    # print('* NB1: xxx')
    print(colors.bg.orange + '                                           ' + colors.reset + '\n')

    return


def make_hadd_fname(outdir, ds, nfilesperchunk, chunkindex, fromevent = None, nEvents = None):

    s = Sample(ds)
    outdir = '{0}/{1}/{2}/'.format(outdir , s.year() , s.makeUniqueName())
    if not os.path.exists(outdir): os.makedirs(outdir)

    if fromevent and nEvents: haddFileName = "{0}/Skimmed_{1}_{2}_f{3}_n{4}.root".format( outdir , nfilesperchunk , chunkindex , fromevent , nEvents )
    else: haddFileName = "{0}/Skimmed_{1}_{2}.root".format( outdir , nfilesperchunk , chunkindex )

    return haddFileName, os.path.exists(haddFileName)


def get_fileNames(campaign, ds, nfilesperchunk, chunkindex):

    all_inputFiles = campaign.get_dataset_info( ds )['files']
    chunks = [ all_inputFiles[a:a+nfilesperchunk] for a in range( 0 , len(all_inputFiles) , nfilesperchunk ) ]
    print(ds,nfilesperchunk,chunkindex,len(all_inputFiles) , len(chunks) )
    inputFiles = chunks[ chunkindex ]

    return inputFiles


def defineModules(year, isData, dataset, campaign):

    """
    Configures the modules to be run depending on the year and whether is data or MC
    Returns a list of modules
    """

    modules = []

    #FIXME
    if not isData:

        jmeCorrections = createJMECorrector(isMC=True, dataYear=str(year), runPeriod="B", jesUncert="Total", jetType="AK4PFchs", applySmearing=True, splitJER=False, applyHEMfix=False, saveMETUncs=[]) #saveMETUncs=['T1', 'T1Smear']
        modules.append(jmeCorrections())

        jecs = ['Total']

        for jec in jecs:
            if year==2016:
                # modules.extend([jetSelector2016()])
                modules.extend([JetSelector(2016,_defaultVjjSkimCfg['min_jetPt'], _defaultVjjSkimCfg['max_jetEta'], apply_id=True, vetoObjs=[])])


    modules.append(SkimEventsAndComputeObservables(dataset, campaign))

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

    #-- Define keep/drop filepath
    keep_drop = '{0}/python/UserCode/VJJSkimmer/postprocessing/etc/skimmer_keep_and_drop.txt'.format( os.getenv('CMSSW_BASE' , '.') )

    campaign = None
    if opt.campaign: campaign = CampaignManager(opt.campaign)
    else: raise ValueError('Please specify campaign name you want to run using -c option')
    print(campaign.AllInfo[opt.year].keys())

    #-- Set input files
    inputFiles = get_fileNames(campaign, opt.dataSet, opt.nfilesperchunk, opt.chunkindex)

    #-- Set chain of modules to be run
    mymodules = defineModules(opt.year, opt.isData, opt.dataSet, campaign)
    # mymodules = [SkimEventsAndComputeObservables(opt.dataSet, campaign)]
    print('My modules: ', mymodules)

    #-- Set output
    if opt.firstEntry : haddFileName, exists = make_hadd_fname(opt.outdir, opt.dataSet, opt.nfilesperchunk, opt.chunkindex , opt.firstEntry , opt.maxEntries)
    else: haddFileName, exists = make_hadd_fname(opt.outdir, opt.dataSet, opt.nfilesperchunk, opt.chunkindex)
    print(colors.fg.lightblue + '\n== Processing following files:' + colors.reset)
    for i in inputFiles: print(i)
    print(colors.fg.lightblue + '\n== Creating output file:' + colors.reset)
    print(haddFileName + '\n')
    if exists: print(colors.fg.red + "The output file already exists, it will be overwritten : {0}\n".format( haddFileName ) + colors.reset)

    #-- Call post-processor
    p = PostProcessor(outputDir=opt.workingdir,
                    inputFiles=inputFiles,
                    cut=None,
                    branchsel=None,
                    modules=mymodules,
                    provenance=True,
                    justcount=False,
                    fwkJobReport=False,
                    noOut=False,
                    outputbranchsel = keep_drop,
                    firstEntry=opt.firstEntry,
                    maxEntries=opt.maxEntries,
                    haddFileName = haddFileName)

    p.run() #Run the PostProcessor code

    print(colors.bold + colors.fg.orange + '\n... DONE !' + colors.reset)

    return


# //--------------------------------------------
# //--------------------------------------------

if __name__ == "__main__":

    print(sys.argv)
    main()
