'''
Create the HTCondor submit script to submit Skimmer jobs

# jobFlavours = { '8nm':'espresso' , #20m
#                 '1nh':'microcentury', #1h
#                 '8nh':'longlunch', #2h
#                 '1nd':'workday', #1d
#                 '2nd':'tomorrow', #2d
#                 '1nw':'testmatch', #1w
#                 '2nw':'nextweek' } #2w
'''

#! /usr/bin/env python
import os
import argparse
from collections import OrderedDict
from UserCode.VJJSkimmer.samples.Sample import Sample
from UserCode.VJJSkimmer.samples.Manager import currentSampleList
from UserCode.VJJSkimmer.samples.campaigns.Manager import Manager as CampaignManager
from UserCode.VJJSkimmer.postprocessing.vjj_VJJSkimmerJME_postproc import make_hadd_fname, get_fileNames
from datetime import datetime
from UserCode.VJJSkimmer.postprocessing.helpers.ColoredPrintout import *

import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

# //--------------------------------------------
# //--------------------------------------------

#-- Define samples to process #Empty <-> will process all datasets; ['a','b'] <-> will process only datasets whose names contain (a || b)

#Data samples
DATAsamples = ['SinglePhoton', 'DoubleEG', 'DoubleMuon', 'EGamma',"Photon"]

#MC samples
MCsamples = ['GJets_SM_5f', #Signal
    'GJets_SM_4f',
    'GJets_Pt', #GJetsSherpa (NLO 2016)
    'G1Jet_LHEGpT', #GJetsLO
    #'GJets_Pt-20To100','GJets_Pt-100To200','GJets_Pt-200To500','GJets_Pt-500To1000','GJets_Pt-1000To2000','GJets_Pt-2000To5000', #GJetsSherpaHighStat (2016) 
    #'GJets_Mjj', #SignalMGPythia500
    'ToLL_0J','ToLL_1J','ToLL_2J','DY1JetsToLL','DY2JetsToLL','DY3JetsToLL','DY4JetsToLL','DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX','DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8', #DY
    'DiPhoton', #DiPhoton
    'WJetsToLNu', 'WJetsToQQ_HT', #WJets
    'QCD_Pt', #QCD
    'LLJJ', #LLJJ
    'TTTo2L2Nu', #ttbar
    'TTGJets', #ttgamma
    'ZGTo2LG',
    'WGToLNuG',
    'LNuAJJ',
    'ST_s',
    'ST_t'
]

#-- Empty <-> will process all years; [a,b] <-> will process only datasets corresponding to years (a || b)
#NB: gets overridden by arg --year
years = [2016,2017,2018]

# //--------------------------------------------
# //--------------------------------------------

