#! /usr/bin/env python
import argparse
import sys
import os
import datetime
import getpass
import json
import glob
import re
from UserCode.VJJSkimmer.samples.Manager import *
from UserCode.VJJSkimmer.samples.Sample import *
import ROOT


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

def GetJobSubmissionTime( working_directory , username = getpass.getuser() ):
    jobtime = ''
    if not os.path.exists( '{0}/.requestcache'.format( working_directory ) ):
        print( 'echo "Job {0}/.requestcache doesnt exist, it is skipped";'.format( working_directory ) )
        return None,None
    with  open('{0}/.requestcache'.format( working_directory ) ) as f:
        for line in f:
            if '{0}_crab'.format(username) in line:
                jobtime = line[1:14]
    D, T = jobtime.split('_')
    date = datetime.datetime( int(D[:2])+2000 , int(D[2:4]) , int(D[4:]) , int(T[:2]) , int(T[2:4]) , int(T[4:]) )
    return jobtime,date

def FinalSummary( wd , ds , outLFNDirBase ):
    job_time,_ = GetJobSubmissionTime( wd )
    if job_time == None:
        print( 'is going to skip this dataset')
        return {'total':0 , 'files':{} , 'filestat':{'nFile':0 ,'nOkFiles':0 ,  'nFilesWithError':0 , 'nFilesWithNoHisto':0 , 'nNoneFiles':0 , 'nNotExisting':0} , 'message':'.requestcache file does not exist'}
    s_name = ds.split('/')[1]
    s = Sample( ds )
    job_name = wd.split('/')[-1]

    stat,ratio,failds,finishds,others = ParseStatusJSON( wd + '/status.json' )
    if stat < 0:
        #the json file is not available, we assume maximum 1000 outputs
        allfiles = glob.glob("{0}/{1}/{2}/{3}/*/out_*.root".format( outLFNDirBase , s_name , job_name , job_time  ) )
        regex = re.compile( '.*out_(?P<jobid>[0-9]*).root' )
        jobids = [ int(regex.match( f ).groupdict()['jobid']) for f in allfiles ]
        missing_jobids = set(range( max(jobids) ) ) - set( jobids )
        allfiles += ["{0}/{1}/{2}/{3}/0000/out_{4}.root".format( outLFNDirBase , s_name , job_name , job_time , job_id ) for job_id in missing_jobids]
    else:
        allfiles = ["{0}/{1}/{2}/{3}/0000/out_{4}.root".format( outLFNDirBase , s_name , job_name , job_time , job_id ) for job_id in finishds+failds+others]

    ret = {'total':0 , 'size':0 , 'files':{} , 'filestat':{'nFile':0 ,'nOkFiles':0 ,  'nFilesWithError':0 , 'nFilesWithNoHisto':0 , 'nNoneFiles':0 , 'nNotExisting':0}}
    for f in allfiles:
        ret['filestat']['nFile'] += 1
        if os.path.exists( f ):
            try:
                fo = ROOT.TFile.Open( f )
            except:
                ret['files'][f] = 'error while openning the file'
                ret['filestat']['nFilesWithError'] += 1
            if fo :
                cutflow = fo.Get('cutflow') if s.isData() else fo.Get('wgtSum')
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
                fo.Close()
            else:
                ret['files'][f] = 'file is None'
                ret['filestat']['nNoneFiles'] += 1
        else:
            ret['files'][f] = 'does not exist'
            ret['filestat']['nNotExisting'] += 1

    return ret

def ParseStatusJSON( jsonfile ):
    Failed = []
    Finished = []
    Others = []
    nTotal = 0
    if not os.path.exists( jsonfile ):
        return -10,-1,Failed,Finished,Others
    with open( jsonfile ) as f:
        try:
            js = json.load( f )
        except ValueError as ve:
            return -20,-1,Failed,Finished,Others
        for job in js:
            nTotal += 1
            if js[job]['State'] == 'failed':
                Failed.append( job )
            elif js[job]['State'] == 'finished':
                Finished.append( int(job) )
            else:
                Others.append( job )
    Failed.sort()
    Finished.sort()
    Others.sort()

    if len(Others)==0 and len(Failed) == 0:
        return 1,0,Failed,Finished,Others
    elif len(Others)==0:
        return 0,(1.0*len(Failed))/nTotal,Failed,Finished,Others
    else:
        return 2,(1.0*len(Failed))/nTotal,Failed,Finished,Others

