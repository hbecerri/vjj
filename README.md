# VJJSkimmer

Tools for skimming and building of final ntuple analysis for V+2j analysis based on NanoAOD.
For more details on the analysis visit the twiki page: https://twiki.cern.ch/twiki/bin/view/CMS/AjjEWK

## Installation

```
export SCRAM_ARCH=slc7_amd64_gcc700
cmsrel CMSSW_10_2_13
cd CMSSW_10_2_13/src
cmsenv

#Higgs combination tool (see https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/)
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit
git fetch origin
git checkout v8.1.0
scram b
cd -

#nanoAOD tools
git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools
cd PhysicsTools/NanoAODTools
scram b
cd -

#SMP-19-005 framework (if ssh does not work for you switch to https)
git clone ssh://git@gitlab.cern.ch:7999/cms-ewkvjj/vjjskimmer.git UserCode/VJJSkimmer
cd UserCode/VJJSkimmer
scram b
```

## Skimming 

## Final ntuple production

The final V+2j selection at reco and gen level runs on NanoAOD ntuples and saves a summary tree for the analysis.
The code can be found under `python/postprocessing/modules`:

* `VJJSelector.py` steers the selection of the basic objects and the call to the final V+2j selection
* `VJJEvent.py` holds the final variables to store in the ntuple and applies the final V+2j selection
* `{Photon,Muon,Electron,Jet}Selector.py` perform basic selection on the objects and compute the corresponding scale factors
* `ScaleFactorBase.py` holds generic functions to read and evaluate scale factors from TH1, TGraph or TF1
* the `etc` sub-directory contains configuration files, scale factor ROOT files etc which are used by the selection code

A wrapper is available in `python/postprocessing/vjj_postproc.py` to build the command to run the code.
You can inspect its options with `-h`. An example of how to run it is give below:

```
python python/postprocessing/vjj_postproc.py \
       -i root://cms-xrd-global.cern.ch//store/mc/RunIIFall17NanoAODv6/GJets_Mjj-500_SM_5f_TuneCP5_EWK_13TeV-madgraph-pythia8/NANOAODSIM/PU2017_12Apr2018_Nano25Oct2019_102X_mc2017_realistic_v7-v1/260000/45CA9950-BD37-374A-8604-AC35C9446A0F.root \
       -N 5000
```


## Instructions for continuous integration

A basic set of scripts are run everytime the code is pushed to gitlab. These test are defined in `.gitlab-ci.yml`. 
Special instructions are given below on how to prepare the final validation based on the comparison of the cutflow histograms.

1 the first step is to define the directory to be used as reference for the continuous integration and the samples to be copied over in `python/postprocessing/etc/testDatasets.py`
1 run locally `python/postprocessing/vjj_basetests.py` to prepare the continuous integration directory. The script will copy over the samples and prepare a summary pickle file with the cutflow expected using the current snapshot of the code. See below for an example of how to run
1 update .gitlab-ci.yml if needed for the command to run automatically in gitlab

The `vjj_basetests.py` can be run locally with:
```
python python/postprocessing/etc/testDatasets.py --prepare 2016,data 2016,mc 2017,data 2017,mc 2018,data 2018,mc
```
Omitting the `--prepare` option will simply run the skims and compare the cutflows with the ones stored by default
 