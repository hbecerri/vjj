<!--
```
CODE EXAMPLE
```

=== Emoji list (see https://gist.github.com/rxaviers/7360908)
:arrow_right:
:information_source:
:heavy_exclamation_mark:
:heavy_check_mark:
:link:
:white_check_mark:
:heavy_multiplication_x:
:x:
:negative_squared_cross_mark:
:bangbang:
:white_check_mark:
:copyright:
:clock430:
:no_entry:
:ok:
:arrow_right_hook:
:paperclip:
:open_file_folder:
:chart_with_upwards_trend:
:lock:
:hourglass:
:warning:
:construction:
:fr:
:one: :two: :hash:
:underage:
:put_litter_in_its_place:
:new:


#HOW TO HIDE CONTENTS (which can be viewed by cliking icon) :
<details>
<summary>[NameOfHiddenContent]:</summary>
[theHiddenContent]
</details>
-------------------------------------------->
:construction: **README UNDER CONSTRUCTION**


Tools for skimming and building of final ntuple analysis for V+2j analysis based on NanoAOD.
For more details on the analysis visit the [Twiki page](https://twiki.cern.ch/twiki/bin/view/CMS/AjjEWK).


[[_TOC_]]


## Installation

```
export SCRAM_ARCH=slc7_amd64_gcc700
cmsrel CMSSW_10_2_13
cd CMSSW_10_2_13/src
cmsenv

#-- Higgs combination tool (see https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/)
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit
git fetch origin
git checkout v8.1.0
scram b
cd -

#-- nanoAOD tools
git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools
cd PhysicsTools/NanoAODTools
scram b
cd -

#-- SMP-19-005 framework (if ssh does not work, use https)
git clone ssh://git@gitlab.cern.ch:7999/cms-ewkvjj/vjjskimmer.git UserCode/VJJSkimmer
#git clone https://gitlab.cern.ch/cms-ewkvjj/vjjskimmer.git UserCode/VJJSkimmer
cd UserCode/VJJSkimmer
scram b
```

## 'Big ntuples' production

The final V+2j selection at reco and gen level runs on NanoAOD ntuples and saves a summary tree for the analysis.
The code can be found under `python/postprocessing/modules`:

* `VJJSelector.py` steers the selection of the basic objects and the call to the final V+2j selection
* `VJJEvent.py` holds the final variables to store in the ntuple and applies the final V+2j selection
* `{Photon,Muon,Electron,Jet}Selector.py` perform basic selection on the objects and compute the corresponding scale factors
* `ScaleFactorBase.py` holds generic functions to read and evaluate scale factors from TH1, TGraph or TF1
* the `etc` sub-directory contains configuration files, scale factor ROOT files etc which are used by the selection code

#### Run the code

A wrapper is available in `python/postprocessing/vjj_postproc.py` to build the command to run the code. You can inspect its options with `-h`.

- Example command to run interactively (in `python/postprocessing`):
```
voms-proxy-init --rfc --voms cms --hours 192 #Renew proxy

#-- Make sure that your file exists (via DAS)
#-- Make sure you run on UltraLgacy reconstruction
python vjj_postproc.py -i root://cms-xrd-global.cern.ch//store/mc/RunIISummer20UL16NanoAODv9/GJets_DR-0p4_HT-400To600_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_mcRun2_asymptotic_v17-v2/230000/9EA5E2CC-2DB3-6B4E-BA71-B56D3244B10B.root -N 5000 -y 2016 -S 22
```

- Example command to run via CRAB (in `python/scripts`):
```
#-- SUBMIT
python vjj_crab.py submit

#--year X <-> process only samples of year 'X'
#-d X <-> process only the specific sample 'X'
#--datasetkey X <-> process only samples whose names contain 'X'
#--runcommands <-> run commands; else, only prints them to stdout
#More options available
```

:arrow_right: Submit crab jobs. The config file is based on the template `python/etc/crab_cfg.py`, with overriding options `outLFNDirBase` / `inputDataset` / `workArea`.
The crab job runs the script `crab_script.sh`, which in turn calls the `vjj_postproc.py` wrapper with arguments `--inputfiles=crab` (needed to process file via CRAB) and `--dataSet` set to the proper dataset DAS name.


## 'Skimmed ntuples' production

In `python/postprocessing/modules/`, the `VJJSkimmerJME.py` is used to skim big ntuples and only retain events entering the final categories. It calls `BDTReader.py` and `ReadComputeObservables_VJJSkimmerJME.py` to (re)compute the MVA and other relevant observables, individually for each JME variation.
This code varies an individual output TTree for the nominal scenario, and for each JME variation.
Different branch selections may be applied to the nominal/shifted TTrees, via independent keep/drop instruction files.

The wrapper code `vjj_VJJSkimmerJME_postproc.py` chains the different modules: it calls the nanoAOD `jetmetHelperRun2` module, then calls JetSelector once per JME variation to obtain varied jet collections (nominal collection read directly from big ntuples), and finally the skimmer code.
You can specify there the JEC/JER variations to process.
In the PostProcessor call, one can specify preselection cuts (to speed up the processing) and JSON luminosity masks to apply to data.

#### Run the code

- Example command to run interactively (in `python/postprocessing`):
```
python vjj_VJJSkimmerJME_postproc.py -c PhotonData_16 -o . --workingdir . -d /SinglePhoton/Run2016H-UL2016_MiniAODv2_NanoAODv9-v1/NANOAOD --nfilesperchunk 1 --chunkindex 0 -N 1000 -S 22   -> Esto es para nano_v9

#-c <-> campaign file, must be found in `python/samples/campaigns/`
#-o <-> outputdir, where to write the final output files
#--workingdir <-> where to write the tmp output files (before call to haddnano.py to merge all tmp outputs)
#-d <-> name of dataset to process
#-nfilesperchunk x <-> will chain x files per chunk, i.e. process x files per run/job (use 1 file per job by default for skimmer)
#--chunkindex x <-> run on the xth chunk of files
#-N x <-> only process the x first events
#More options available
```

- Example command to run via HTCondor (in `python/scripts`):
```
python vjj_VJJSkimmerJME.submit.py -c july20new --baseoutdir . -o TEST -d SinglePhoton_2016_B_v2 #Create the config file

condor_submit vjj_VJJSkimmerJME.submit #Submit the jobs

#-c <-> campaign file, must be found in `python/samples/campaigns/`
#--baseoutdir<-> where to write the final output files (BASE)
#-o <-> where to write the final output files (SUFFIX)
#-d <-> name of dataset to process; if empty, process all datasets
#More options available
```

:information_source: The user can configure this code to define a list of years/sample keywords to process (to avoid processing useless samples).

:arrow_right: Once all jobs are finished, rerunning the same command will reproduce a config file including only failed jobs.
Since these jobs likely failed due to memory consumption, it is better to split them in smaller chunks of e.g. 100K events, by adding the additional options `--splitjobs --neventsperjob 100000`.
Repeat with smaller values until all jobs are completed.

## Compute the integrated luminosities

The integrated recorded luminosity corresponding to a given trigger path may be computed using `brilcalc`.

:arrow_right: See the dedicated [Twiki](https://twiki.cern.ch/twiki/bin/viewauth/CMS/BrilcalcQuickStart).

- Example command to compute the recorded luminosity recorded by the trigger path `HLT_Photon175_v`:
```
#Go to lxplus, cmsenv (?)

export PATH=$HOME/.local/bin:/cvmfs/cms-bril.cern.ch/brilconda/bin:$PATH #Set up env

pip install --user --upgrade brilws #Make sure latest version installed

brilcalc lumi --normtag /cvmfs/cms-bril.cern.ch/cms-lumi-pog/Normtags/normtag_PHYSICS.json -u /fb -i /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions16/13TeV/ReReco/Final/Cert_271036-284044_13TeV_ReReco_07Aug2017_Collisions16_JSON.txt --hltpath "HLT_Photon175_v*" #Adapt JSON and trigger path to your needs
```

## Create a new campaign file

When processing ntuples, one must refer to a campaign file listing the filepaths, cross sections, etc. These files can be found under `python/samples/campaigns/`.

Below are example commands to create a new campaign file:

```
cd scripts

#-- [MAKE] <-> interactive; specify dataset(s) and years(s) #Can consider only one year/sample with:
./vjj_campaign.sh make -d /eos/bigNtuplesDir -c myCampaign #--year 16 --sample PhotonData <-> will consider only 2016 samples containing the 'PhotonData' keyword

#-- [SUBMIT] (all datasets) <-> HTcondor; runs [make] on all years/datasets
./vjj_campaign.sh submit -d /eos/bigNtuplesDir -c myCampaign

#-- [MERGE] (all datasets) <-> inetactive; merges all outputs from condor jobs
./vjj_campaign.sh merge -d /eos/bigNtuplesDir -c myCampaign

#-- Verify the output JSON file, and add its parent information
voms-proxy-init --rfc --voms cms --hours 192 #Renew proxy (need to access DAS -- cf. GetParent() function)
python #Interactive python

>from UserCode.VJJSkimmer.samples.campaigns.Manager import Manager as CampaignManager
>campaign = CampaignManager('july20new')
>ds_name = '/SinglePhoton/Run2016D-02Apr2020-v1/NANOAOD' #Random samplename
>campaign.get_dataset_info(ds_name)
```

## Instructions for continuous integration

:construction: **TO VERIFY**

<details>
<summary>Instructions</summary>
A basic set of scripts are run everytime the code is pushed to gitlab. These test are defined in `.gitlab-ci.yml`.
Special instructions are given below on how to prepare the final validation based on the comparison of the cutflow histograms.

1. the first step is to define the directory to be used as reference for the continuous integration and the samples to be copied over in `python/postprocessing/etc/testDatasets.py`
1. run locally `python/postprocessing/vjj_basetests.py` to prepare the continuous integration directory. The script will. copy over the samples and prepare a summary pickle file with the cutflow expected using the current snapshot of the code. See below for an example of how to run
1. update .gitlab-ci.yml if needed for the command to run automatically in gitlab

The `vjj_basetests.py` script can be run locally with:

```
python python/postprocessing/vjj_basetests.py --prepare 2016,data 2016,mc 2017,data 2017,mc 2018,data 2018,mc
```

Omitting the `--prepare` option will simply run the skims and compare the cutflows with the ones stored by default.
Note: you may need to start a proxy before running the `prepare` step.
</details>
