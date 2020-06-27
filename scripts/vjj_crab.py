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

def GetJobSubmissionTime( working_directory , username = getpass.getuser() ):
    jobtime = ''
    if not os.path.exists( '{0}/.requestcache'.format( working_directory ) ):
        print( 'echo "Job {0}/.requestcache doesnt exist, it is skipped";'.format( working_directory ) )
        return None
    with  open('{0}/.requestcache'.format( working_directory ) ) as f:
        for line in f:
            if '{0}_crab'.format(username) in line:
                jobtime = line[1:14]
    D, T = jobtime.split('_')
    date = datetime.datetime( int(D[:2])+2000 , int(D[2:4]) , int(D[4:]) , int(T[:2]) , int(T[2:4]) , int(T[4:]) )
    return jobtime,date

def FinalSummary( wd , ds , outLFNDirBase ):
    job_time,_ = GetJobSubmissionTime( wd )
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

    ret = {'total':0 , 'files':{}}
    for f in allfiles:
        if os.path.exists( f ):
            try:
                fo = ROOT.TFile.Open( f )
            except:
                ret['files'][f] = 'error while openning the file'
            if fo :
                cutflow = fo.Get('cutflow') if s.isData() else fo.Get('wgtSum')
                if cutflow:
                    ret['files'][f] = cutflow.GetBinContent(1)
                    ret['total'] += cutflow.GetBinContent(1)
                else:
                    ret['files'][f] = 'no wgtSum/cutflow histo available'
                fo.Close()
            else:
                ret['files'][f] = 'file is None'
        else:
            ret['files'][f] = 'does not exist'

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



def create_config_files():
    with open('auto_crab_cfg.py' , 'w') as f:
        f.write('from UserCode.VJJSkimmer.etc import crab_cfg\n')
        f.write('config = crab_cfg.config\n')

    # with open('auto_crab_signal_cfg.py' , 'w') as f:
    #     f.write('from UserCode.VJJSkimmer.etc import crab_cfg\n')
    #     f.write('config = crab_cfg.config\n')
    #     f.write("config.JobType.scriptArgs += ['--isSignal']\n" )

def main():

    #parse command line
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument( 'action',   help='the action to take', choices=['submit','delete', 'resubmit' , 'status' , 'statussummary' , 'makecampaignfile'] ,  type=str)
    parser.add_argument( '--samples',  dest='samples',   help='file which includes list of samples, by default latest available list is used', default='auto' , type=str )
    parser.add_argument( '--workarea',  dest='workarea',   help='directory name to store crab job information',  default='crab',  type=str)
    parser.add_argument( '--runcommands',  dest='runcommands',   help='Run commands instead of printing them on stdout',  default=False,  action='store_true')
    parser.add_argument( '--crab_cfg' , dest='crab_cfg'  , help="specify the name of the crab config file, if not specified it is automatically created" , default='auto' )
    parser.add_argument( '--outLFNDirBase' , dest='outLFNDirBase'  , help="the address where the output files are stored, it is just used for makecampaignfile action"  )
    opt = parser.parse_args()
    
    samples = None
    if opt.samples == "auto":
        samples = currentSampleList
    else:
        samples = Manager( opt.samples )

    crab_dir = '{0}/src/UserCode/VJJSkimmer/crab/'.format( os.getenv('CMSSW_BASE') )
    opt.workarea = crab_dir + opt.workarea
    if not os.path.exists( crab_dir ): os.makedirs( crab_dir )

    if opt.crab_cfg == 'auto':
        create_config_files()
        opt.crab_cfg = 'auto_crab_cfg.py'

    all_commands_torun = [] #'source /cvmfs/cms.cern.ch/crab3/crab.sh;']
    #all_commands_torun.append( 'voms-proxy-init -hours 999 -voms cms;' )
    if opt.action == 'submit':
        for ds,info in samples.all_datasets():
            s = Sample( ds )
            #if info['signal']:
            if any([a in ds for a in ['QCD', 'Sherpa' , 'sherpa']] ):
                all_commands_torun.append( 'crab submit --config={4} General.requestName={1} Data.inputDataset={0} General.workArea={3}_{2};'.format( ds , s.makeUniqueName() , s.year() , opt.workarea , opt.crab_cfg ) )

    elif opt.action == 'delete':
        for ds,info in samples.all_datasets():
            #if info['signal']:
            #if any([a in ds for a in ['QCD', 'Sherpa' , 'sherpa']] ):
            if True:
                s = Sample( ds )
                #all_commands_torun.append( 'rm -rf {0}_{1}/crab_{2};'.format( opt.workarea , s.year() , s.makeUniqueName() ) )
                all_commands_torun.append( 'mv {0}_{1}/crab_{2} /tmp/hbakhshi/;'.format( opt.workarea , s.year() , s.makeUniqueName() ) )
    elif opt.action == 'resubmit' :
        for ds,info in samples.all_datasets():
            s = Sample( ds )
            #if not any([a in ds for a in ['QCD', 'Sherpa' , 'sherpa']] ):
            if True:
                all_commands_torun.append( 'crab resubmit -d {0}_{1}/crab_{2};'.format(  opt.workarea , s.year() , s.makeUniqueName() ) )
    elif opt.action == 'status' :
        all_commands_torun.append( 'echo "is going to fetch the status of crab jobs and store results in json format for further processing"')
        for ds,info in samples.all_datasets():
            s = Sample( ds )
            #if not any([a in ds for a in ['QCD', 'Sherpa' , 'sherpa']] ):
            jsonfile = '{0}_{1}/crab_{2}/status.json'.format(  opt.workarea , s.year() , s.makeUniqueName() )
            stat,ratio,failds,finishds,others = ParseStatusJSON( jsonfile )
            if stat != 1:
                dt_tag = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
                all_commands_torun.append( 'echo "fetching status of {0}";'.format( s.makeUniqueName() ) )
                all_commands_torun.append( 'mv {0} {0}_{1};'.format( jsonfile , dt_tag ) )
                all_commands_torun.append( 'crab status -d {0}_{1}/crab_{2} --json | grep \'"1":\' > {0}_{1}/crab_{2}/status.json;'.format(  opt.workarea , s.year() , s.makeUniqueName() ) )
        all_commands_torun.append( '{0} statussummary --sample {1} --workarea {2};'.format( sys.argv[0] , opt.samples , opt.workarea ) )
    elif opt.action == 'statussummary' :
        for ds,info in samples.all_datasets():
            s = Sample( ds )
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
        for ds,info in samples.all_datasets():
            if not ds in ['/EGamma/Run2018D-02Apr2020-v1/NANOAOD' , '/GJets_Mjj-500_SM_5f_TuneCP5_INTERFERENCE_13TeV-madgraph-pythia8/RunIIAutumn18NanoAODv7-Nano02Apr2020_102X_upgrade2018_realistic_v21-v1/NANOAODSIM' ]:
                continue
            s = Sample(ds)
            outjs[ds] = FinalSummary( '{0}_{1}/crab_{2}'.format(  opt.workarea , s.year() , s.makeUniqueName() )  , ds , opt.outLFNDirBase )
        json.dumps( outjs ,  open('campaign.json' , 'w') )

    if opt.runcommands:
        print('running commands by this script is not implemented yet')
    else:
        for command in all_commands_torun:
            print(command)

if __name__ == "__main__":

    main()
