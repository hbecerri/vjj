#! /usr/bin/env python
import os
import argparse
from collections import OrderedDict
from UserCode.VJJSkimmer.samples.Manager import currentSampleList 
from UserCode.VJJSkimmer.samples.campaigns.Manager import Manager as CampaignManager
from UserCode.VJJSkimmer.postprocessing.vjj_final_postpro import make_hadd_fname, get_fileNames

import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True


def main():

    #parse command line
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--campaign',     dest='campaign',   help='campaign',  default=None, type=str)
    parser.add_argument('--nfilesperchunk',     dest='nfilesperchunk',   help='number of files to run on',  default=1, type=int)
    parser.add_argument('--baseoutdir' , dest='baseoutdir' , help='the base directory to write output fiels' , default= '/eos/cms/store/cmst3/group/top/SMP-19-005' , type=str )
    parser.add_argument('-o' , '--outdir',     dest='outdir',   help='output directory name. it will be added at the end of the baseoutdir',  default='Skimmed', type=str)
    parser.add_argument('-l', '--logdir',     dest='logdir',   help='logdir',  default='SkimmerCondor', type=str)
    parser.add_argument('--flavour', dest='flavour',   help='job-flavour',  default='8nh' , choices=['8nm' , '1nh' , '8nh' , '1nd' , '2nd' , '1nw' , '2nw'], type=str)
    parser.add_argument('--outfilename', dest='outfilename',   help='the name of the submit file',  default='vjj_finalSkimmer.submit' , type=str)
    parser.add_argument('--includeexistingfiles', dest='includeexistingfiles',   help='ignore if an output file exists and resubmit the job',  default=False , action='store_true')
    parser.add_argument('--splitjobs', dest='splitjobs',   help='set nfilesperchunk=1 and run for the remaining jobs',  default=False , action='store_true')
    parser.add_argument('--neventsperjob', dest='neventsperjob',   help='set nevents per job, only if splitjobs is set',  default=-1 , type=int)


    opt, unknownargs = parser.parse_known_args()

    campaign = None
    if opt.campaign:
        campaign = CampaignManager( opt.campaign )
    else:
        raise ValueError( 'please specify campaign name you want to run using -c option')
    
    jobFlavours = { '8nm':'espresso' ,
                    '1nh':'microcentury',
                    '8nh':'longlunch',
                    '1nd':'workday',
                    '2nd':'tomorrow',
                    '1nw':'testmatch',
                    '2nw':'nextweek' }

    if not os.path.exists( opt.logdir ):
        os.makedirs( opt.logdir )

    condor = []

    step_par_name = 'Step' if opt.includeexistingfiles else 'chunkid'
    full_outdir = '{2}/{0}/{1}/'.format( opt.campaign , opt.outdir , opt.baseoutdir )
    total_existing_files = 0
    total_jobs = 0
    total_jobs_with_no_input = 0

    actual_nfilesperchunk = 1 if opt.splitjobs else opt.nfilesperchunk
    print(actual_nfilesperchunk)

    condor.append( ('executable' , '{0}/vjj_finalSkimmer.sh'.format(os.getcwd()) ) )
    if opt.neventsperjob > 0 :
        condor.append( ('arguments','-c {3} -d $(DATASET) --nfilesperchunk {0} --chunkindex $({1}) -o {2} -N {4} -f $(FIRSTEVENT)'.format(actual_nfilesperchunk , step_par_name , full_outdir , opt.campaign , opt.neventsperjob )))
    else:
        condor.append( ('arguments','-c {3} -d $(DATASET) --nfilesperchunk {0} --chunkindex $({1}) -o {2}'.format(actual_nfilesperchunk , step_par_name , full_outdir , opt.campaign)))
    condor.append( ('output','{0}/$(ClusterId).$(ProcId).out'.format(opt.logdir)))
    condor.append( ('error','{0}/$(ClusterId).$(ProcId).err'.format(opt.logdir)))
    condor.append( ('log','{0}/$(ClusterId).log'.format(opt.logdir)))
    condor.append( ('+JobFlavour',jobFlavours[opt.flavour]))
    condor.append( ('transfer_executable',False))
    condor.append( ('requirements','( (OpSysAndVer =?= "CentOS7") || (OpSysAndVer =?= "SLC6") )'))
    #condor.append( ('should_transfer_files' , 'NO') )
    condor.append( ('stream_output' , True ) )
    condor.append( ('stream_error' , True ) )
    condor.append( ('WHEN_TO_TRANSFER_OUTPUT' , 'ON_EXIT_OR_EVICT' ) )

    for s,info in currentSampleList.all_datasets():
        totalFiles = len( campaign.get_dataset_info(s)['files'] )
        nsteps = totalFiles/opt.nfilesperchunk if totalFiles%opt.nfilesperchunk==0 else 1+totalFiles/opt.nfilesperchunk
        if opt.includeexistingfiles:
            condor.append( ('queue' ,  nsteps , s ) )
            total_jobs += condor[-1][1]
        else:
            filesToRun = []
            for step in range( nsteps ):
                _,exists = make_hadd_fname( full_outdir , s , opt.nfilesperchunk , step )
                if not exists:
                    try:
                        inputfilenames = get_fileNames(campaign , s , opt.nfilesperchunk , step )
                        if opt.splitjobs:
                            for i in range( opt.nfilesperchunk ):
                                newjobindex = step*opt.nfilesperchunk+i
                                if opt.neventsperjob != -1:
                                    fIn = ROOT.TFile.Open( inputfilenames[0] )
                                    tIn = fIn.Get("Events")
                                    ntotalevents = tIn.GetEntries()
                                    for start in range(0, ntotalevents , opt.neventsperjob ):
                                        _,exists1 = make_hadd_fname( full_outdir , s , 1 , newjobindex , start , opt.neventsperjob )
                                        if not exists1:
                                            filesToRun.append( [newjobindex , start] )
                                else:
                                    _,exists1 = make_hadd_fname( full_outdir , s , 1 , newjobindex )
                                    if not exists1:
                                        filesToRun.append( newjobindex )
                        else:
                            filesToRun.append( step )
                    except:
                        print( "input files for {0} / {1} / step: {2} can not be fetched (total={3})".format( opt.campaign , s , step , totalFiles ) )
                        total_jobs_with_no_input += 1
                else:
                    total_existing_files += 1
            condor.append( ('queue_list' , filesToRun , s ) )
            total_jobs += len( filesToRun )
    added_samples = []
    print(opt.outfilename)
    with open( opt.outfilename , 'w') as f:
        available_nqueues = []
        for l in condor:
            if l[0] == 'queue' and opt.includeexistingfiles:
                available_nqueues.append( l[1] )
            elif l[0] == 'queue_list':
                continue
            else:
                f.write( '{0:20s}= {1}\n'.format( l[0] , l[1] ) )
        if opt.includeexistingfiles:
            for lqueue in sorted( set(available_nqueues) , reverse=True ):
                f.write( 'queue {0} DATASET from (\n'.format( lqueue ) )
                for ll in condor:
                    if ll[0] == 'queue' and ll[1] == lqueue:
                        if ll[2] in added_samples:
                            continue
                        f.write( '\t{0}\n'.format( ll[2] ) )
                        added_samples.append( ll[2] )
                f.write( ")\n" )
        else:
            if opt.neventsperjob < 0 :
                f.write( 'queue DATASET,{0} from (\n'.format( step_par_name ) )
                for l in condor:
                    if l[0] == 'queue_list':
                        for index in l[1]:
                            f.write('\t{0} {1}\n'.format( l[2] , index ) )
            else:
                f.write( 'queue DATASET,{0},FIRSTEVENT from (\n'.format( step_par_name ) )
                for l in condor:
                    if l[0] == 'queue_list':
                        for index in l[1]:
                            f.write('\t{0} {1} {2}\n'.format( l[2] , index[0] , index[1] ) )

            f.write( ')\n' )
    print('In total, {0} jobs will be submitted. The output of {1} files already exists. They are skipped'.format( total_jobs , total_existing_files ) )
    print('{0} jobs skipped, because the input files can not be found'.format( total_jobs_with_no_input ) )
    print( 'run `condor_submit {0}` to submit jobs'.format( opt.outfilename ) )

if __name__ == "__main__":

    main()

                                
                                
