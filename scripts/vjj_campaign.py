#! /usr/bin/env python
import os
import sys
import json
import argparse
from collections import OrderedDict
from UserCode.VJJSkimmer.samples.campaigns.Maker import Maker as CampaignMaker
from UserCode.VJJSkimmer.samples.Manager import currentSampleList
from UserCode.VJJSkimmer.samples.Sample import Sample
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(True)


def make_fname(c,y,s,ds):
    ret = './{2}/{0}_{1}'.format( s,y,c )
    for s in ds:
        ss = Sample(s)
        ret += '_{0}'.format( ss.makeUniqueName() )
    ret += '.json'
    return ret


def main():
    #parse command line
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument( 'action',   help='the action to take', choices=['make','merge', 'submit' ] ,  type=str)
    parser.add_argument('-c' , '--campaign',     dest='campaign',   help='the name of the produced campaign',  type=str)
    
    if sys.argv[1] in ['submit' , 'make']:
        parser.add_argument('-d' , '--directory',     dest='directory',   help='directory containing rootfiles',  type=str)
        parser.add_argument('-o' , '--outjsonname',     dest='outjsonname',   help='name of the json output',  default='auto', type=str)
    if sys.argv[1] == 'make':
        parser.add_argument( '--year',  dest='year',   help='year', choices=['16','17','18','all'] , type=str , default='all'  )
        parser.add_argument( '--sample',  dest='sample',   help='sample' , choices=[s.name for _,s in currentSampleList.all_samples.items()] , type=str , default=None)
        parser.add_argument('-s','--ds', action='append' , dest='datasets' , type=str , default=[] )

    opt, unknownargs = parser.parse_known_args()

    import __main__ as main
    currentdir = os.path.dirname(os.path.abspath(main.__file__))
    campaigndir = currentdir + '/' + opt.campaign
    if not os.path.exists( campaigndir ): os.makedirs( campaigndir )

    if opt.action == 'make': #Run on specific year/dataset
        if opt.outjsonname == 'auto':
            opt.outjsonname = make_fname( opt.campaign , opt.year , opt.sample , opt.datasets )

        print('== Running CampaignMaker()...')
        maker = CampaignMaker( opt.directory , opt.outjsonname , opt.sample , opt.year , opt.datasets )
    
    elif opt.action == 'submit': #Run on all years/datasets
        logDir = campaigndir + '/logs/'
        if not os.path.exists( logDir  ): os.makedirs( logDir )
        commands = OrderedDict()
        commands['executable'] = '{0}/vjj_campaign.sh'.format( currentdir )
        commands['output'] = '{0}/$(ClusterId).$(ProcId).out'.format( logDir )
        commands['error'] = '{0}/$(ClusterId).$(ProcId).err'.format( logDir )
        commands['log'] = '{0}/$(ClusterId).log'.format( logDir )
        commands['+JobFlavour'] = 'microcentury' #microcentury=1h, longlunch=2h 
        commands['transfer_executable'] = False
        commands['requirements'] = '( (OpSysAndVer =?= "CentOS7") || (OpSysAndVer =?= "SLC6") )'
        commands['stream_output'] = True
        commands['stream_error'] = True
        commands['arguments'] = 'make -c {0} -d {1} --year $(YEAR) --sample $(SAMPLE)'.format( opt.campaign , opt.directory)
        commands['queue YEAR,SAMPLE from ('] = None
        for y in ['16','17','18']:
            for s in [s.name for _,s in currentSampleList.all_samples.items()]:
                commands['\t{0} {1}'.format( y , s)] = None
        commands[')'] = None
        with open( campaigndir + '/submit' , 'w' ) as f:
            for c,v in commands.items():
                if v != None:
                    f.write( '{0} = {1}\n'.format( c , v ) )
                else:
                    f.write( '{0}\n'.format( c ) )
        print('run the following command to submit jobs')
        print('condor_submit {0}/submit'.format(opt.campaign) )

    elif opt.action == 'merge':
        outjs = {}
        for y in ['16','17','18']:
            for s in [s.name for _,s in currentSampleList.all_samples.items()]:
                f=make_fname( opt.campaign , y , s , [])
                if os.path.exists(f):
                    fi = open(f)
                    js = json.load( fi )
                    for ds in js:
                        outjs[ds] = js[ds]
                else:
                    print('output for {0} in {1} is missing, please reproduce it by the following command'.format( s , y ) )
                    print('{0} make -c {1} --year {2} --sample {3} -d {4}'.format( sys.argv[0] , opt.campaign , y , s , 'THEDIR' ) )
        outjson = '{0}/src/UserCode/VJJSkimmer/python/samples/campaigns/{1}'.format( os.environ['CMSSW_BASE'] , opt.campaign)
        if os.path.exists( outjson ):
            confirm = ''
            while confirm == '':
                confirm = raw_input('the campaign file {0} exist, are you sure you want to rewrite it?[y/n]'.format(outjson))
            if confirm.lower() not in ['y','yes']:
                print('exit')
                return
        with open( outjson  , 'w') as f:
            json.dump( outjs  , f ) 
        print('==> Wrote the campaign JSON file: {0}'.format( outjson ) )


if __name__ == "__main__":
    main()


