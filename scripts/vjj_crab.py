#! /usr/bin/env python
import argparse
from UserCode.VJJSkimmer.samples.Manager import *

def main():

    #parse command line
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument( '--samples',  dest='samples',   help='file including list of samples',  default='',  type=str)
    parser.add_argument( '--workarea',  dest='workarea',   help='directory to store crab job information',  default='crab',  type=str)

    opt = parser.parse_args()

    samples = Manager( opt.samples )
    for ds,info in samples.all_datasets():
        print('crab submit --config=crab_cfg.py General.requestName={1} Data.inputDataset={0} General.workArea={3}_{2};'.format( ds , ds.split('/')[1] , info['year'] , opt.workarea) )

if __name__ == "__main__":

    main()
