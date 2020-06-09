#! /usr/bin/env python
import argparse
from UserCode.VJJSkimmer.samples.Manager import *
from UserCode.VJJSkimmer.samples.Sample import *

def main():

    #parse command line
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument( 'action',   help='the action to take', choices=['submit'] ,  type=str)
    parser.add_argument( '--samples',  dest='samples',   help='file which includes list of samples',  type=str , required=True )
    parser.add_argument( '--workarea',  dest='workarea',   help='directory name to store crab job information',  default='crab',  type=str)
    parser.add_argument( '--runcommands',  dest='runcommands',   help='Run commands instead of printing them on stdout',  default=False,  action='store_true')

    opt = parser.parse_args()
    samples = Manager( opt.samples )
    opt.workarea = '../crab/' + opt.workarea

    all_commands_torun = ['source /cvmfs/cms.cern.ch/crab3/crab.sh;']
    all_commands_torun.append( 'voms-proxy-init -hours 999 -voms cms;' )
    if opt.action == 'submit':
        for ds,info in samples.all_datasets():
            s = Sample( ds )
            all_commands_torun.append( 'crab submit --config=crab_cfg.py General.requestName={1} Data.inputDataset={0} General.workArea={3}_{2};'.format( ds , s.makeUniqueName() , s.year() , opt.workarea) )


    if opt.runcommands:
        print('running commands by this script is not implemented yet')
    else:
        for command in all_commands_torun:
            print(command)

if __name__ == "__main__":

    main()
