#!/bin/bash
#mkdir -p archive
cd $1
for i in `ls`
do
    echo "$i"
	zip -r $i.zip $i
done
