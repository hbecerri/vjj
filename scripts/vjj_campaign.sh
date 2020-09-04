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
$CMSSW_BASE/src/UserCode/VJJSkimmer/scripts/vjj_campaign.py $@;
