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
        with open(file) as f:
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
                xsection = -1
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
            with open(file , 'w') as f:
                json.dump( self.js , f )

    def get_xsection(self, ds):
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


        tree = ElementTree(html)        
        tree.write( '{0}/src/UserCode/VJJPlotter/web/Campaigns/{1}.html'.format( os.getenv('CMSSW_BASE' , '.') , self.filename.split('.')[0] ) )

    

a = Manager('june2020')
a.write_html()