def create_config_files(outdir, fs):
    fsname = {b:a for a,b in RegionFinalStateDict.items()}[fs]
    outdir = '{0}/{1}'.format(outdir,fsname)

    with open('auto_crab_cfg.py' , 'w') as f:
        f.write('from UserCode.VJJSkimmer.etc import crab_cfg\n')
        f.write('config = crab_cfg.config\n')
#        f.write("config.Data.outLFNDirBase = '/store/group/phys_smp/vbfA/Hugo_test3/{0}'\n".format(outdir)) #USER-SPECIFIC PATH #Verify write permissions, e.g. with: [crab checkwrite --lfn=/store/group/phys_smp/vbfA --site T2_CH_CERN]
        f.write("config.Data.outLFNDirBase = '/store/group/phys_smp/vbfA/yian_test_syst/{0}'\n".format(outdir)) #USER-SPECIFIC PATH #Verify write permissions, e.g. with: [crab checkwrite --lfn=/store/group/phys_smp/vbfA --site T2_CH_CERN]
#        f.write("config.Data.outLFNDirBase = '/store/group/phys_smp/vbfA/yian/{0}'\n".format(outdir)) #USER-SPECIFIC PATH #Verify write permissions, e.g. with: [crab checkwrite --lfn=/store/group/phys_smp/vbfA --site T2_CH_CERN]
        f.write("config.JobType.scriptArgs.append('--finalState={0}')\n".format(fs))


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
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument( 'action',   help='the action to take', choices=['submit','delete', 'resubmit' , 'status' , 'statussummary' , 'makecampaignfile'] ,  type=str)
    parser.add_argument( '--samplelist',  dest='samplelist',   help='file including list of samples. By default, latest available list is used', default='auto' , type=str ) #E.g.: ../python/samples/lists/NanoAODv7.lst #Use most recent by default
    parser.add_argument( '--year',  dest='year',   help='year', choices=[2016,2017,2018,-1] , type=int , default=-1  )
    parser.add_argument( '--workarea',  dest='workarea',   help='directory name to store crab job information',  default='crab',  type=str)
    parser.add_argument( '--runcommands',  dest='runcommands',   help='Run commands instead of printing them on stdout',  default=False,  action='store_true')
    parser.add_argument( '--crab_cfg' , dest='crab_cfg'  , help="specify the name of the crab config file, if not specified it is automatically created" , default='auto' )
    parser.add_argument( '--outLFNDirBase' , dest='outLFNDirBase'  , help="[Only for makecampaignfile action] Address where the output files are stored"  )
    parser.add_argument('-d', '--dataset', dest='dataset',   help='process only this dataset',  default='', type=str)
    parser.add_argument('--datasetkey', dest='datasetkey',   help='process only samples containing this keyword',  default='', type=str)
    parser.add_argument('-S', '--finalState',     dest='finalState',   help='photon:22, fake photon:-22, mm: 169, ee:121',  default=0, type=int)
    opt = parser.parse_args()
# //--------------------------------------------

    if opt.finalState == None: raise ValueError('Must set the final state. Use --help for the options.') 
    samples = None
    if opt.samplelist == "auto":
        samples = currentSampleList
    else:
        samples = Manager( opt.samplelist )

    if opt.crab_cfg == 'auto':
        create_config_files(opt.workarea, opt.finalState)
        opt.crab_cfg = 'auto_crab_cfg.py'

    crab_dir = '{0}/src/UserCode/VJJSkimmer/crab/{1}/'.format( os.getenv('CMSSW_BASE') ,  {b:a for a,b in RegionFinalStateDict.items()}[opt.finalState])
    opt.workarea = crab_dir+ opt.workarea
    if not os.path.exists( crab_dir ): os.makedirs( crab_dir )

