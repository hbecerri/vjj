#! /usr/bin/env python
import os
import json
import argparse
from collections import OrderedDict
from UserCode.VJJSkimmer.samples.Sample import Sample
from UserCode.VJJSkimmer.samples.Manager import currentSampleList 
from UserCode.VJJSkimmer.samples.campaigns.Manager import Manager as CampaignManager
from UserCode.VJJSkimmer.postprocessing.vjj_final_postpro import make_hadd_fname, get_fileNames
import ROOT

corruptedFiles = []
nonExistingFiles = []

def FinalSummary( sample , outdir , len_parent_files , nfilesperchunk ):
    ret = {'total':0 , 'size':0 , 'files':{} , 'filestat':{'nFile':0 ,'nOkFiles':0 ,  'nFilesWithError':0 , 'nFilesWithNoHisto':0 , 'nNoneFiles':0 , 'nNotExisting':0}}
    nsteps = len_parent_files/nfilesperchunk if len_parent_files%nfilesperchunk==0 else 1+len_parent_files/nfilesperchunk
    allfiles = [ "{0}/{1}/{2}/Skimmed_{3}_{4}.root".format( outdir , sample.year() , sample.makeUniqueName() , nfilesperchunk , i ) for i in range(nsteps) ]
    for f in allfiles:
        ret['filestat']['nFile'] += 1
        if os.path.exists( f ):
            fo = None
            try:
                fo = ROOT.TFile.Open( f )
            except:
                ret['files'][f] = 'error while openning the file'
                ret['filestat']['nFilesWithError'] += 1
                corruptedFiles.append( f )
            if fo :
                cutflow = fo.Get('cutflow') if sample.isData() else fo.Get('wgtSum')
                if cutflow:
                    bin_zero = cutflow.FindBin( 0.5 )
                    yields = cutflow.GetBinContent( bin_zero )
                    size = fo.GetSize()
                    ret['files'][f] = (yields,size)
                    ret['total'] += yields
                    ret['size'] += size
                    ret['filestat']['nOkFiles'] += 1
                else:
                    ret['files'][f] = 'no wgtSum/cutflow histo available'
                    ret['filestat']['nFilesWithNoHisto'] += 1
                    corruptedFiles.append( f )
                fo.Close()
            else:
                ret['files'][f] = 'file is None'
                ret['filestat']['nNoneFiles'] += 1
                corruptedFiles.append( f )
        else:
            ret['files'][f] = 'does not exist'
            ret['filestat']['nNotExisting'] += 1
            nonExistingFiles.append( f )

    return ret


def main():
    #parse command line
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--parentcampaign',     dest='parentcampaign',   help='name of the parent campaign',  default=None, type=str)
    parser.add_argument('-o' , '--outdir',     dest='outdir',   help='output directory, $TOP_CMG_AREA/SMP-19-005/$campaign/$outdir/',  default='Skimmed', type=str)
    parser.add_argument('--nfilesperchunk',     dest='nfilesperchunk',   help='number of files to run on',  default=1, type=int)

    opt, unknownargs = parser.parse_known_args()

    parentcampaign = None
    if opt.parentcampaign:
        parentcampaign = CampaignManager( opt.parentcampaign )
    else:
        raise ValueError( 'please specify the parent campaign name you want to run using -c option')
    
    full_outdir = '/eos/cms/store/cmst3/group/top/SMP-19-005/{0}/{1}/'.format( opt.parentcampaign , opt.outdir )

    outjs = {}
    outjs['generalInfo'] = {'parentcampaign':opt.parentcampaign}
    completedSamples = []
    incompletesamples = []
    for ds,info in currentSampleList.all_datasets():
        #print('get information for ds {0}'.format( ds ) )
        s = Sample(ds)
        outjs[ds] = FinalSummary( s , full_outdir , len( parentcampaign.get_dataset_info(ds)['files'] ) , opt.nfilesperchunk )

        if parentcampaign.js[ ds ]['total'] != outjs[ds]['total']:
            print( 'Warning: some events are missing in {0}, {1} events are in parent while {2} event processed in skimmed'.format( s.makeUniqueName() , parentcampaign.js[ ds ]['total'] , outjs[ds]['total'] ) )
            outjs[ds]['complete']=False
            incompletesamples.append( ds )
        else:
            outjs[ds]['complete']=True
            completedSamples.append( ds )
        if outjs[ds]['filestat']['nFile'] == 0:
            print( 'Warning: no file is available for {0}'.format( s.makeUniqueName() ) )
            print( '\there is the summary : {0}'.format( outjs[ds]['filestat'] ) )
        
        #print outjs
    with open('campaign.json' , 'w') as f :
        json.dump( outjs ,  f )

    print('------------------------------------')
    print('List of existing corrupted files ({0}):'.format(len(corruptedFiles) ) )
    print(' '.join( corruptedFiles ) )
    print('------------------------------------')
    print('List of non existing files ({0}):'.format(len(nonExistingFiles) ) )
    print(' '.join( nonExistingFiles ) )
    print('------------------------------------')
    print('List of incomplete samples ({0}):'.format(len(incompletesamples) ) )
    print('\n'.join( incompletesamples ) )


if __name__ == "__main__":

    main()

