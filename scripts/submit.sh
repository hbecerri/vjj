for i in 16
do
  echo ${i}
  for file in `cat sample_20${i}`
  do
#  echo $file 
     echo "python vjj_VJJSkimmerJME.submit.py -c DoubleMuData_16 --baseoutdir ./ -o TEST -d $file -y 20$i"
     python vjj_VJJSkimmerJME.submit.py -c DoubleMuData_16 --baseoutdir ./ -o TEST -d $file -y 20$i
  done
done
