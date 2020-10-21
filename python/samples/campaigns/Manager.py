from UserCode.VJJSkimmer.samples.Manager import Manager as SampleManager
from UserCode.VJJSkimmer.samples.Sample import Sample
from UserCode.VJJSkimmer.samples.xsections import xsec
import os
import json
import numpy as np
from xml.etree.ElementTree import ElementTree, Element, SubElement, Comment, tostring

class Manager():
    def __init__(self, file):
        self.filename = file
        try:
            __dir=os.path.dirname(os.path.abspath(__file__))
        except:
            __dir = os.getcwd()
        with open('{0}/{1}'.format( __dir , file) ) as f:
            self.js = json.load( f )

        self.isSkimmedCampaign = False
        if 'generalInfo' in self.js:
            if 'parentcampaign' in self.js['generalInfo']:
                self.parentcampaign = Manager( self.js['generalInfo']['parentcampaign'] )
                self.isSkimmedCampaign = True
            
        isJsonModified = False

#        self.dyjs = {}
#        for key, val in self.js.iteritems():
#            if '10DYJetsMGHT' in key:
#                self.dyjs[key]=val
#        print self.dyjs'''
        self.samples = SampleManager( self.js.keys() , update_html=False )
        #self.samples = SampleManager( self.dyjs.keys() , update_html=False )
        self.AllInfo = {}
        self.LinkedSamples = {}
        self.SamplesWithWeightErrors = []
        for ds, year, binval , sname in self.samples.all_datasets(moreinfo=True):
            ds = str(ds)
            s = Sample(ds)
            year = s.year()
            xsection = 0 if s.isData() else 1
            ntotal = 0
                
            if not self.isSkimmedCampaign:
                try:
                    parent = str( self.js[ds]['parent'] )
                except:
                    parent = s.GetParent().ds
                    self.js[ds]['parent'] = parent
                    isJsonModified = True

                if s.isData():
                    xsection = 0
                else:
                    xsection = xsec[parent]
                #ntotal = self.js[ds]['total']
                
                        
           
            if year not in self.AllInfo:
                self.AllInfo[year] = {}
                #sname:{'weights':{i:vals['name'] for i,vals in self.js[ds]['weights'].items()} , binval:{'xsecs':[] , 'samples':[] , 'nevents':{} }}}
            if sname not in self.AllInfo[year]:
                self.AllInfo[year][sname] = {'weights':{str(vals['name']):{str(ds):int(i)} for i,vals in self.js[ds]['weights'].items()} }
            else:
                if len( set([a for a in self.AllInfo[year][sname]['weights'].keys()])-set([v['name'] for _,v in self.js[ds]['weights'].items()] ) ) > 0:
                    if (year,sname) not in self.SamplesWithWeightErrors:
                        self.SamplesWithWeightErrors.append( (year,sname) )
                    
                for i,val in self.js[ds]['weights'].items():
                    wname = str(val['name'])
                    if wname in self.AllInfo[year][sname]['weights']:
                        self.AllInfo[year][sname]['weights'][wname][str(ds)] = int(i)
                    else:
                        self.AllInfo[year][sname]['weights'][wname] = {str(ds): int(i)}
                        if (year,sname) not in self.SamplesWithWeightErrors:
                            self.SamplesWithWeightErrors.append( (year,sname) )

            if binval not in self.AllInfo[year][sname]:
                self.AllInfo[year][sname][binval] = {'xsecs':[] , 'samples':[] , 'nevents':{vals['name']:[] for _,vals in self.js[ds]['weights'].items() } }

            self.AllInfo[year][sname][binval]['xsecs'].append( xsection )
            self.AllInfo[year][sname][binval]['samples'].append( ds )
            for i,vals in self.js[ds]['weights'].items():
                wname = vals['name']
                if wname in self.AllInfo[year][sname][binval]['nevents']:
                    self.AllInfo[year][sname][binval]['nevents'][wname].append( vals['total'] )
                else:
                    self.AllInfo[year][sname][binval]['nevents'][wname] = [ vals['total'] ]
            self.LinkedSamples[ ds ] = self.AllInfo[year][sname][binval]

        if isJsonModified:
            print('writing json file')
            with open('{0}/{1}'.format( __dir , file) , 'w') as f:
                json.dump( self.js , f )
        
        if len(self.SamplesWithWeightErrors)>0:
            print( 'following samples have some inconsistent weights, please have a look')
            print( self.SamplesWithWeightErrors )

    def get_allWeightIndices(self , ds):
        s = Sample(ds)

        sampleWeights = self.AllInfo[s.year()][ self.samples.get_sampleName(ds) ]['weights']

        ret = { 0:('nominal' , 0) }
        nameIndice = {'nominal':0}
        index = 1
        for scale_id in range( len([ k for k in sampleWeights.keys() if 'SCALE' in k ]) ):
            nname = 'SCALE_{0}'.format(scale_id)
            ret[ index ] = ( nname , 0 ) 
            nameIndice[ nname ] = index
            index += 1
        for ps_id in range( len([ k for k in sampleWeights.keys() if 'PS' in k ]) ):
            nname = 'PS_{0}'.format(ps_id)
            ret[ index ] = ( nname , 0 ) 
            nameIndice[nname] = index
            index += 1
        for pdf_id in range( len([ k for k in sampleWeights.keys() if 'PDF' in k ]) ):
            nname = 'PDF_{0}'.format(pdf_id)
            ret[ index ] = ( nname , 0 ) 
            nameIndice[nname] = index
            index += 1
        for lhe_id in range( len([ k for k in sampleWeights.keys() if 'LHE' in k ]) ):
            nname = 'LHE_{0}'.format(lhe_id)
            ret[ index ] = ( nname , 0 ) 
            nameIndice[nname] = index
            index += 1

        #return sampleWeights
        for wname,info in sampleWeights.items():
            if ds in info:
                windex = nameIndice[wname]
                wnewname = ret[ windex ][0]
                if wnewname != wname :
                    print( wname , wnewname )
                ret[windex] = ( wnewname, info[ds] )
        return ret

    def get_lumis(self, ds):
        s = Sample(ds)
        year = s.year()
        LUMIS = None
        if year==2016:
            LUMIS={'LowVPt':28200.0, 'HighVPt':35900.0}
        elif year==2017:
            LUMIS={'LowVPt':7661.0,'HighVPt':41367.0}
        elif year==2018:
            LUMIS={'LowVPt':59735.969368,'HighVPt':59735.969368}

        LUMIS['HighVPtee'] = LUMIS['HighVPtmm'] = LUMIS['LowVPtee'] = LUMIS['LowVPtmm'] = LUMIS['HighVPt']
        return LUMIS
                

    def get_dataset_info(self, ds , just_ok_files = True):
        for year in self.AllInfo:
            for sample in self.AllInfo[year]:
                for binval in self.AllInfo[year][sample]:
                    if binval == 'weights':
                        continue
                    for ds_ in self.AllInfo[year][sample][binval]['samples']:
                        s = Sample(ds_)
                        if ds == ds_ or ds == s.makeUniqueName():
                            files = []
                            for f,info in self.js[ds]['files'].items():
                                if just_ok_files:
                                    if type( info ) in [str, unicode]:
                                        continue
                                files.append( os.path.abspath(f) )
                            return {'color':self.samples.get_sampleColor(sample), 'nTotal':self.get_allNTotals(ds) , 'xsection':self.get_xsection(ds) , 'sample':s , 'sName':sample , 'files':files , 'regions':self.samples.get_sampleRegions(sample)}
        return None

    def get_files_byyear(self , year , just_ok_files = False):
        for ds,info in self.samples.all_datasets():
            if info['year']==year:
                for f,info in self.js[ds]['files'].items():
                    if just_ok_files:
                        if type( info ) == str:
                            continue
                    yield os.path.abspath(f)

    def get_xsection(self, ds):
        s = Sample(ds)
        if s.isData():
            return 0
        else:
            if 'parent' in self.js[ds]:
                return xsec[ self.js[ds]['parent'] ]
            else:
                return 1

    def get_xsection_avg(self, ds):
        try:
            return np.mean( self.LinkedSamples[ds]['xsecs'] )
        except:
            return 0

    def get_xsection_variance(self, ds):
        try:
            return np.var( self.LinkedSamples[ds]['xsecs'] )
        except:
            return 0
        
    def get_allNTotals(self ,ds ):
        allweights = self.get_allWeightIndices(ds)
        ret = {}
        for windex,info in allweights.items():
            wname = info[0]
            if info[1] == 0:
                wname = 'nominal'
            ret[windex] = self.get_nTotal( ds , wname )
        return ret
            
    def get_nTotal(self , ds , wname):
        return np.sum(  self.LinkedSamples[ds]['nevents'][wname] )

    def get_lumi_weight(self , ds ):
        s = Sample(ds)
        lumis = self.get_lumis(ds)
        ret = {cat:{0:1} for cat in lumis}
        if not s.isData():
            xsec = self.get_xsection(ds)
            allntotals = self.get_allNTotals(ds)
            for index,ntotal in allntotals.items():
                for cat,lumi in lumis.items():
                    ret[cat][index] = lumi*xsec/ntotal
        return ret

    def fileInfo(self , f):
        f = os.path.abspath( f )
        for year in self.AllInfo:
            for sample in self.AllInfo[year]:
                for binval in self.AllInfo[year][sample]:
                    for ds in self.AllInfo[year][sample][binval]['samples']:
                        if f in [os.path.abspath(fff) for fff in self.js[ds]['files']]:
                            s = Sample(ds)
                            return {'color':self.samples.get_sampleColor(sample), 'nTotal':self.get_allNTotals(ds, 'nominal') , 'xsection':self.get_xsection(ds) , 'sample':s , 'sName':sample }

        raise NameError('no dataset found for file:{0}'.format( f ))

    def write_html(self):
        html = Element("html")
        head = SubElement( html , 'head')
        css = SubElement( head , 'link'  )
        css.set( 'rel',"stylesheet" )
        css.set( 'href', "https://www.w3schools.com/w3css/4/w3.css")
        body = SubElement( html , 'body')
        index = SubElement( body , 'div')
        lst = SubElement( index , 'ol' )
        lst.set( 'class',"w3-ol" )
        
        for year in self.AllInfo:
            year_in_list = SubElement( lst , 'li' )
            year_in_list.text = str(year)
            samples = SubElement( year_in_list , 'ol' )

            div_samples = SubElement( body , 'div' )
            div_samples.set( 'id' , 'samples_{0}'.format( year ) )
            SubElement( div_samples , 'h1' ).text = str(year)
            year_samples = SubElement( div_samples , 'ol' )

            for s in self.AllInfo[year]:
                s_in_list = SubElement( SubElement( samples , 'li' ) , 'a')
                s_in_list.text = s
                s_in_list.set( 'href' , '#{0}{1}'.format( year , s ) )

                s_bins = SubElement(year_samples , 'li')
                s_link = SubElement( s_bins  , 'a' )
                s_link.set('name' , '{0}{1}'.format( year , s ) )
                s_link.text = s
                
                
                if len(self.AllInfo[year][s]) == 1:
                    div_info = SubElement( s_bins , 'div')
                    info_ol = SubElement( div_info , 'ul')
                    samples_ys = self.AllInfo[year][s][ self.AllInfo[year][s].keys()[0] ]['samples']
                    SubElement( info_ol , 'li' ).text = 'ntotal = {0}'.format( self.get_nTotal( samples_ys[0] , 'nominal' )  )
                    SubElement( info_ol , 'li' ).text = 'xsection = {0}+-{1}'.format( self.get_xsection( samples_ys[0] ) , self.get_xsection_variance(samples_ys[0]))
                    
                    bin_ol = SubElement( s_bins , 'ol' )
                    for sample in samples_ys:
                        sample_li = SubElement( bin_ol , 'li')
                        sample_li.text = sample
                        
                        div_ds = SubElement( sample_li , 'div')
                        lo_ds = SubElement( div_ds , 'ul')
                        for ds_file_prop in ["nFilesWithNoHisto", "nFile", "nOkFiles", "nFilesWithError", "nNotExisting", "nNoneFiles"]:
                            SubElement( lo_ds , 'li' ).text = '{0} : {1}'.format( ds_file_prop , self.js[ sample ]["filestat"][ds_file_prop] )
                        lo_ds_files = SubElement( div_ds , 'ul')
                        for file_ds,file_ds_stat in self.js[sample]['files'].items():
                            SubElement( lo_ds_files , 'li' ).text = '{0} : {1}'.format( file_ds , file_ds_stat ) 
                else:
                    s_lst = SubElement( s_bins , 'ol' )
                    
                    for bin_val in self.AllInfo[year][s]:
                        bin_li = SubElement( s_lst , 'li' )
                        bin_li.text = bin_val
                        
                        samples_ys = self.AllInfo[year][s][bin_val]['samples']
                        div_info = SubElement( bin_li , 'div')
                        info_ol = SubElement( div_info , 'ul')
                        SubElement( info_ol , 'li' ).text = 'ntotal = {0}'.format( self.get_nTotal( samples_ys[0] , 'nominal' ) )
                        SubElement( info_ol , 'li' ).text = 'xsection = {0}+-{1}'.format( self.get_xsection( samples_ys[0] ) , self.get_xsection_variance(samples_ys[0]))
    
                        bin_ol = SubElement( bin_li , 'ol' )
                        for sample in samples_ys:
                            sample_li = SubElement( bin_ol , 'li')
                            sample_li.text = sample

                            div_ds = SubElement( sample_li , 'div')
                            lo_ds = SubElement( div_ds , 'ul')
                            for ds_file_prop in ["nFilesWithNoHisto", "nFile", "nOkFiles", "nFilesWithError", "nNotExisting", "nNoneFiles"]:
                                SubElement( lo_ds , 'li' ).text = '{0} : {1}'.format( ds_file_prop , self.js[ sample ]["filestat"][ds_file_prop] )
                            lo_ds_files = SubElement( div_ds , 'ul')
                            for file_ds,file_ds_stat in self.js[sample]['files'].items():
                                SubElement( lo_ds_files , 'li' ).text = '{0} : {1}'.format( file_ds , file_ds_stat ) 

        tree = ElementTree(html)        
        tree.write( '{0}/src/UserCode/VJJPlotter/web/Campaigns/{1}.html'.format( os.getenv('CMSSW_BASE' , '.') , self.filename.split('.')[0] ) )

    

#a = Manager('june2020')
#a.write_html()
