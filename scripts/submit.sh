for i in 18
do
  echo ${i}
  for file in `cat sample_20${i}`
  do
#  echo $file 
     echo "python vjj_VJJSkimmerJME.submit.py -c GJetsNLO_100To150_${i}  --baseoutdir ./ -o TEST -d $file -y 20$i"
     python vjj_VJJSkimmerJME.submit.py -c GJetsNLO_100To150_${i}  --baseoutdir ./ -o TEST -d $file -y 20$i
  done
done
