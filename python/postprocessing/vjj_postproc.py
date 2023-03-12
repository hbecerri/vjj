#!/usr/bin/env python
import os, sys
import ROOT
import argparse
ROOT.PyConfig.IgnoreCommandLineOptions = True
from importlib import import_module
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from UserCode.VJJSkimmer.postprocessing.modules.VJJSelector import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.countHistogramsModule import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.puWeightProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.muonScaleResProducer import *
from UserCode.VJJSkimmer.postprocessing.modules.VJJEvent import _defaultObjCfg
from UserCode.VJJSkimmer.postprocessing.modules.MuonSelector import *
from UserCode.VJJSkimmer.postprocessing.modules.ElectronSelector import *
from UserCode.VJJSkimmer.postprocessing.modules.PhotonSelector import *
from UserCode.VJJSkimmer.postprocessing.modules.JetSelector import *
from UserCode.VJJSkimmer.postprocessing.etc.testDatasets import getTestDataset, getTestCIDir
from UserCode.VJJSkimmer.samples.Sample import SampleNameParser
from UserCode.VJJSkimmer.samples.Manager import currentSampleList as samples
from UserCode.VJJSkimmer.postprocessing.helpers.ColoredPrintout import *

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

def PrintBanner(year):
    '''
    Print some info when starting this code
    '''

    print('\n' + colors.bg.orange + '                                           ' + colors.reset)
    print(colors.fg.orange + '\n--- Running VJJSelector (via vjj_postproc.py) ---' + colors.reset + '\n')
    # print('* NB1: xxx')
    print(colors.bg.orange + '                                           ' + colors.reset + '\n')

    print('== YEAR: ', year)

    return


def defineModules(year, isData, isSignal, fs, preVFP=False):
    """
    Configures the modules to be run depending on the year and whether is data or MC
    Returns a list of modules
    """

    if isData and isSignal:
        raise ValueError('isData and isSignal can not be True at the same time')

    modules=[]
    modules.append( {2016:muonScaleRes2016 , 2017:muonScaleRes2017 , 2018:muonScaleRes2018}[year]() )

    options = { 'vpf' : '' if year != 2016 else 'pre' if preVFP else 'post'   }
    print('options ',options) 
    modules.extend( [
                    countHistogramsModule(),
                    MuonSelector( year ) ,
                    ElectronSelector( era = year , **options ),
                    PhotonSelector( year , apply_id = True , cfg=_defaultObjCfg, vetoObjs = [("Muon", "mu"), ("Electron", "ele")] , **options ),
                    PhotonSelector( year , apply_id = False , cfg=_defaultObjCfg, vetoObjs = [("Muon", "mu"), ("Electron", "ele")] , **options ),
#                    JetSelector( year , _defaultObjCfg, apply_id=True ),
#                    JetSelector( year , _defaultObjCfg, apply_id=False ),
#                    JetSelector( year , _defaultObjCfg, applyPUid=True ),
                    JetSelector( year , _defaultObjCfg, applyPUid=False ),
                    VJJSelector(isData , year , signal=isSignal, finalState = fs)] )

    if not isData:
        modules.append( {2016:puWeight_UL2016 , 2017:puWeight_UL2017 , 2018:puWeight_UL2018}[year]() )

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

