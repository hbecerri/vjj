import os, datetime, re,sys, json
from UserCode.VJJSkimmer.samples.Manager import currentSampleList
from UserCode.VJJSkimmer.samples.Sample import Sample
import ROOT


class Maker:

    def __init__(self , base_dir , newjsonname , samplename , year_tofilter = 'all' , ds_tofilter=[] ):
        self.dir = base_dir
        self.samples = currentSampleList

        self.regex = re.compile( '.*out_(?P<jobid>[0-9]*).root' )
        self.info = {}
        for ds, year, binval , sname in self.samples.all_datasets(moreinfo=True):
            if sname == samplename:
                if year_tofilter != 'all':
                    if year != year_tofilter:
                        continue
                if len(ds_tofilter)!=0:
                    if ds not in ds_tofilter:
                        continue
                print('processing {0}'.format(ds) )
                self.info[ds] = self.get_sample_info( ds )
                

        dsnames = self.info.keys()
        ninconsistencies = 0
        inconsistencymap = {}
        for i in range( len(dsnames) ):
            ds1 = dsnames[i]
            s1 = Sample(ds1)
            wgts1 = self.info[ds1]['weights']
            #if wgts1['0']['total'] == 0:
            #    continue

            wgts1 = set([ v['name'] for _,v in wgts1.items() ])
            inconsistencymap[ s1.makeUniqueName() ] = []
            for j in range( len(dsnames) ):
                ds2 = dsnames[j]
                s2 = Sample(ds2)
                wgts2 = self.info[ds2]['weights']
                #if wgts2['0']['total'] == 0:
                #    continue
                wgts2 = set([ v['name'] for _,v in wgts2.items() ])

                if wgts1 != wgts2:
                    print( '\033[91m weights of {0} and {1} are not consistent \033[0m'.format( s1.makeUniqueName() , s2.makeUniqueName() ) )
                    print( 'here is the list of weights available in the first and not in the second: {0}'.format( wgts1-wgts2 ) )
                    print( 'here is the list of weights available in the second and not in the first: {0}'.format( wgts2-wgts1 ) )
                    ninconsistencies += 1
                    inconsistencymap[ s1.makeUniqueName() ].append( s2.makeUniqueName() )
                    #if s2.makeUniqueName() in inconsistencymap.keys():
                    #    inconsistencymap[ s2.makeUniqueName() ].append( s1.makeUniqueName() )
                    #else:
                    #    inconsistencymap[ s2.makeUniqueName() ] = [s1.makeUniqueName()]
        if ninconsistencies == 0:
            print( '\033[92m weights are consistent \033[0m' )
        else:
            print( inconsistencymap )
            for ds in sorted(inconsistencymap.keys() , key=lambda k: len(inconsistencymap[k]) , reverse=True  ):
                if len( inconsistencymap[ds] ) == 0:
                    continue
                print('\033[91m {0} is inconsistent with \033[0m'.format(ds) )
                for ds2 in inconsistencymap[ds]:
                    print('\t{0}'.format(ds2))
                    inconsistencymap[ds2].remove(ds)

        with open(newjsonname , 'w') as f:
            json.dump( self.info , f ) 
        

    def get_sample_info(self , das):
        s = Sample(das)
        name = s.makeUniqueName()
        
        print(self.dir , das , name )
        dir = os.path.join( self.dir , das.split('/')[1] , 'crab_' + name )
        if not os.path.exists( dir ):
            print('\033[91m the directory for sample {0} does not exist \033[0m'.format(das) )
            return {'weights':{'0':{'name':'nominal', 'total':0}} , 'size':0 , 'files':{} , 'filestat':{'nFile':0 ,'nOkFiles':0 ,  'nFilesWithError':0 , 'nFilesWithNoHisto':0 , 'nNoneFiles':0 , 'nNotExisting':0} , 'submit_datetime':str('')}
        dates = os.listdir(dir) 
        if len(dates) == 1:
            D, T = dates[0].split('_')
            date = datetime.datetime( int(D[:2])+2000 , int(D[2:4]) , int(D[4:]) , int(T[:2]) , int(T[2:4]) , int(T[4:]) )

            all_jobs = {}
            for dd , _ , files in os.walk( os.path.join( dir , dates[0] ) ):
                for f in files:
                    #print(dd,f)
                    if f.endswith('.root') :
                        jobid = int( self.regex.match( f ).groupdict()['jobid'] )
                        all_jobs[ jobid ] = os.path.join( dd , f )
            ret = {'weights':{'0':{'name':'nominal', 'total':0}} , 'size':0 , 'files':{} , 'filestat':{'nFile':0 ,'nOkFiles':0 ,  'nFilesWithError':0 , 'nFilesWithNoHisto':0 , 'nNoneFiles':0 , 'nNotExisting':0} , 'submit_datetime':str(date)}
            sys.stdout.write('\tjobs:')
            
            #FIXME why incorrect files e.g. for /SinglePhoton/Run2016D-02Apr2020-v1/NANOAOD ?
            nwgts = -1
            for job in range( 1, max(all_jobs)+1 ):
                sys.stdout.write( '{0},'.format(job) )
                sys.stdout.flush()
                ret['filestat']['nFile'] += 1
                if job in all_jobs:
                    f = all_jobs[job]
                    print('== f ', f) #FIXME
                    try:
                        fo = ROOT.TFile.Open( f )
                    except:
                        ret['files'][f] = 'error while openning the file'
                        ret['filestat']['nFilesWithError'] += 1
                        ret['size'] += size
                    if fo :
                        size = fo.GetSize()
                        ret['files'][f] = {'size':size}
                        cutflow = fo.Get('cutflow') if s.isData() else fo.Get('wgtSum')
                        if cutflow:
                            if s.isData():
                                bin_zero = cutflow.FindBin( 0.5 )
                                yields = cutflow.GetBinContent( bin_zero )
                                ret['files'][f]['0'] = yields
                                ret['weights']['0']['total'] += yields
                            else:
                                if nwgts < 0:
                                    events_t = fo.Get("Events")
                                    def readvals(e,b):
                                        return getattr(e,b) if hasattr(e,b) else 0
                                    for e in events_t:
                                        nwgts_ps = readvals(e,'nPSWeight')
                                        nwgts_scale = readvals(e,'nLHEScaleWeight')
                                        nwgts_lhe = readvals(e,'nLHEReweightingWeight')
                                        nwgts_pdf = readvals(e,'nLHEPdfWeight')
                                        break
                                    del events_t
                                    nwgts = 1
                                    for i in range(nwgts_ps) :
                                        ret['weights'][ str(nwgts) ] = {'name':'PS_{0}'.format(i) , 'total':0}
                                        nwgts += 1
                                    for i in range(nwgts_scale) :
                                        ret['weights'][ str(nwgts) ] = {'name':'SCALE_{0}'.format(i) , 'total':0}
                                        nwgts += 1
                                    for i in range(nwgts_lhe) :
                                        ret['weights'][ str(nwgts) ] = {'name':'LHE_{0}'.format(i) , 'total':0}
                                        nwgts += 1
                                    for i in range(nwgts_pdf) :
                                        ret['weights'][ str(nwgts) ] = {'name':'PDF_{0}'.format(i) , 'total':0}
                                        nwgts += 1
                                for wgt in range( nwgts ):
                                    yields = cutflow.GetBinContent( wgt+1 )
                                    ret['files'][f][str(wgt)] = yields
                                    ret['weights'][str(wgt)]['total'] += yields

                            ret['size'] += size
                            ret['filestat']['nOkFiles'] += 1
                        else:
                            ret['files'][f] = 'no wgtSum/cutflow histo available'
                            ret['filestat']['nFilesWithNoHisto'] += 1
                        fo.Close()
                    else:
                        ret['files'][f] = 'file is None'
                        ret['filestat']['nNoneFiles'] += 1
                else: #Problem: if next file not found, declare previous file as missing !
                    print('XX f ', f) #FIXME --> wrong index, should be updated to n+1
                    #ret['files'][f] = 'does not exist'
                    ret['filestat']['nNotExisting'] += 1
            print('')

            suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
            i = 0
            nbytes = ret['size']
            while nbytes >= 1024 and i < len(suffixes)-1:
                nbytes /= 1024.
                i += 1
            f = '{:.2f}'.format(nbytes).rstrip('0').rstrip('.')
            ret['size'] =  '{0} {1}'.format(f, suffixes[i])
            return ret

                        
        else:
            raise ValueError( 'there is {0} dates for {1}, {2}'.format( len(dates) , das , ','.join(dates) ) )        
