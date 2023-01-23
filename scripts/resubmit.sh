# process ID *_myCampaign_syst CampaignFile (PhotonData_all) year total num
echo "${2} ${3}"
ls /eos/user/y/yian/AJJ_analysis/$2/$3_${4}_$1/Skim_$1_*.root >file_$1
dir=/eos/user/y/yian/AJJ_analysis/$2/$3_$1/
cp ${2}_${3}${4}_vjj_VJJSkimmerJME.submit ${2}_${3}${4}_vjj_VJJSkimmerJME.resubmit
job="${2}_${3}${4}_vjj_VJJSkimmerJME.resubmit"
if [[ -f tmp ]];then
   rm tmp
fi



j=0
for((i=0;i<=${5};i++ ))
do
  file=Skim_$1_${i}.root
  if [[  -f $dir${file} ]];then
     line=$[$i+18-$j]
     echo $i $j $line
     sed -i "$line d" $job
     j=$[$j+1]
     echo $i $j $line"******************"
  else
     line=`expr $i + 18`
     sed -n "$line p" $job > tmp
  fi
done
#sed -i '18,$d' DoubleEG_2016_vjj_VJJSkimmerJME.resubmit
#for line in `cat tmp`
#do
# echo $line
#
#done
