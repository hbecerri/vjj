#! /bin/bash

export workingdirectory=$(pwd)
echo $workingdirectory
echo "$(dirname "$0")"
cd "$(dirname "$0")"
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
$CMSSW_BASE/src/UserCode/VJJSkimmer/python/postprocessing/vjj_final_postpro.py $@ --workingdir ${workingdirectory};
ls -lart ${workingdirectory}
rm -rf ${workingdirectory}/*.root
ls -lart ${workingdirectory}