# //--------------------------------------------
    #parse command line
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-y', '--year',       dest='year',   help='year',  choices=[2016,2017,2018], default=-1,  type=int)
    parser.add_argument('-p', '--FPV',        dest='fpv',    help='for 2016 pixel, pre or post FPV',  default=False, action='store_true')
    parser.add_argument(      '--isData',     dest='isData', help='data?', default=False, action='store_true')
    parser.add_argument(      '--isSignal',   dest='isSignal', help='signal?', default=False, action='store_true')
    parser.add_argument('-i', '--inputfiles', dest='inputFiles',   help='input, should be set to crab to run on GRID', type=str,
                        default='auto')
    parser.add_argument('-k', '--keep_and_drop', dest='keep_and_drop',   help='keep and drop', type=str,
                        default='{0}/python/UserCode/VJJSkimmer/postprocessing/etc/keep_and_drop.txt'.format( os.getenv('CMSSW_BASE' , '.') ) )
    parser.add_argument('-ok', '--output_keep_and_drop', dest='output_keep_and_drop',   help='output keep and drop', type=str,
                        default='{0}/python/UserCode/VJJSkimmer/postprocessing/etc/output_keep_and_drop.txt'.format( os.getenv('CMSSW_BASE' , '.') ) )
    parser.add_argument('-N', '--maxEntries', dest='maxEntries',   help='max. entries to process', type=int,
                        default=None)
    parser.add_argument('-f', '--firstEntry', dest='firstEntry',   help='first entry to process', type=int,
                        default=0)
    parser.add_argument('-d', '--localCIDir',     dest='localCIDir',   help='local CI directory',  default=getTestCIDir(), type=str)
    parser.add_argument('-S', '--finalState',     dest='finalState',   help='photon:22, fake photon:-22, mm: 169, ee:121',  default=0, type=int)
    parser.add_argument('-D', '--dataSet',     dest='dataSet',   help='dataset name to run on, setting it overrides "year", "data" and "isSignal" values.',  default=None, type=str)
# //--------------------------------------------

# //--------------------------------------------
    opt, unknownargs = parser.parse_known_args() #job number is passed by crab as the first argument and shouldn't be parsed here

    if opt.dataSet:
        s = SampleNameParser()
        _, info = s.parse( opt.dataSet )
        if 'year' in info.keys():
            opt.year = 2000 + int( info[ 'year' ] )
            opt.isData = 'isData' in info.keys()
            opt.isSignal = samples.is_signal( opt.dataSet )
            opt.fpv = 'prevfp' in info.keys()
            print( 'dataset name is {0}'.format( opt.dataSet ) )
            print( 'year, isData, preVFP and isSignal are set from the dataset name to {0}, {1}, {2} and {3}'.format( opt.year , opt.isData , opt.fpv, opt.isSignal ) )
        else:
            raise ValueError( 'dataSet name seems inconsistent: {0}'.format( opt.dataSet ) )
        

    if opt.year == None: raise ValueError('Must set year !')
    if opt.finalState == None: raise ValueError('Must set the final state. Use --help for the options.') 
    if opt.finalState not in [22, -22, 169, 121]: raise ValueError('Non standard value for final state. Use --help for the options.') 

    PrintBanner(opt.year) #Print banner in terminal

    crab = False
    inputFiles = []
    if opt.inputFiles == "auto":
        inputFiles = [getTestDataset(opt.year, opt.isData, fromLocalCIDir=opt.localCIDir)]
    elif opt.inputFiles == "crab":
        import PhysicsTools.NanoAODTools.postprocessing.framework.crabhelper as nano_crab
        inputFiles = nano_crab.inputFiles()
        crab = True
    else:
        inputFiles=opt.inputFiles.split(',')

    #-- Set input files
    print(colors.fg.lightblue + '\n== Processing following files:' + colors.reset)
    for i in inputFiles: print(i)

    fwkJobReport=False
    haddFileName = None
    if crab:
        fwkJobReport=True
        haddFileName = 'out.root'
# //--------------------------------------------

# //--------------------------------------------
    #-- Define modules to run
    modules=defineModules(opt.year,opt.isData, opt.isSignal, opt.finalState, opt.fpv)
    # print('My modules: ', mymodules)
    #call post processor
    p=PostProcessor(outputDir=".",
                    inputFiles=inputFiles,
                    cut=None,
                    branchsel=opt.keep_and_drop,
                    modules=modules,
                    provenance=True,
                    justcount=False,
                    fwkJobReport=fwkJobReport,
                    noOut=False,
                    outputbranchsel = opt.output_keep_and_drop,
                    maxEntries=opt.maxEntries,
                    firstEntry=opt.firstEntry,
                    haddFileName = haddFileName)

    p.run()
# //--------------------------------------------


# //--------------------------------------------
# //--------------------------------------------


if __name__ == "__main__":

    main()
