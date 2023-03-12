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
from UserCode.VJJSkimmer.postprocessing.modules.VJJEvent import _defaultVjjSkimCfg, _defaultObjCfg

#To copy job output manually (not used)
#from shutil import copyfile
#import glob


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


def make_hadd_fname(workingdir,outdir, ds, nfilesperchunk, chunkindex, fromevent = None, nEvents = None):

    s = Sample(ds)
    outdir = '{0}/{1}/{2}/'.format(outdir , s.year() , s.makeUniqueName())
    if not os.path.exists(outdir): os.makedirs(outdir)

    if fromevent and nEvents: haddFileName = "{0}/Skimmed_{1}_{2}_f{3}_n{4}.root".format(outdir, nfilesperchunk, chunkindex, fromevent, nEvents)
    else: haddFileName = workingdir+"/{0}/Skimmed_{1}_{2}.root".format(outdir, nfilesperchunk, chunkindex)
#    else: haddFileName = "{0}/out_{1}_Skim.root".format(outdir, chunkindex+1)

    return haddFileName, os.path.exists(haddFileName)


def get_fileNames(campaign, ds, nfilesperchunk, chunkindex, printout=True):
    all_inputFiles = campaign.get_dataset_info( ds )['files']
#    print(all_inputFiles)
#    print(len(all_inputFiles))
    chunks = [ all_inputFiles[a:a+nfilesperchunk] for a in range( 0 , len(all_inputFiles) , nfilesperchunk ) ]
    if printout: print(ds,nfilesperchunk,chunkindex,len(all_inputFiles) , len(chunks) )
    inputFiles = chunks[ chunkindex ]

    return inputFiles


def defineModules(year, isData, dataset, campaign, finalState, jme_vars):

    modules = []

    print('finale state:',finalState)
    if not isData and jec_sources != '':

        jmeCorrections = createJMECorrector(isMC=True, dataYear=str(year), runPeriod="B", jesUncert=jec_sources, jetType="AK4PFchs", applySmearing=True, splitJER=False, applyHEMfix=False, saveMETUncs=[])
        modules.append(jmeCorrections())
        for var in jme_vars:
            modules.extend([JetSelector(year, cfg=_defaultObjCfg, apply_id=True, JMEvar=var)])
            modules.extend([JetSelector(year, cfg=_defaultObjCfg, apply_id=False, JMEvar=var)])
    modules.append(VJJSkimmerJME(dataset, campaign, finalState, _defaultVjjSkimCfg, JMEvars=jme_vars, includeTotalJER=includeTotalJER))
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
    parser.add_argument('--workingdir',     dest='workingdir',   help='where to temporarily store individual output files',  default='./', type=str)
    parser.add_argument('-o' , '--outdir',     dest='outdir',   help='final output directory',  default='./', type=str)
    parser.add_argument('-f', '--firstEntry', dest='firstEntry',   help='first entry to process', type=int, default=0)
    parser.add_argument('-S', '--finalState',     dest='finalState',   help='photon:22, fake photon:-22, mm: 169, ee:121',  default=0, type=int)
    opt, unknownargs = parser.parse_known_args()

    if not opt.dataSet: raise ValueError('Please specify dataset name using -d option')

    if opt.finalState == None: raise ValueError('Must set the final state. Use --help for the options.') 
    if opt.finalState not in [22, -22, 169, 121]: opt.finalState = 22   #raise ValueError('Non standard value for final state. Use --help for the options.') 
     
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

    print(opt.isData)

    #-- Define 'golden json' luminosity mask to be applied for data
    jsonMask = None
    if opt.isData: #Do not apply to MC !
        jsonDir = '/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/'
        if opt.year == 2016: jsonMask = jsonDir+'Collisions16/13TeV/Legacy_2016/Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt' #2016
        elif opt.year == 2017: jsonMask = jsonDir+'Collisions17/13TeV/Legacy_2017/Cert_294927-306462_13TeV_UL2017_Collisions17_GoldenJSON.txt' #2017
        elif opt.year == 2018: jsonMask = jsonDir+'Collisions18/13TeV/Legacy_2018/Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt' #2018
    if jsonMask is not None: print(colors.fg.lightblue + '\n== Applying lumi mask: ' + colors.reset); print(jsonMask); print('')


    
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
    mymodules = defineModules(opt.year, opt.isData, opt.dataSet, campaign, opt.finalState, jme_vars)
    # print('My modules: ', mymodules)


    #-- Set output
    if opt.firstEntry : haddFileName, exists = make_hadd_fname(opt.workingdir,opt.outdir, opt.dataSet, opt.nfilesperchunk, opt.chunkindex, opt.firstEntry, opt.maxEntries)
    else: haddFileName, exists = make_hadd_fname(opt.workingdir,opt.outdir, opt.dataSet, opt.nfilesperchunk, opt.chunkindex)
#    haddFileName=opt.workingdir+haddFileName
    print(colors.fg.lightblue + '\n== Creating output file:' + colors.reset)
    print(haddFileName + '\n')
    if exists: print(colors.fg.red + "The output file already exists, it will be overwritten : {0}\n".format(haddFileName) + colors.reset)

    #-- Cut formula for event preselection (do not process further uninteresting events) #Do not use, cf. below
    # cut = None
    cut = 'vjj_njets>=2 && vjj_fs!=0 && vjj_trig>0 && vjj_jj_m>350' #NB: speed up processing
    print('finale state:',opt.finalState)

    #-- Call post-processor
    p = PostProcessor(outputDir=opt.workingdir, #Dir where to store individual output files
                    inputFiles=inputFiles,
                    cut=cut,
                    modules=mymodules,
                    outputbranchsel=keep_drop,
                    jsonInput=jsonMask,
                    branchsel=None,
                    provenance=True,
                    justcount=False,
                    fwkJobReport=False,
                    noOut=False,
                    firstEntry=opt.firstEntry,
                    maxEntries=opt.maxEntries,
                    haddFileName=haddFileName) #If not None <-> final outputfile name (after running 'haddnano.py')

    print(opt.workingdir)
    p.run() #Run the PostProcessor code

    print(colors.bold + colors.fg.orange + '\n... DONE !' + colors.reset)

    #-- Manual copy of output files (not used) #NB: noticed some files got truncated (size/time job limitations ?)
    '''
    for name in glob.glob('./*.root'):
        print(name)
        outname = '/afs/cern.ch/work/n/ntonon/public/VBFphoton/CMSSW_10_2_27/src/UserCode/VJJSkimmer/scripts/'+haddFileName
        print('MANUAL COPY FROM: ', name, ' TO: ', outname)
    copyfile(name, outname)
    '''

    return


# //--------------------------------------------
# //--------------------------------------------

if __name__ == "__main__":

    #print(sys.argv)

    main()
