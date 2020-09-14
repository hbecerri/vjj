#! /usr/bin/env python
import os, sys
import ROOT
import argparse
ROOT.PyConfig.IgnoreCommandLineOptions = True
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from UserCode.VJJSkimmer.postprocessing.modules.VJJSkimmer import *
from UserCode.VJJSkimmer.samples.campaigns.Manager import Manager as CampaignManager
from UserCode.VJJSkimmer.samples.Sample import Sample

def make_hadd_fname(outdir, ds, nfilesperchunk, chunkindex , fromevent = None , nEvents = None ):
    s = Sample(ds)
    outdir = '{0}/{1}/{2}/'.format( outdir , s.year() , s.makeUniqueName() )
    if not os.path.exists( outdir ):
        os.makedirs( outdir )
    if fromevent and nEvents:
        haddFileName = "{0}/Skimmed_{1}_{2}_f{3}_n{4}.root".format( outdir , nfilesperchunk , chunkindex , fromevent , nEvents )
    else:
        haddFileName = "{0}/Skimmed_{1}_{2}.root".format( outdir , nfilesperchunk , chunkindex )
    return haddFileName, os.path.exists(haddFileName)

def get_fileNames( campaign , ds , nfilesperchunk , chunkindex ):

    all_inputFiles = campaign.get_dataset_info( ds )['files']
    chunks = [ all_inputFiles[a:a+nfilesperchunk] for a in range( 0 , len(all_inputFiles) , nfilesperchunk ) ]
    print(ds,nfilesperchunk,chunkindex,len(all_inputFiles) , len(chunks) )
    inputFiles = chunks[ chunkindex ]
    return inputFiles

def main():

    #parse command line
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-N', '--maxEntries', dest='maxEntries',   help='max. entries to process', type=int,
                        default=None)
    parser.add_argument('-d', '--dataSet',     dest='dataSet',   help='dataset name to skim',  default=None, type=str)
    parser.add_argument('-c', '--campaign',     dest='campaign',   help='campaign',  default=None, type=str)
    parser.add_argument('--chunkindex',     dest='chunkindex',   help='chunk the file list into sub-lists with size=nfilesperchunk and selects #chunkindex to run on',  default = None, type=int)
    parser.add_argument('--nfilesperchunk',     dest='nfilesperchunk',   help='number of files to run on',  default=1, type=int)
    parser.add_argument('--workingdir',     dest='workingdir',   help='where to store individual files',  default='./', type=str)
    parser.add_argument('-o' , '--outdir',     dest='outdir',   help='output directory',  default='./', type=str)
    parser.add_argument('-f', '--firstEntry', dest='firstEntry',   help='first entry to process', type=int, default=0)

    opt, unknownargs = parser.parse_known_args()
    keep_drop = '{0}/python/UserCode/VJJSkimmer/postprocessing/etc/skimmer_keep_and_drop.txt'.format( os.getenv('CMSSW_BASE' , '.') )

    campaign = None
    if opt.campaign:
        campaign = CampaignManager( opt.campaign )
    else:
        raise ValueError( 'please specify campaign name you want to run using -c option')
        
    print( campaign.AllInfo[2016].keys() )
    module = None
    inputFiles = None
    if opt.dataSet:
        module = VJJSkimmer( opt.dataSet , campaign )
        inputFiles = get_fileNames( campaign , opt.dataSet , opt.nfilesperchunk , opt.chunkindex )
    else:
        raise ValueError('please specify dataset name using -d option')


    if opt.firstEntry :
        haddFileName, exists = make_hadd_fname(opt.outdir, opt.dataSet, opt.nfilesperchunk, opt.chunkindex , opt.firstEntry , opt.maxEntries)
    else:
        haddFileName, exists = make_hadd_fname(opt.outdir, opt.dataSet, opt.nfilesperchunk, opt.chunkindex)
    print( 'processing following files:')
    for i in inputFiles:
        print( i )
    print( 'creating output file:' )
    print(haddFileName )
    if exists:
        print("the output file already exists, it will be overwritten : {0}".format( haddFileName ) )
    #call post processor
    p=PostProcessor(outputDir=opt.workingdir,
                    inputFiles=inputFiles,
                    cut=None,
                    branchsel=None,
                    modules=[module],
                    provenance=True,
                    justcount=False,
                    fwkJobReport=False,
                    noOut=False,
                    outputbranchsel = keep_drop,
                    firstEntry=opt.firstEntry,
                    maxEntries=opt.maxEntries,
                    haddFileName = haddFileName)

    p.run()


if __name__ == "__main__":
    print(sys.argv)
    main()
