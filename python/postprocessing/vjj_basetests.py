#!/usr/bin/env python

import os,sys
import optparse
import copy
import ROOT
import pickle
from UserCode.VJJSkimmer.postprocessing.etc.testDatasets import getTestDataset,getTestCIDir


def runTestCodeCommand(year,dstype,maxEntries,localCIDir=None):

    """ run skim """

    isDataFlag='--isData' if dstype=='data' else ''
    cmd  = 'python python/postprocessing/vjj_postproc.py'
    cmd += ' -i auto -y {0} -N {1} {2}'.format(year,maxEntries,isDataFlag)
    cmd += ' -k python/postprocessing/etc/keep_and_drop_ci.txt'
    if localCIDir:
        cmd += ' --localCIDir {0}'.format(localCIDir)
    print(cmd)
    os.system(cmd)


def prepareCIDir(opt,args,rootxd = "root://cms-xrd-global.cern.ch/"):

    """prepares the test directory holding the files to run on """

    if not opt.skipCopy:
        print('Creating',opt.localCIDir)
        os.system('mkdir ' + opt.localCIDir)

        if not 'X509_USER_PROXY' in os.environ:
            print('No user proxy in environment. Starting one now')
            os.system('voms-proxy-init --voms cms')

    cutflows={}
    for a in args:

        year,dstype=a.split(',')
        year=int(year)
        url=getTestDataset(year=year,isData=True if dstype=='data' else False)
        
        #copy locally
        oname='{0}/{1}'.format(opt.localCIDir,os.path.basename(url))
        if not opt.skipCopy:
            os.system('xrdcp {0}/{1} {2}'.format(rootxd,url,oname))
        
        #run skim
        runTestCodeCommand(year=year,dstype=dstype,maxEntries=opt.maxEntries)

        #read cutflow histo to memory
        sname=os.path.basename(url).replace('.root','_Skim.root')
        fIn=ROOT.TFile.Open(sname)
        k=(year,dstype)
        cutflows[k]= {'histo': fIn.Get('cutflow').Clone('cutflow_{0}_{1}'.format(*k)),
                      'url':url }
        cutflows[k]['histo'].SetDirectory(0)
        fIn.Close()

    #save reference cutflows, test files and options used for future reference
    pname=os.path.join(opt.localCIDir,'reference_cutflows.pck')
    with open(pname,'wb') as fout:
        pickle.dump(cutflows,fout,pickle.HIGHEST_PROTOCOL)
        pickle.dump(opt,fout,pickle.HIGHEST_PROTOCOL)
    print('Reference cutflow histograms and summary information stored in',pname)
        

def validate(opt,args):

    """ runs the validation and returns a report """

    pname=os.path.join(opt.localCIDir,'reference_cutflows.pck')
    with open(pname,'r') as fin:
        ref_cutflows=pickle.load(fin)

    report={}
    for a in args:

        #run skim
        year,dstype=a.split(',')
        year=int(year)
        k=(year,dstype)
        runTestCodeCommand(year=year,dstype=dstype,maxEntries=opt.maxEntries,localCIDir=opt.localCIDir)

        #compute differences in the cutflow
        fname=getTestDataset(year,True if dstype=='data' else False,fromLocalCIDir=opt.localCIDir)
        sname=os.path.basename(fname).replace('.root','_Skim.root')
        fIn=ROOT.TFile.Open(sname)
        diff_cutflow=fIn.Get('cutflow')
        diff_cutflow.Add( ref_cutflows[k]['histo'], -1 )

        if diff_cutflow.Integral()==0:
            report[a]='OK'
        else:
            report[a]='Cutflow differences found'
            for xbin in range(diff_cutflow.GetNbinsX()):
                delta=diff_cutflow.GetBinContent(xbin+1)
                if delta==0: continue
                report[a]+=' (%d,%d) '%(xbin+1,delta)
            report[a] += '(original data from: %s)'%ref_cutflows[k]['url']

        fIn.Close()

    return report



def main():

    #parse command line
    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)
    parser.add_option('-d', '--localCIDir',     dest='localCIDir',   help='local CI directory [%default]',  default=getTestCIDir(), type='string')
    parser.add_option(      '--prepare',    dest='prepare',  help='prepare test input directory? [%default]', default=False, action='store_true')
    parser.add_option(      '--skipCopy',   dest='skipCopy',  help='skip copy to EOS? [%default]', default=False, action='store_true')
    parser.add_option('-N', '--maxEntries', dest='maxEntries',   help='max. entries to process [%default]', type=int, default=5000)  
    (opt, args) = parser.parse_args()

    if opt.prepare:
        prepareCIDir(opt,args)

    report=validate(opt,args)
    import json
    with open('report.json','w') as fout:
        json.dump(report, fout)
    print('Report available in report.json')



if __name__ == "__main__":
    sys.exit(main())


     


