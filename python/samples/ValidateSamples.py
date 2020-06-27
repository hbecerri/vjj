#! /usr/bin/env python

from Manager import *
from Sample import *
import json
import sys
import subprocess

class GrandParentChecks:
    def __init__(self , year , loadfromfile = False , fname = 'NanoAODv6.lst' ):
        self.parser = SampleNameParser()
        self.manager = Manager(fname)
        self.fname = fname
        if loadfromfile:
            with open( self.gpfilename() ) as f:
                self.all_grandparent = json.load( f )
            with open(self.pfilename() ) as f:
                self.all_parent = json.load( f )
        else:
            self.all_grandparent = {}
            self.all_parent = {}

            for ds,info in self.manager.all_datasets():
                s = Sample(ds , self.parser)
                if s.year() != year :
                    continue
                p = s.GetParent()
                if p :
                    if p.ds in self.all_parent:
                        self.all_parent[p.ds].append( ds )
                    else:
                        self.all_parent[p.ds] = [ds]
                    gp = p.GetParent()
                    if not gp:
                        print( 'grand parent for sample {0} not found, its parent is {1}'.format( ds , p.ds ) )
                        continue
                    if gp.ds in self.all_grandparent:
                        self.all_grandparent[ gp.ds ].append( ds ) 
                    else:
                        self.all_grandparent[ gp.ds ] = [ ds ]
                else:
                    print( 'parent for sample {0} not found'.format( ds ) )


            with open( self.gpfilename() , 'w' ) as f:
                json.dump( self.all_grandparent , f )
            with open( self.pfilename() , 'w' ) as f:
                json.dump( self.all_parent , f )

    def gpfilename(self):
        return self.fname.split('.')[0] + '_grandparent_{0}.lst'.format( year )
    def pfilename(self):
        return self.fname.split('.')[0] + '_parent_{0}.lst'.format( year )

    def check_parentsunique(self):
        for p in self.all_parent:
            if len( self.all_parent[p] ) != 1:
                print( "{0} is parent of {1}".format( p , self.all_parent[p] ) )
    def check_gparentsunique(self):
        for p in self.all_grandparent:
            if len( self.all_grandparent[p] ) != 1:
                print( "{0} is grandparent of {1}".format( p , self.all_grandparent[p] ) )
    def check_pu2017(self):
        for p in self.all_grandparent:
            s = Sample(p)
            if s.isData():
                continue
            if 'PU2017' not in p:
                print( "{0}".format( self.all_grandparent[p] ) )

#year = int(sys.argv[1] )
#gp = GrandParentChecks( int(sys.argv[1])  , loadfromfile = True  )
#gp.check_parentsunique()
#gp.check_gparentsunique()
#if year==2017:
#    gp.check_pu2017()



def UpdateList( old_file , new_str , new_file ):
    lst = []
    with open( old_file ) as f:
        for l in f:
            parts = l[:-1].split('/')
            print parts
            if len(parts)>1:
                lst.append( parts[1] )
    with open( new_file , 'w' ) as f:
        for ds in set( lst ):
            process = subprocess.Popen( [ '/cvmfs/cms.cern.ch/common/dasgoclient', "-query=dataset=/{0}/*{1}*/NANO*".format(ds,new_str) ], stdout=subprocess.PIPE)
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    f.write( output.strip() )
                    f.write( '\n' )

#UpdateList( 'NanoAODv6_v2.lst' , '02Apr2020' , 'NanoAODv7.lst' )
#The produced list may contain several non related samples, specially for 2017, samples where their grand parents doesn't contain PU2017 are not reliable and should be removed

def makeListOfParents():
    parser = SampleNameParser()
    for ds,_ in currentSampleList.all_datasets():
        s = Sample(ds , parser)
        parent = s.GetParent()
        if parent:
            print(parent.ds)
        else:
            print("\#please find parent of {0}".format( ds ) )
        
makeListOfParents()

