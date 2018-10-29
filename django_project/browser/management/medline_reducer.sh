#!/bin/sh
file=$1
touch $file.melodi
echo "Reading file - $file"
awk -v file="$file.melodi" -F " " 'BEGIN{l="f"}
#find the lines containing fields of interest, set flat 'l' to true and print line
{ if ($1 ~ /^TI/ || $1 ~ /^MH$/ || $1 ~ /^JT/ || $1 ~ /^DCOM/ || $1 ~ /^PMID/) {l="t"; print $0 > file; next};
#find overflow lines (start with spaces) after fields of interest and print
if (l=="t" && $0 ~ /^ /) {print $0 > file; l="t";}
else{l="f";}
}' $file
echo "Creating output file - $file.melodi.gz"
#gzip $file.melodi