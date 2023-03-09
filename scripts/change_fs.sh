for f in `cat file_tmp`
do
if [[ $f =~ 'all' ]];then
  sed -i 's/_182018/_all2018/' $f
fi

done
