import ROOT
import os
import errno
import numpy as np    

class ScaleFactorBase(object):
    """ wraps the general procedure to read ROOT objects or others storing scale factors to apply in an analysis """

    def __init__(self):
        self.sf_dict={}
        pass
        
    def init(self):
        self.sf_dict={}

    def addSFObject(self,tag,obj , stat = None , syst = None):

        """ adds an object directory  """

        self.sf_dict[tag]={'main':obj, 'stat':stat , 'syst':syst}
        if obj.InheritsFrom('TH1'):
            self.extrapolateToNullBins(obj)
            obj.SetDirectory(0)
        if stat and stat.InheritsFrom('TH1'):
            self.extrapolateToNullBins(stat)
            stat.SetDirectory(0)
        if syst and syst.InheritsFrom('TH1'):
            self.extrapolateToNullBins(syst)
            syst.SetDirectory(0)

    def extrapolateToNullBins(self,h):

        """ check for unfilled bins (may happen e.g. for muons...), currently only for 2D histos """

        if not h.InheritsFrom('TH2'): return

        toFill=[]
        nbinsx=h.GetNbinsX()
        nbinsy=h.GetNbinsY()
        for xbin in range(nbinsx):
            for ybin in range(nbinsy):
                val=h.GetBinContent(xbin+1,ybin+1)
                if val>0 : continue
                neighbors=[(xbin+i,ybin+j) for i in range(3) for j in range(3)]
                neighbors=[xy for xy in neighbors if xy!=(xbin+1,ybin+1) and xy[0]<nbinsx+1 and xy[0]>0 and xy[1]<nbinsy+1 and xy[1]>0]
                n_neighbors=len(n_neighbors)
                if n_neighbors==0 : continue
                sumSF    = [h.GetBinContent(*xy) for xy in neighbors]
                sumSFUnc = [h.GetBinError(*xy)   for xy in neighbors]
                toFill.append( (xy,sum(sumSF)/n_neighbors,sum(sumSFUnc)/n_neighbors) )
        
        if len(toFill)>0:
            print 'Will interpolate SF 2D histo',h.GetName(),'with',len(toFill),'values'

        for xy,val,valUnc in toFill:
            h.SetBinContent(xy[0],xy[1],val)
            h.SetBinError(xy[0],xy[1],valUnc)

    
    def addSFFromSource(self,tag,url,obj):
        
        """opens a ROOT file and stores the object containing the scale factors"""

        url=ROOT.gSystem.ExpandPathName(url)
        if not os.path.isfile(url) : 
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), url)

        fIn=ROOT.TFile.Open(url)
        sfObj = fIn.Get(obj)
        statObj = fIn.Get( obj + "_stat" )
        systObj = fIn.Get( obj + "_syst" )
        #print tag, url , obj, sfObj, statObj, systObj
        self.addSFObject(tag, sfObj, statObj, systObj)
        fIn.Close()
        
    def evalSF(self,tag,objAttrs):

        """
        evaluates the scale factors based on a tuple of object attributes
        returns a tuple with the nominal scale factor, and its binned uncertainty (if existing)
        """

        if not tag in self.sf_dict:
            return None

        sfVal=None
        sfObj=self.sf_dict[tag]['main']
        if sfObj.InheritsFrom('TH1'):

            hdxf=0.5*sfObj.GetXaxis().GetBinWidth(1)
            hdxl=0.5*sfObj.GetXaxis().GetBinWidth(sfObj.GetNbinsX())
            xbin = sfObj.GetXaxis().FindBin(
                max(sfObj.GetXaxis().GetXmin()+hdxf,min(sfObj.GetXaxis().GetXmax()-hdxl,objAttrs[0]))
            )

            if sfObj.InheritsFrom('TH2'):
                hdyf=0.5*sfObj.GetYaxis().GetBinWidth(1)
                hdyl=0.5*sfObj.GetYaxis().GetBinWidth(sfObj.GetNbinsY())
                ybin = sfObj.GetYaxis().FindBin(
                    max(sfObj.GetYaxis().GetXmin()+hdyf,min(sfObj.GetYaxis().GetXmax()-hdyl,objAttrs[1]))
                )

                xbin = sfObj.GetBin( xbin , ybin )

            
            val = sfObj.GetBinContent(xbin)
            stat_err = self.sf_dict[tag]['stat'].GetBinContent( xbin )-val if self.sf_dict[tag]['stat'] else sfObj.GetBinError(xbin)
            syst_err = self.sf_dict[tag]['syst'].GetBinContent( xbin )-val if self.sf_dict[tag]['syst'] else 0.0
            sfVal=(val, np.sqrt( stat_err**2 + syst_err**2 ) )
        else:
            sfVal=(sfObj.Eval(*objAttrs),0. )
          
        return sfVal


    def combineScaleFactors(self,sfList):

        sfVals=[x[0] for x in sfList]
        sfUncs=[x[1] for x in sfList]

        totalSF=np.prod(sfVals)
        for i,sf in enumerate(sfVals):
            sfUncs[i]= 0. if sf==0 else (sfUncs[i]/sf)**2
        totalSFUnc=totalSF*np.sqrt(sum(sfUncs))

        return (totalSF,totalSFUnc)
