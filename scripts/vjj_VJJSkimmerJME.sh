#! /bin/bash

export workingdirectory=$(pwd) #Write temporary output on HTcondor workingdir #Then moved to outdir defined in wrapper code by haddnano.py tool
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
echo "directory: "${workingdirectory}
cd ${workingdirectory};
ls -lart
pwd;
ls -lart ${workingdirectory}
echo "[--> Output dir: ${10}]"
/afs/cern.ch/user/y/yian/work/ewk_ajj/CMSSW_10_6_29/src/UserCode/VJJSkimmer/python/postprocessing/vjj_VJJSkimmerJME_postproc.py $@ --workingdir ${workingdirectory};
ls -lart ${workingdirectory}
#cp ${workingdirectory}/out*_Skim.root ${workingdirectory}/${10} 
mv ${workingdirectory}/out*_Skim.root ${workingdirectory}/out.root 
ls -lart ${workingdirectory}
