for f in `cat file_tmp`
do
sed -i '2s/-S 22/-S -22/' $f

done
