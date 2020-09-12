#!/bin/bash
mkdir -p archive
for i in `ls $1`
do
    echo "$i"
	zip -r archive/$i.zip $1/$i
done