def main():

    current_time = datetime.now().strftime("%d%b%Y_%Hh%Mm%S") #Date/time suffix

    #parse command line
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--campaign',     dest='campaign',   help='campaign',  default=None, type=str)
    parser.add_argument('--nfilesperchunk',     dest='nfilesperchunk',   help='number of files to run on',  default=1, type=int)
    parser.add_argument('--baseoutdir' , dest='baseoutdir' , help='the base directory to write output files' , default='/eos/cms/store/group/phys_smp/vbfA/skimmed_ntuples' , type=str) #/eos/cms/store/group/phys_smp/vbfA/skimmed_ntuples #/eos/user/n/ntonon/condor_outputs
    parser.add_argument('-o' , '--outdir',     dest='outdir',   help='output directory name. it will be added at the end of the baseoutdir',  default='outputs_'+current_time, type=str)
    parser.add_argument('-l', '--logdir',     dest='logdir',   help='logdir',  default='condor_', type=str)
    parser.add_argument('--flavour', dest='flavour',   help='job-flavour',  default='tomorrow', choices=['espresso' ,'microcentury','longlunch','workday','tomorrow','testmatch','nextweek'], type=str)
    parser.add_argument('--outfilename', dest='outfilename',   help='the name of the submit file',  default='vjj_VJJSkimmerJME.submit' , type=str)
    parser.add_argument('--includeexistingfiles', dest='includeexistingfiles',   help='ignore if an output file exists and resubmit the job',  default=False , action='store_true')
    parser.add_argument('--splitjobs', dest='splitjobs',   help='set nfilesperchunk=1 and run for the remaining jobs',  default=False , action='store_true')
    parser.add_argument('--neventsperjob', dest='neventsperjob',   help='set nevents per job, only if splitjobs is set',  default=-1 , type=int)
    parser.add_argument('-d', '--dataset', dest='dataset',   help='name of single dataset to process (else process all)',  default='', type=str)
    parser.add_argument('--data', dest='onlydata', help='only process data samples', nargs='?', const=1)
    parser.add_argument('--mc', dest='onlymc', help='only process mc samples', nargs='?', const=1)
    parser.add_argument('-y', '--year', dest='year',   help='process only the specified year',  default=-1, type=int)

    opt, unknownargs = parser.parse_known_args()

    condor = []

    campaign = None
    if opt.campaign: campaign = CampaignManager( opt.campaign )
    else: raise ValueError( 'please specify campaign name you want to run using -c option')

    if not os.path.exists( opt.logdir+opt.campaign.replace('/','_')+str(opt.year)+'_'+current_time ): os.makedirs( opt.logdir+opt.campaign.replace('/','_')+str(opt.year)+'_'+current_time )
    opt.logdir=opt.logdir+opt.campaign.replace('/','_')+str(opt.year)+'_'+current_time 

    datasetsToProcess = DATAsamples + MCsamples
    if opt.onlydata and opt.onlymc: print(colors.fg.lightred + 'ERROR: cannot use both options onlydata and opt.onlymc !'); return
    elif opt.onlydata: datasetsToProcess = DATAsamples
    elif opt.onlymc: datasetsToProcess = MCsamples

    yearsToProcess = years
    if opt.year > 0: yearsToProcess = [opt.year]

    print(colors.fg.orange + '== Only considering samples containing any of the following keys:' + colors.reset)
    print('#########',datasetsToProcess)

    step_par_name = 'Step' if opt.includeexistingfiles else 'chunkid'
    full_outdir = '{2}/{0}/{1}/'.format( opt.campaign , opt.outdir , opt.baseoutdir )
    total_existing_files = 0
    total_jobs = 0
    total_jobs_with_no_input = 0

    actual_nfilesperchunk = 1 if opt.splitjobs else opt.nfilesperchunk
    print('actual_nfilesperchunk:',actual_nfilesperchunk)

    fs=22
    if 'mm' in opt.campaign:
       fs=169 
    elif 'ee' in opt.campaign:
       fs=121 
    elif 'fake' in opt.campaign:
       fs=-22 
    condor.append( ('executable' , '{0}/vjj_VJJSkimmerJME.sh'.format(os.getcwd()) ) )
    if opt.neventsperjob > 0 :
        condor.append( ('arguments','-c $(CAMPAIGN) -d $(DATASET) --nfilesperchunk {0} --chunkindex $({1}) -o {2} -N {3} -f $(FIRSTEVENT) -S {4}'.format(actual_nfilesperchunk , step_par_name , full_outdir , opt.neventsperjob , fs )))
#        condor.append( ('arguments','-c {3} -d $(DATASET) --nfilesperchunk {0} --chunkindex $({1}) -o {2} -N {4} -f $(FIRSTEVENT) -S -22'.format(actual_nfilesperchunk , step_par_name , full_outdir , opt.campaign , opt.neventsperjob )))
    else:
        condor.append( ('arguments','-c $(CAMPAIGN) -d $(DATASET) --nfilesperchunk {0} --chunkindex $({1}) -o {2} -S {3}'.format(actual_nfilesperchunk , step_par_name , full_outdir , fs)))
#        condor.append( ('arguments','-c {3} -d $(DATASET) --nfilesperchunk {0} --chunkindex $({1}) -o {2} -S -22'.format(actual_nfilesperchunk , step_par_name , full_outdir , opt.campaign)))

