#! /usr/bin/env python
import os, sys
import ROOT
import argparse
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
from UserCode.VJJSkimmer.postprocessing.etc.testDatasets import getTestDataset, getTestCIDir
from UserCode.VJJSkimmer.samples.Sample import *


def defineModules(year,isData):

    """
    configures the modules to be run depending on the year and whether is data or MC
    returns a list of modules
    """

    modules=[]
    if not isData:
        if year==2016:
            modules.append( puAutoWeight_2016() )
            modules.append( PrefCorr() )
            modules.append( PrefCorr(jetroot="L1prefiring_jetpt_2016BtoH.root",
                                     jetmapname="L1prefiring_jetpt_2016BtoH",
                                     photonroot="L1prefiring_photonpt_2016BtoH.root",
                                     photonmapname="L1prefiring_photonpt_2016BtoH") )
            modules.extend( [muonSelector2016(), electronSelector2016(), photonSelector2016(), jetSelector2016() ])
            modules.append( vjjSkimmer2016mc() )
        if year==2017:
            modules.append( puAutoWeight_2017() )
            modules.append( PrefCorr(jetroot="L1prefiring_jetpt_2017BtoF.root",
                                     jetmapname="L1prefiring_jetpt_2017BtoF",
                                     photonroot="L1prefiring_photonpt_2017BtoF.root",
                                     photonmapname="L1prefiring_photonpt_2017BtoF") )
            modules.extend( [muonSelector2017(), electronSelector2017(), photonSelector2017(), jetSelector2017() ])
            modules.append( vjjSkimmer2017mc() )
        if year==2018:
            modules.append( puAutoWeight_2018() )
            modules.extend( [muonSelector2018(), electronSelector2018(), photonSelector2018(), jetSelector2018() ])
            modules.append( vjjSkimmer2018mc() )

    else:
        if year==2016:
            modules.extend( [muonSelector2016(), electronSelector2016(), photonSelector2016(), jetSelector2016() ])
            modules.append( vjjSkimmer2016data() )
        if year==2017:
            modules.extend( [muonSelector2017(), electronSelector2017(), photonSelector2017(), jetSelector2017() ])
            modules.append( vjjSkimmer2017data() )
        if year==2018:
            modules.extend( [muonSelector2018(), electronSelector2018(), photonSelector2018(), jetSelector2018() ])
            modules.append( vjjSkimmer2018data() )

    return modules


def vjj_postproc(opt, crab = False):
    
    """steers the VJJ analysis"""

    #start by defining modules3 to run
    modules=defineModules(opt.year,opt.isData)

    fwkJobReport=False
    haddFileName = None
    if crab:
        fwkJobReport=True
        haddFileName = 'out.root'

    #call post processor
    p=PostProcessor(outputDir=".",
                    inputFiles=opt.inputFiles,
                    cut=None,
                    branchsel=None,
                    modules=modules,
                    provenance=True,
                    justcount=False,
                    fwkJobReport=fwkJobReport,
                    noOut=False,
                    outputbranchsel = opt.keep_and_drop,
                    maxEntries=opt.maxEntries,
                    firstEntry=opt.firstEntry,
                    haddFileName = haddFileName)

    p.run()



def main():

    #parse command line
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-y', '--year',       dest='year',   help='year',  default=2017,  type=int)
    parser.add_argument(      '--isData',     dest='isData', help='data?', default=False, action='store_true')
    parser.add_argument('-i', '--inputfiles', dest='inputFiles',   help='input, should be set to crab to run on GRID', type=str,
                        default='auto')
    parser.add_argument('-k', '--keep_and_drop', dest='keep_and_drop',   help='keep and drop', type=str,
                        default='{0}/python/UserCode/VJJSkimmer/postprocessing/etc/keep_and_drop.txt'.format( os.getenv('CMSSW_BASE' , '.') ) )
    parser.add_argument('-N', '--maxEntries', dest='maxEntries',   help='max. entries to process', type=int,
                        default=None)
    parser.add_argument('-f', '--firstEntry', dest='firstEntry',   help='first entry to process', type=int,
                        default=0)
    parser.add_argument('-d', '--localCIDir',     dest='localCIDir',   help='local CI directory',  default=getTestCIDir(), type=str)
    parser.add_argument('-D', '--dataSet',     dest='dataSet',   help='dataset name to run on, setting it overrides "year" and "data" values.',  default=None, type=str)

    opt, unknownargs = parser.parse_known_args() #job number is passed by crab as the first argument and shouldn't be parsed here


    if opt.dataSet:
        s = SampleNameParser()
        _, info = s.parse( opt.dataSet )
        if 'year' in info.keys():
            opt.year = 2000 + int( info[ 'year' ] )
            opt.isData = 'isData' in info.keys()
            print( 'dataset name is {0}'.format( opt.dataSet ) )
            print( 'year, isData are set from the dataset name to {0} and {1}'.format( opt.year , opt.isData ) )
        else:
            raise ValueError( 'dataSet name seems inconsistent: {0}'.format( opt.dataSet ) )

    crab = False
    if opt.inputFiles == "auto":
        opt.inputFiles = [getTestDataset(opt.year, opt.isData, fromLocalCIDir=opt.localCIDir)]
    elif opt.inputFiles == "crab":
        import PhysicsTools.NanoAODTools.postprocessing.framework.crabhelper as nano_crab
        opt.inputFiles = nano_crab.inputFiles()
        crab = True
    else:
        opt.inputFiles=opt.inputFiles.split(',')

    vjj_postproc(opt , crab)


if __name__ == "__main__":

    main()
