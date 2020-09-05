#!/bin/bash

# example usage:
# calculateXSectionAndFilterEfficiency.sh -f datasets.txt -c Moriond17 -d MINIAODSIM -n 1000000 (-m)
# documentation
# https://twiki.cern.ch/twiki/bin/viewauth/CMS/HowToGenXSecAnalyzer#Automated_scripts_to_compute_the

# To obtain CERN SSO credentials (necessary to read from McM):
#   ./getCookie.sh

FILE='MINIAODS.lst'
CAMPAIGN='Moriond17'
DATATIER='MINIAODSIM'
EVENTS='10000000'
MCM=False
SKIPEXISTING=False
LINENUMBER=0

DEBUG=False
#DEBUG=True

export HOME=/afs/cern.ch/user/h/hbakhshi/
echo `pwd`
cd /afs/cern.ch/user/h/hbakhshi/work/VBFGamma/CMSSW_10_2_13/src/UserCode/VJJSkimmer/python/samples/xsections/
#cd /afs/cern.ch/user/h/hbakhshi/work/VBFGamma/CMSSW_10_2_13/src/GeneratorInterface/calculateXSectionAndFilterEfficiency/
echo `pwd`

export SCRAM_ARCH=slc7_amd64_gcc700
eval `scramv1 runtime -sh`
export X509_USER_PROXY=`pwd`/x509up_u12330

while getopts f:c:d:n:m:s:l: option
do
    case "${option}"
	in
        f) FILE=${OPTARG};;
        c) CAMPAIGN=${OPTARG};;
        d) DATATIER=${OPTARG};;
        n) EVENTS=${OPTARG};;
        m) MCM=True;;
        s) SKIPEXISTING=True;;
	l) LINENUMBER=${OPTARG};;

    esac
done


echo ${LINENUMBER}
mapfile -s ${LINENUMBER} -n 1 datasets < ${FILE}
export dataset=${datasets[0]::-1}
name="$dataset"
echo "Name read from file - $name"

echo 'compute_cross_section.py -f '${dataset}' -c '${CAMPAIGN}' -n '${EVENTS}' -d '${DATATIER}' --mcm "'${MCM}'" --skipexisting "'${SKIPEXISTING}'" --debug "'${DEBUG}'"'
output="$(python compute_cross_section.py -f "${dataset}" -c "${CAMPAIGN}" -n "${EVENTS}" -d "${DATATIER}" --mcm "${MCM}" --skipexisting "${SKIPEXISTING}" --debug "${DEBUG}")"
output="${output#*.txt}"
output="${output#*.txt}"
#echo ${output}

if [ "${DEBUG}" != "True" ]; then
    if [[ $output == *"cmsRun"* ]]; then
        eval ${output}
    else
        echo ${output}
    fi
else
    echo 'output'
    echo "${output}"
    exit 1
fi
echo ""


