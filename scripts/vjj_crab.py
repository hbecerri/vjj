#! /usr/bin/env python
import argparse
import sys
import os
from UserCode.VJJSkimmer.samples.Manager import *
from UserCode.VJJSkimmer.samples.Sample import *


def create_config_files():
    with open('auto_crab_cfg.py' , 'w') as f:
        f.write('from UserCode.VJJSkimmer.etc import crab_cfg\n')
        f.write('config = crab_cfg.config\n')

    with open('auto_crab_signal_cfg.py' , 'w') as f:
        f.write('from UserCode.VJJSkimmer.etc import crab_cfg\n')
        f.write('config = crab_cfg.config\n')
        f.write("config.JobType.scriptArgs += '--isSignal'\n" )

def main():

    #parse command line
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument( 'action',   help='the action to take', choices=['submit'] ,  type=str)
    parser.add_argument( '--samples',  dest='samples',   help='file which includes list of samples',  type=str , required=True )
    parser.add_argument( '--workarea',  dest='workarea',   help='directory name to store crab job information',  default='crab',  type=str)
    parser.add_argument( '--runcommands',  dest='runcommands',   help='Run commands instead of printing them on stdout',  default=False,  action='store_true')
    parser.add_argument( '--crab_cfg' , dest='crab_cfg'  , help="specify the name of the crab config file, if not specified it is automatically created" , default='auto' )

    opt = parser.parse_args()
    samples = Manager( opt.samples )

    crab_dir = '{0}/src/UserCode/VJJSkimmer/crab/'.format( os.getenv('CMSSW_BASE') )
    opt.workarea = crab_dir + opt.workarea
    if not os.path.exists( crab_dir ): os.makedirs( crab_dir )

    config_files = {}
    if opt.crab_cfg == 'auto':
        create_config_files()
        config_files['signal'] = 'auto_crab_signal_cfg.py'
        config_files['all'] = 'auto_crab_cfg.py'
    else:
        cfg_files = opt.crab_cfg.split(',')
        config_files['all'] = cfg_files[0]
        config_files['signal'] = cfg_files[1] if len(cfg_files)==2 else cfg_files[0]

    all_commands_torun = ['source /cvmfs/cms.cern.ch/crab3/crab.sh;']
    all_commands_torun.append( 'voms-proxy-init -hours 999 -voms cms;' )
    if opt.action == 'submit':
        for ds,info in samples.all_datasets():
            s = Sample( ds )
            config_file = config_files[ 'signal' if info['signal'] else 'all' ]
            all_commands_torun.append( 'crab submit --config={4} General.requestName={1} Data.inputDataset={0} General.workArea={3}_{2};'.format( ds , s.makeUniqueName() , s.year() , opt.workarea , config_file ) )


    if opt.runcommands:
        print('running commands by this script is not implemented yet')
    else:
        for command in all_commands_torun:
            print(command)

if __name__ == "__main__":

    main()
