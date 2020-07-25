#! /usr/bin/env python
import os, sys
import ROOT
import argparse
ROOT.PyConfig.IgnoreCommandLineOptions = True
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from UserCode.VJJSkimmer.postprocessing.modules.VJJSkimmer import *
from UserCode.VJJSkimmer.samples.campaign.Manager import Manager as CampaignManager

def main():

    #parse command line
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-N', '--maxEntries', dest='maxEntries',   help='max. entries to process', type=int,
                        default=None)
    parser.add_argument('-d', '--dataSet',     dest='dataSet',   help='dataset name to skim',  default=None, type=str)
    parser.add_argument('-c', '--campaign',     dest='campaign',   help='campaign',  default=None, type=str)
    parser.add_argument('--chunkindex',     dest='chunkindex',   help='chunk the file list into sub-lists with size=nfilesperchunk and selects #chunkindex to run on',  default = None, type=int)
    parser.add_argument('--nfilesperchunk',     dest='nfilesperchunk',   help='number of files to run on',  default=1, type=int)
    parser.add_argument('-o' , '--outdir',     dest='outdir',   help='output directory',  default='./', type=str)
    

    opt, unknownargs = parser.parse_known_args()
    keep_drop = '{0}/python/UserCode/VJJSkimmer/postprocessing/etc/skimmer_keep_and_drop.txt'.format( os.getenv('CMSSW_BASE' , '.') )

    campaign = None
    if opt.campaign:
        campaign = CampaignManager( opt.campaign )
    else:
        raise ValueError( 'please specify campaign name you want to run using -c option')
        
    module = None
    inputFiles = None
    if opt.dataSet:
        module = VJJSkimmer( opt.dataSet )
        all_inputFiles = campaign.get_dataset_info( opt.dataSet )['files']
        chunks = [ all_inputFiles[a:a+opt.nfilesperchunk] for a in range( 0 , len(all_inputFiles) , opt.nfilesperchunk ) ]
        inputFiles = chunks[ opt.chunkindex ]
    else:
        raise ValueError('please specify dataset name using -d option')

    haddFileName = "Skimmed_{0}_{1}_{2}.root".format( module.sample.makeUniqueName() , opt.nfilesperchunk , opt.chunkindex )
    #call post processor
    p=PostProcessor(outputDir=opt.outdir,
                    inputFiles=inputFiles,
                    cut=None,
                    branchsel=None,
                    modules=[module],
                    provenance=True,
                    justcount=False,
                    fwkJobReport=False,
                    noOut=False,
                    outputbranchsel = keep_drop,
                    maxEntries=opt.maxEntries,
                    haddFileName = haddFileName)

    p.run()


if __name__ == "__main__":

    main()
