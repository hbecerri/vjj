#!/bin/bash
ls *.json >file
for f in `cat file`
do
fname=`echo $f | awk -F. '{print $1}'`
mv $f $fname
echo $fname
done


