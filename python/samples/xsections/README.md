# Tools for cross section management

## Extract cross sections for each sample

Recipe is available on https://twiki.cern.ch/twiki/bin/viewauth/CMS/HowToGenXSecAnalyzer
The automated script is used on condor to calculated the cross section of each sample. 
List of MiniAOD samples was prepared using [scripts/ValidateSamples.py](scripts/ValidateSamples.py) script.
Small modifications are made to the standard package. Modified files are available here : [calculateXSectionAndFilterEfficiency.sh](calculateXSectionAndFilterEfficiency.sh) and [compute_cross_section.py](compute_cross_section.py). 
A [submit](submit) file is also created to submit jobs on condor. 

script [extract_xsections.py](extract_xsections.py) is used to parse the output files and produce [xsections.json](xsections.json) file


## Access xsections

import the current package

```
from UserCode.VJJSkimmer.samples.xsections import xsec
xsec['sample full name'] # returns the cross section value
```