#//--------------------------------------------

    #-- condor_submit args #See: https://htcondor.readthedocs.io/en/latest/man-pages/condor_submit.html
    #condor.append( ('Universe','vanilla'))
    condor.append( ('output','{0}/$(ClusterId).$(ProcId).out'.format(opt.logdir)))
    condor.append( ('error','{0}/$(ClusterId).$(ProcId).err'.format(opt.logdir)))
    condor.append( ('log','{0}/$(ClusterId).log'.format(opt.logdir)))
    #condor.append( ('+MaxRuntime',32400)) #Sets the max run time to 32400/3600=9h
    condor.append( ('+JobFlavour','\"{}\"'.format(opt.flavour))) #Must be enclosed in double quotes
    condor.append( ('transfer_executable',False))
    condor.append( ('requirements','( (OpSysAndVer =?= "CentOS7") || (OpSysAndVer =?= "SLC6") )'))
    condor.append( ('stream_output' , True ) )
    condor.append( ('stream_error' , True ) )
    condor.append( ('max_transfer_output_mb' , '4000' ) ) #Must use 'IF_NEEDED' to write output directly to /eos
    condor.append( ('should_transfer_files' , 'YES' ) ) #Must use 'IF_NEEDED' to write output directly to /eos
    condor.append( ('when_to_transfer_output' , 'ON_EXIT' ) ) #ON_SUCCESS/ON_EXIT_OR_EVICT
    condor.append( ('transfer_output_files' , 'out.root' ) ) #ON_SUCCESS/ON_EXIT_OR_EVICT
    condor.append( ('transfer_output_remaps' , '"out.root=root://eosuser.cern.ch//eos/user/y/yian/AJJ_analysis/$(OUTPUT)$(CAMPAIGN)_{0}_$(ClusterId)/Skim_$(ClusterId)_$(ProcId).root"'.format(opt.year) ) ) #ON_SUCCESS/ON_EXIT_OR_EVICT
#    condor.append( ('transfer_output_remaps' , '"out.root=Skim_$(ClusterId)_$(ProcId).root"' ) ) #ON_SUCCESS/ON_EXIT_OR_EVICT
#    condor.append( ('output_destination' , 'root://eosuser.cern.ch//eos/user/y/yian/AJJ_analysis/$(ClusterId)/' ) ) 
#    condor.append( ('MY.XRDCP_CREATE_DIR' , 'True' ) ) 
    condor.append( ('request_memory' , '30GB' ) ) 

#//--------------------------------------------
    for s,info in currentSampleList.all_datasets():
        n = Sample(s)
        data_flag=False

        for subsample in DATAsamples:
            if n.makeUniqueName().split('_')[0] in subsample:
               data_flag=True
               break 

#        print('data flag: ',data_flag)
	if data_flag:
           if str(opt.year) not in n.makeUniqueName():
              continue
           if opt.dataset != '' and n.makeUniqueName().split('_')[0] not in opt.dataset:
              continue
	else:
#           print('############TEST###########',opt.dataset,n.makeUniqueName(),' ',str(opt.year))
           if str(opt.year) not in n.makeUniqueName() and opt.year != 2016:
              continue
           if opt.dataset != '' and n.makeUniqueName().split('13TeV')[0] not in opt.dataset : #for MC
                continue

	if data_flag:
            sample_name=n.makeUniqueName().split('_')[0]+'_'
        else:
	    sample_name=n.makeUniqueName().split('13TeV')[0]
        print('***************TEST*************',opt.dataset,n.makeUniqueName(),' ',str(opt.year))

        if len(datasetsToProcess)>0 and not any(substring in n.makeUniqueName() for substring in datasetsToProcess): 
            print('Ignoring dataset: ', n.makeUniqueName())
            continue #Ignore all non-selected datasets
        if len(yearsToProcess)>0 and not any(year == n.year() for year in yearsToProcess): continue #Ignore all non-selected years