# //--------------------------------------------
    #-- Define list of commands to run
    all_commands_torun = [] #'source /cvmfs/cms.cern.ch/crab3/crab.sh;']
    #all_commands_torun.append( 'voms-proxy-init -hours 999 -voms cms;' )

    #-- Main loop on samples to process
    counter_samples = 0
#    for ds,info in samples.all_datasets():

    for ds,info in samples.extractSamples(opt.finalState):
#        print(ds) 
        s = Sample( ds )
        #print(s.makeUniqueName())
        if opt.dataset != '' and s.makeUniqueName() != opt.dataset: continue #Only process this specific sample
        if opt.datasetkey != '' and opt.datasetkey not in s.makeUniqueName(): continue #Only process samples matching this keyword
        counter_samples+= 1

        if opt.action == 'submit':
            if opt.year != -1 and s.year() != opt.year : continue
            all_commands_torun.append( 'crab submit --config={4} General.requestName={1} Data.inputDataset={0} General.workArea={3}_{2};'.format( ds , s.makeUniqueName() , s.year() , opt.workarea , opt.crab_cfg ) )

        elif opt.action == 'delete':
            all_commands_torun.append( 'mv {0}_{1}/crab_{2} /tmp/{3}/;'.format( opt.workarea , s.year() , s.makeUniqueName(), os.environ["USER"] ) )

        elif opt.action == 'resubmit' :
            all_commands_torun.append( 'crab purge -d {0}_{1}/crab_{2};'.format(  opt.workarea , s.year() , s.makeUniqueName() ) )

        elif opt.action == 'status' :
            all_commands_torun.append( 'echo "is going to fetch the status of crab jobs and store results in json format for further processing"')
            jsonfile = '{0}_{1}/crab_{2}/status.json'.format(  opt.workarea , s.year() , s.makeUniqueName() )
            stat,ratio,failds,finishds,others = ParseStatusJSON( jsonfile )
            if stat != 1:
                dt_tag = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
                all_commands_torun.append( 'echo "fetching status of {0}";'.format( s.makeUniqueName() ) )
                all_commands_torun.append( 'mv {0} {0}_{1};'.format( jsonfile , dt_tag ) )
                all_commands_torun.append( 'crab status -d {0}_{1}/crab_{2} --json | grep \'"1":\' > {0}_{1}/crab_{2}/status.json;'.format(  opt.workarea , s.year() , s.makeUniqueName() ) )
            all_commands_torun.append( '{0} statussummary --sample {1} --workarea {2};'.format( sys.argv[0] , opt.samplelist , opt.workarea ) )

        elif opt.action == 'statussummary' :
            stat,ratio,failds,finishds,others = ParseStatusJSON( '{0}_{1}/crab_{2}/status.json'.format(  opt.workarea , s.year() , s.makeUniqueName() ) )
            if stat==1 or (len(failds)==0 and stat>=0):
                continue
            #if not s.isData():
            #    continue
            print( 'job {0} status is {1},{2:.1f}%'.format( s.makeUniqueName() , stat , ratio*100 ) )
            if stat != 1 :
                print ('\tList of failed jobs: {0}'.format( str( failds ) ) )
                print ('\tList of other jobs: {0}'.format( str( others ) ) )

        elif opt.action == 'makecampaignfile':
            outjs = {}
            print('get information for ds {0}'.format( ds ) )
            s = Sample(ds)
            outjs[ds] = FinalSummary( '{0}_{1}/crab_{2}'.format(  opt.workarea , s.year() , s.makeUniqueName() )  , ds , opt.outLFNDirBase )
            with open('campaign.json' , 'w') as f :
                json.dump( outjs ,  f ) #print outjs
# //--------------------------------------------

    print('\n-- Considering {} samples --\n'.format(counter_samples))

    if opt.runcommands:
        print('running commands by this script is not implemented yet')
    else:
        for command in all_commands_torun:
            print(command)

    return


# //--------------------------------------------
# //--------------------------------------------


if __name__ == "__main__":

    main()
