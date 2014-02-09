#!/bin/bash

dir=$1

if [ -z "$dir" ]; then
	echo usage: $0 expt-output-dir
	exit
fi

for d in $dir/*; do
	out=`cat $d/rate.txt | awk '$3 > 0 { sum += $3; count += 1; } END { print sum/count; }'`;
	echo $d -- $out Gbit;
done

