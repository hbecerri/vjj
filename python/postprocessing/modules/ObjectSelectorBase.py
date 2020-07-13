from abc import ABCMeta, abstractproperty, abstractmethod
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection 

class ObjectSelectorBase( Module ):
    __metaclass__ = ABCMeta

    def beginJob(self):
        pass

    def endJob(self):
        pass

    @abstractproperty
    def collection_name(self):
        pass

    @abstractproperty
    def obj_name(self):
        pass

    @abstractmethod
    def isGood(self, obj):
        pass

    @abstractmethod
    def fillSFs(self , objs , combined=True):
        pass

    def weight_names(self):
        return [ 'vjj_{0}_effWgt{1}'.format(self.obj_name() , var) for var in [ '' , 'Up' , 'Dn'] ]

    def mindr_toVetoObjs(self, obj):
        drs = [obj.DeltaR( a ) for a in self.vetoObjs ] or [float('inf')]
        mindr = min( drs  )
        return mindr
        
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        
        for brnch in self.weight_names():
            self.out.branch( brnch , 'F' , limitedPrecision=False )

        self.idx_branchName = 'vjj_{0}s'.format(self.obj_name() )
        self.out.branch( self.idx_branchName  , "b", lenVar='vjj_n{0}s'.format(self.obj_name() ) )
        
    def selectedObjs(self):
        return [ self.objects[idx]  for i,idx in enumerate(self.good_objectsIdx) if i <  self.nObjsForSF ]
        

    def analyze(self, event):
        self.out.fillBranch( self.idx_branchName , [] )
        for brnch in self.weight_names():
            self.out.fillBranch( brnch , -1 )

        self.vetoObjs = []
        for veto_coll, indices in self.vetoObjsInfo:
            veto_collection = Collection(event, veto_coll)
            selected_indices = getattr( event , "vjj_{0}s".format( indices ) )
            self.vetoObjs.extend( [veto_collection[i] for i in selected_indices] )


        self.objects = Collection( event , self.collection_name() )
        self.good_objectsIdx = [ i for i,obj in enumerate( self.objects ) if self.isGood( obj ) and i<250 ]

        self.out.fillBranch( self.idx_branchName , self.good_objectsIdx )
        
        SFs = self.fillSFs( self.selectedObjs() , True )
        
        for brnch in self.weight_names():
            self.out.fillBranch( brnch , SFs[brnch] )
            

        if self.doFilter :
            if len( self.good_objectsIdx ) >= self.nObjsForSF:
                return True
            else:
                return False
        else:
            return True

    def setParams(self, nObjsForSF, vetoObjs=[] , dofilter = False ):
        self.nObjsForSF = nObjsForSF
        self.vetoObjsInfo = vetoObjs
        self.doFilter = dofilter

    def __init__(self):
        pass
