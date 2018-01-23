#!/usr/bin/env bash

#generate test set
#gunzip -c semmedVER25_PREDICATION_AGGREGATE_to12312015.psv.gz | head -n 100 | gzip > semmedVER25_PREDICATION_AGGREGATE_to12312015_100.psv.gz
#gunzip -c semmedVER25_PREDICATION_AGGREGATE_to12312015_100.psv.gz | cut -d "|" -f4 | sort | uniq | tr '\n' '|'
#gunzip -c semmedVER25_CITATIONS_to12312015.psv.gz | egrep -w '16691646|16691650|16691651|16691653|16691656|16691659|16691660|16691661|16691671|16691673|16691677|16691678|16691679|16691681|16691688|16691689|16691690|16691695|16691697|16691699|16691702|16691703|16691704|16691706|16691711|16691714|16691716|16691719|16691720|16691723|16691725|16691731|16691732|16691736|16691737|16691741|16691742|16691743|16691744|16691748|16691749|16691750|16691751|16691752|16691753|16691754|16691755|16691757|16691758|16691761|16691762|16691763|16691764|16691765|16691770|16691771|16691774|16691776|16691777|16691781|16691782|16691785|16691788|16691790|16691795|16691796|16691799|16691802|16691807|16691811|16691812|16691813|16691815|16691816|16691820|16691823|16691837|16691840|16691847|16691848|16691850|16691856|16691862|16691863' | gzip > semmedVER25_CITATIONS_to12312015_100.psv.gz


#server
#PRE=''

#local
PRE=''

DPATH=$PRE/software/neo4j/neo4j-enterprise-3.0.0/data/databases/neo4j3_db

NPATH=$PRE/data/mesh/freq_count_files/

MPATH=$PRE/data/mesh/hierarchy/
MRPATH=$PRE/data/mesh/MRCOC/
MRPATH2=$PRE/data/mesh/extra/

#SemMed files

sem_triple=semmed_processed/semmed_triple.txt.gz
#v25
SPATH=$PRE/data/SemMedDB/v12312015/
sem_citations_edit=semmedVER25_CITATIONS_to12312015_edit.psv.gz
sem_citations=semmedVER25_CITATIONS_to12312015.psv.gz
sem_pred_ag=semmedVER25_PREDICATION_AGGREGATE_to12312015.psv.gz

#existing user data
UPATH=$PRE/data/melodi/

neo4j stop

if [ -d $DPATH ]; then
	echo "Deleting db..."
	rm -r $DPATH
fi

if [ -s $SPATH/$sem_citations_edit ]
then
    echo 'Citations file already edited'
else
    echo 'Creating modified Citations file...'
    gunzip -c $SPATH/$sem_citations | sed "s/'//g" | gzip > $SPATH/semmedVER26_CITATIONS_R_to04302016_edit.psv.gz
fi

echo $NPATH/MH_freq_count.gz

neo4j-import --into $DPATH --delimiter "|" \
--nodes:SearchSet $UPATH/user_data_node_headers.psv,$UPATH/user_nodes.psv \
--nodes:Mesh $NPATH/MH_freq_count_headers.txt,$NPATH/MH_freq_count.gz \
--nodes:Mesh $NPATH/MH_SH_freq_count_headers.txt,$NPATH/MH_SH_freq_count.gz \
\
--nodes:Pubmed $SPATH/semmedVER25_CITATIONS_headers.csv,$SPATH/$sem_citations_edit \
--nodes:Pubmed $MRPATH2/mesh_extra_pubmed_headers.txt,$MRPATH2/pubmed_01_01_2016__03_08_16.txt.gz \
\
--nodes:SDB_triple $SPATH/semmed_processed/semmed_triple_headers.psv,$SPATH/$sem_triple \
--nodes:SDB_item $SPATH/semmed_processed/semmed_item_headers.psv,$SPATH/semmed_processed/semmed_merged_data.txt.gz \
\
--nodes:MeshTree $MPATH/meshTreeNodes_header.txt,$MPATH/meshTreeNodes.txt \
\
--relationships:HAS_MESH $MRPATH/mesh_relations_headers.txt,$MRPATH/detailed_CoOccurs_2016_uniq_zy.neo4j.txt.gz \
--relationships:HAS_MESH $MRPATH2/mesh_relations_headers.txt,$MRPATH2/mesh_01_01_2016__03_08_16.txt.gz \
\
--relationships:MP $MPATH/meshTreeRels_header.txt,$MPATH/meshTreeRels.txt \
\
--relationships:SEM $SPATH/semmedVER25_PREDICATION_AGGREGATE_relations_headers.psv,$SPATH/$sem_pred_ag \
--relationships:SEMS $SPATH/semmed_subject_relations_headers.psv,$SPATH/$sem_triple \
--relationships:SEMO $SPATH/semmed_object_relations_headers.psv,$SPATH/$sem_triple \
\
--relationships:INCLUDES $UPATH/user_data_rel_headers.psv,$UPATH/user_info.psv \
--skip-duplicate-nodes true --bad-tolerance 100000000000


neo4j start

sleep 10


#indexes

#search sets
neo4j-shell -c 'CREATE index on :SearchSet(name);'
#neo4j-shell -c 'CREATE index ON :SearchSet(user_id);'

#mesh
neo4j-shell -c 'CREATE index ON :Mesh(mesh_name);'
neo4j-shell -c 'CREATE index ON :Mesh(mesh_id);'
neo4j-shell -c 'CREATE index on :MeshTree(tree_id);'
neo4j-shell -c 'CREATE index on :MeshTree(mesh_name);'

#SemMedDB
#neo4j-shell -c 'CREATE CONSTRAINT ON (p:Pubmed) ASSERT p.pmid IS UNIQUE ;'
neo4j-shell -c 'CREATE index on :Pubmed(pmid);'
neo4j-shell -c 'CREATE index on :Pubmed(dcom);'
neo4j-shell -c 'CREATE index on :SDB_triple(pid);'
neo4j-shell -c 'CREATE index on :SDB_triple(s_name);'
neo4j-shell -c 'CREATE index on :SDB_triple(o_name);'
neo4j-shell -c 'CREATE index on :SDB_item(name);'
neo4j-shell -c 'CREATE index on :SDB_item(i_freq);'
neo4j-shell -c 'CREATE index on :SDB_item(s_freq);'
neo4j-shell -c 'CREATE index on :SDB_item(o_freq);'

#sleep 1000

#warm up the cache
#START n=node(*) OPTIONAL MATCH (n)-[r]->() WITH count(n.property_i_do_not_have) + count(r.property_i_do_not_have) as counted RETURN counted;
