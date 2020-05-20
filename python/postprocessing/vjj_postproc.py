#!/usr/bin/env python
import os, sys
import ROOT
import optparse
ROOT.PyConfig.IgnoreCommandLineOptions = True
from importlib import import_module
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from UserCode.VJJSkimmer.postprocessing.modules.VJJSelector import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.PrefireCorr import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.puWeightProducer import *

def defineModules(year,isData):

    modules=[]
    if not isData:
        if year==2016:
            modules.append( puAutoWeight_2016() )
            modules.append( PrefCorr() )
            modules.append( PrefCorr(jetroot="L1prefiring_jetpt_2016BtoH.root",
                                     jetmapname="L1prefiring_jetpt_2016BtoH",
                                     photonroot="L1prefiring_photonpt_2016BtoH.root",
                                     photonmapname="L1prefiring_photonpt_2016BtoH.root") )
            modules.append( vjjSkimmer2016mc() )
        if year==2017:
            modules.append( puAutoWeight_2017() )
            modules.append( PrefCorr(jetroot="L1prefiring_jetpt_2017BtoF.root",
                                     jetmapname="L1prefiring_jetpt_2017BtoF",
                                     photonroot="L1prefiring_photonpt_2017BtoF.root",
                                     photonmapname="L1prefiring_photonpt_2017BtoF") )
            modules.append( vjjSkimmer2017mc() )
        if year==2018:
            modules.append( puAutoWeight_2018() )
            modules.append( vjjSkimmer2018mc() )

    else:
        if year==2016:
            modules.append( vjjSkimmer2016data() )
        if year==2017:
            modules.append( vjjSkimmer2016data() )
        if year==2018:
            modules.append( vjjSkimmer2018data() )

    return modules

def vjj_postproc(opt,args):

    """ build the command to run based on the options """

    #start by defining modules to run
    modules=defineModules(opt.year,opt.isData)

    #call post processor
    p=PostProcessor(outputDir=".",
                    inputFiles=opt.inputFiles.split(','),
                    cut=None,
                    branchsel=None,
                    modules=modules,
                    provenance=True,
                    justcount=False,
                    fwkJobReport=False,
                    noOut=False,
                    outputbranchsel = opt.keep_and_drop,
                    maxEntries=opt.maxEntries,
                    firstEntry=opt.firstEntry)

    p.run()



def main():

    #parse command line
    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)
    parser.add_option('-y', '--year',       dest='year',   help='year [%default]',  default=2017,  type=int)
    parser.add_option(      '--isData',     dest='isData', help='data? [%default]', default=False, action='store_true')
    parser.add_option('-i', '--inputfiles', dest='inputFiles',   help='input [%default]', type='string',
                      default='45CA9950-BD37-374A-8604-AC35C9446A0F.root')
    parser.add_option('-k', '--keep_and_drop', dest='keep_and_drop',   help='keep and drop [%default]', type='string',
                      default='python/postprocessing/etc/keep_and_drop.txt')
    parser.add_option('-N', '--maxEntries', dest='maxEntries',   help='max. entries to process [%default]', type=int,
                      default=None)
    parser.add_option('-f', '--firstEntry', dest='firstEntry',   help='first entry to process [%default]', type=int,
                      default=0)
    (opt, args) = parser.parse_args()

    vjj_postproc(opt,args)


if __name__ == "__main__":

    main()
