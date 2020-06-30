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

        isJsonModified = False
        self.samples = SampleManager( self.js.keys() , update_html=False )
        self.AllInfo = {}
        self.LinkedSamples = {}
        for ds, year, binval , sname in self.samples.all_datasets(moreinfo=True):
            s = Sample(ds)
            year = s.year()
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
            ntotal = self.js[ds]['total']

            if year not in self.AllInfo:
                self.AllInfo[year] = {sname:{binval:{'xsecs':[] , 'samples':[] , 'nevents':[] }}}
            if sname not in self.AllInfo[year]:
                self.AllInfo[year][sname] = {binval:{'xsecs':[] , 'samples':[] , 'nevents':[] }}
            if binval not in self.AllInfo[year][sname]:
                self.AllInfo[year][sname][binval] = {'xsecs':[] , 'samples':[] , 'nevents':[] }

            self.AllInfo[year][sname][binval]['xsecs'].append( xsection )
            self.AllInfo[year][sname][binval]['samples'].append( ds )
            self.AllInfo[year][sname][binval]['nevents'].append( ntotal )
            self.LinkedSamples[ ds ] = self.AllInfo[year][sname][binval]

        if isJsonModified:
            print('writing json file')
            with open('{0}/{1}'.format( __dir , file) , 'w') as f:
                json.dump( self.js , f )

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
            return xsec[ self.js[ds]['parent'] ]

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
        
    def get_nTotal(self , ds):
        return np.sum(  self.LinkedSamples[ds]['nevents'] )

    def get_lumi_weight(self , ds , lumi = 1000 ):
        s = Sample(ds)
        if s.isData():
            return 1
        else:
            return lumi*self.get_xsection(ds)/self.get_nTotal(ds)

    def fileInfo(self , f):
        f = os.path.abspath( f )
        for year in self.AllInfo:
            for sample in self.AllInfo[year]:
                for binval in self.AllInfo[year][sample]:
                    for ds in self.AllInfo[year][sample][binval]['samples']:
                        if f in [os.path.abspath(fff) for fff in self.js[ds]['files']]:
                            s = Sample(ds)
                            return {'color':self.samples.get_sampleColor(sample), 'nTotal':self.get_nTotal(ds) , 'xsection':self.get_xsection(ds) , 'sample':s , 'sName':sample}

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
                    SubElement( info_ol , 'li' ).text = 'ntotal = {0}'.format( self.get_nTotal( samples_ys[0] )  )
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
                        SubElement( info_ol , 'li' ).text = 'ntotal = {0}'.format( self.get_nTotal( samples_ys[0] ) )
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
