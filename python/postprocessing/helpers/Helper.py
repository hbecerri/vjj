from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from ColoredPrintout import *

# //--------------------------------------------
# //--------------------------------------------

def lineno():
    """Returns the current line number in our program."""
    import inspect
    return inspect.currentframe().f_back.f_lineno


def Get_Updated_JetCollection_JMEvar(event, JMEvar=''):
    '''
    Returns an updated jet collection after corresponding to the JME variation given in argument
    NB: same ordering as original jet collection (<-> sorted according to nominal pt); but this will get re-sorted based on updated pt after jet selection in FillJMEObservables()
    '''

    #-- Copy original jet collection
    jets_new = Collection(event, 'Jet')
    if JMEvar == '': return jets_new

    suffix = '_jes{}'.format(JMEvar) #Default: JEC variation suffix (as in: event.Jet_pt_jesTotalUp)
    if JMEvar == 'JERUp': suffix = '_jerUp' #JERUp suffix
    elif JMEvar == 'JERDown': suffix = '_jerDown' #JERDown suffix

    #-- Retrieve arrays of JME-varied pt/m for all jets in the event
    pt_new = eval('event.Jet_pt{}'.format(suffix))
    mass_new = eval('event.Jet_mass{}'.format(suffix))
    # print('pt_new', pt_new); print('mass_new', mass_new)

    #-- Update the pt/m of all jets in the event
    for ijet, jet in enumerate(jets_new):
        jets_new[ijet].pt = pt_new[ijet]
        jets_new[ijet].m = pt_new[ijet]

    #-- Return updated jet collection
    return jets_new


def Convert_Chars_toIntegers(list_chars):
    '''
    Good object indices get stored as bytes 'b' to minimize disk space
    When reading array from branch and iterate over elements, get error: TypeError: iter() returned non-iterator of type 'Iterator_t<TTreeReaderArray<unsigned char> >'
    ---> Need to convert each element back to integer, using the ord() method to convert unicode -> int
    '''

    return [ord(list_chars[i]) for i in range(len(list_chars))] 

# //--------------------------------------------
# //--------------------------------------------
