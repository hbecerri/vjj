#!/bin/bash



for i in {0..66}
do
python vjj_VJJSkimmerJME_postproc.py -c DYJetsNLO_16 -o . --workingdir . -d /DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16NanoAODAPVv9-106X_mcRun2_asymptotic_preVFP_v11-v1/NANOAODSIM --nfilesperchunk 1 --chunkindex $i -S 169
done


#for i in {0..21}
#do
#python vjj_VJJSkimmerJME_postproc.py -c DYJetsNLO_16 -o . --workingdir . -d /DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16NanoAODv9-106X_mcRun2_asymptotic_v17-v1/NANOAODSIM --nfilesperchunk 1 --chunkindex $i -S 169
#done

#python vjj_VJJSkimmerJME_postproc.py -c DYJetsNLO_16 -o . --workingdir . -d /DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16NanoAODv9-106X_mcRun2_asymptotic_v17-v1/NANOAODSIM --nfilesperchunk 1 --chunkindex $i -S 169

#python vjj_VJJSkimmerJME_postproc.py -c WJetsToLNu_16 -o . --workingdir . -d  /WJetsToLNu_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16NanoAODAPVv9-106X_mcRun2_asymptotic_preVFP_v11-v2/NANOAODSIM --nfilesperchunk 1 --chunkindex $i -S 169

#python vjj_VJJSkimmerJME_postproc.py -c TTTo2L2NuPowheg -o . --workingdir . -d  /TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODAPVv9-106X_mcRun2_asymptotic_preVFP_v11-v1/NANOAODSIM --nfilesperchunk 1 --chunkindex $i -S 169



