Steps to setup application

1. Download SemMedDB data
    - https://skr3.nlm.nih.gov/SemMedDB/

2. Process SemMedDB data
    - Convert sql to psv using mysql_to_csv.py
    - If first time convert psv to neo4j input format using SemMedDB_process.py
    - If adding new data use add_new_semmed.py

3. Download MeSH data
    - https://mbr.nlm.nih.gov/MRCOC/detailed_CoOccurs_2016.txt.gz
    - Pubmed search ("2016/01/01"[Date - Publication] : "3000"[Date - Publication]) and export as MEDLINE
    - Compress - medline_reducer.sh

4. Process MeSH data
    - mrcoc_parser.py
    - mesh_tree.py
    - mesh_medline_to_neo4j.py

5. Create graph
    - load_db.sh

6. Update year frequencies when new data added
    - calculate_year_freqs.py
		- MATCH (p:Pubmed)-[:SEM]-(s:SDB_triple) where p.da > '2017'  with count(distinct(p)) as cp,s set s.freq_2017 = s.freq_2016+cp;
