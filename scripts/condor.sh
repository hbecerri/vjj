for file in `cat file_tmp`
do

 echo $file
# sed -n '/arguments/p' $file
# echo "***************\n"
 condor_submit $file

done