#        print('**********',s,' ',campaign.get_dataset_info(s))
        totalFiles = len( campaign.get_dataset_info(s)['files'] )
        nsteps = totalFiles/opt.nfilesperchunk if totalFiles%opt.nfilesperchunk==0 else 1+totalFiles/opt.nfilesperchunk
        if opt.includeexistingfiles:
            print('!!!!!!!!!!','resbmit??????')
            condor.append( ('queue' ,  nsteps , s ) )
            print(condor[-1][1])
            total_jobs += condor[-1][1]
            print(total_jobs)
        else:
            filesToRun = []
            for step in range( nsteps ):
                outfilepath,exists = make_hadd_fname( "./",full_outdir , s , opt.nfilesperchunk , step )
#                print('############ ',outfilepath,exists)
                if not exists or os.path.getsize(outfilepath)==0: #Will resubmit job if outfile does not exist OR size==0 (changed)
#                    if exists: print('... Will resubmit failed job (filesize=0): ' + outfilepath)
#                    else: 
#                        print('... Will submit missing job: ' + outfilepath)
                    try:
                        inputfilenames = get_fileNames(campaign, s, opt.nfilesperchunk, step,False) #Prints: (dataset,nfilesperchunk,chunkindex,nfiles,nchunks)
                        if opt.splitjobs: #Force set nfilesperchunk=1, recompute job indices
                            for i in range( opt.nfilesperchunk ):
                                if len(inputfilenames)<i+1 :
                                    continue
                                newjobindex = step*opt.nfilesperchunk+i
                                if opt.neventsperjob != -1: #Split by nevents
                                    _,exists1 = make_hadd_fname( "./",full_outdir , s , 1 , newjobindex )
                                    if exists1:
                                        continue
                                    fIn = ROOT.TFile.Open( inputfilenames[i] )
                                    tIn = fIn.Get("Events")
                                    ntotalevents = tIn.GetEntries()
                                    fIn.Close()
                                    for start in range(0, ntotalevents , opt.neventsperjob ):
                                        _,exists1 = make_hadd_fname( "./",full_outdir , s , 1 , newjobindex , start , opt.neventsperjob )
                                        if not exists1:
                                            filesToRun.append( [newjobindex , start] )
                                else:
                                    outpath1,exists1 = make_hadd_fname( "./",full_outdir , s , 1 , newjobindex )
                                    if not exists1 or os.path.getsize(outpath1)==0:
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
    outfilename=sample_name+opt.campaign+str(opt.year)+'_'+opt.outfilename
    print(outfilename)
    outfilename=outfilename.split('/')
    outfilename=outfilename[0]+'_'+outfilename[1]
    with open( outfilename , 'w') as f:
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
                print('############# ',lqueue)
                f.write( 'queue {0} OUTPUT CAMPAIGN DATASET from (\n'.format( lqueue ) )
                for ll in condor:
		    print('$$$$$$$$$$$ ',ll)
                    if ll[0] == 'queue' and ll[1] == lqueue:
                        if ll[2] in added_samples:
                            continue
                        f.write( '\t{0} {1} {2}\n'.format( ll[2],sample_name, opt.campaign) )
                        added_samples.append( ll[2] )
                f.write( ")\n" )
        else:
            if opt.neventsperjob < 0 :
                f.write( 'queue OUTPUT CAMPAIGN DATASET,{0} from (\n'.format( step_par_name ) )
                for l in condor:
                    if l[0] == 'queue_list':
                        for index in l[1]:
                            f.write('\t{0} {1} {2} {3}\n'.format( sample_name,opt.campaign, l[2] , index ) )
            else:
                f.write( 'queue OUTPUT CAMPAIGN DATASET,{0},FIRSTEVENT from (\n'.format( step_par_name ) )
                for l in condor:
                    if l[0] == 'queue_list':
                        for index in l[1]:
                            f.write('\t{0} {1} {2} {3} {4}\n'.format( sample_name, opt.campaign, l[2] , index[0] , index[1] ) )

            f.write( ')\n' )
    print('== In total, {0} jobs will be submitted.'.format(total_jobs))
    if total_existing_files>0: print('== The output of {0} files already exists. They are skipped'.format(total_existing_files))
    if total_jobs_with_no_input>0: print('== {0} jobs skipped, because the input files can not be found'.format(total_jobs_with_no_input))
    print( 'run `condor_submit {0}` to submit jobs'.format( outfilename ) )

if __name__ == "__main__":

    main()
