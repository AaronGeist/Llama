#!/bin/bash
cd "$1"
pwd
index=0
for i in *
do
    index=$(( $index + 1 ))
    indexStr=`printf "%02d" $index`
    extension=${i##*.}

    #echo $indexStr
    echo "$i -> $2_Vol.$indexStr.$extension"
	mv "$i" "$2_Vol.$indexStr.$extension"
done
