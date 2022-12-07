ls /eos/user/y/yian/AJJ_analysis/$2_$3_$1/Skim_$1_*.root >file_$1
dir=/eos/user/y/yian/AJJ_analysis/$2_$3_$1/
cp ${2}_${3}fake_vjj_VJJSkimmerJME.submit ${2}_${3}fake_vjj_VJJSkimmerJME.resubmit
job="${2}_${3}fake_vjj_VJJSkimmerJME.resubmit"
if [[ -f tmp ]];then
   rm tmp
fi



j=0
for((i=0;i<=$4;i++ ))
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
