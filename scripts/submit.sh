for job in `cat submit_job`
do
 echo $job
 condor_submit $job

done
