#! /bin/bash

export workingdirectory=$(pwd)
echo $workingdirectory
echo "$(dirname "$0")"
cd "$(dirname "$0")"
#cd /afs/cern.ch/work/h/hbakhshi/VBFGamma/CMSSW_10_2_13/src/UserCode/VJJPlotter/scripts/
kernel_release=`uname -r`
case ${kernel_release} in

  *"el7"*)
	export SCRAM_ARCH=slc7_amd64_gcc700
    ;;
  *"el6"*)
	export SCRAM_ARCH=slc6_amd64_gcc700
    ;;
esac

echo ${kernel_release}
echo ${SCRAM_ARCH}
uname -a 

eval `scramv1 runtime -sh`;
cd ${workingdirectory};
ls -lart
pwd;
ls -lart ${workingdirectory}
echo "[--> Output dir: ${10}]"
$CMSSW_BASE/src/UserCode/VJJSkimmer/python/postprocessing/vjj_VJJSkimmerJME_postproc.py $@ --workingdir ${workingdirectory};
cp ${workingdirectory}/*.root ${10} #/afs/cern.ch/work/n/ntonon/public/VBFphoton/CMSSW_10_2_27/src/UserCode/VJJSkimmer/scripts/july20w2/TEST/2016/SinglePhoton_2016_B_v2 #Copy output rootfile manually, else missing #FIXME check
rm -rf ${workingdirectory}/*.root
ls -lart ${workingdirectory}
