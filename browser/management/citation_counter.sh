#!/usr/bin/env bash

#to run
#bash management/citation_counter.sh

#for i in {1950..2017}; do echo 'year:'$i; neo4j-shell -c "match (p:Pubmed) where p.processed = false and p.dcom < '$i' return count(distinct(p));"; done > neo4j_citation_years.txt;

for i in {1950..2017}; do echo 'year:'$i; neo4j-shell -c "match (p:Pubmed) where p.da < '$i' return count(p);"; done > pub_counts_per_year.txt;

#if interested in numbers of concepts
#for i in {1950..2017}; do echo 'year:'$i; neo4j-shell -c "match (p:Pubmed)-[r:SEM]-(s:SDB_triple) where p.da < '$i' return count(r);"; done > semmed_counts_per_year.txt;

paste <(cat pub_counts_per_year.txt | grep 'year' | cut -d ':' -f2) <(cat pub_counts_per_year.txt | grep '| ' | grep -v 'count' | cut -d '|' -f2 | sed 's/ //g') | tr '\t' ':' > citation_years.txt
