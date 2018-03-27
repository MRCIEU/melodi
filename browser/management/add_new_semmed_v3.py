import sys,gzip,time,resource,os
from csv import reader

sys.path.append("/Users/be15516/projects/melodi/")

import config

#4 steps
#1. Download num_files
#   Citations and Predication
#2. Convert each sql table to a pipe separated format
#	for i in *sql.gz; do echo $i; python ~/scripts/bristol/mysql_to_csv.py <(gunzip -c $i) | gzip > ${i%%.*}.psv.gz; done
#3. Get rid of double quotest in citations
#	gunzip -c semmedVER30_R_CITATIONS_to12312016.csv.gz | sed "s/'//g" | gzip > semmedVER30_R_CITATIONS_to12312016_edit.csv.gz
#4. Add new data - change file locations in script and run this script
#	python browser/management/add_new_semmed.py

#neo4j
from neo4j.v1 import GraphDatabase,basic_auth
auth_token = basic_auth(config.user, config.password)
driver = GraphDatabase.driver("bolt://"+config.server+":"+config.port,auth=auth_token)

#files
baseDir='/Users/be15516/mounts/rdfs_be15516/data/SemMedDB/v30_R_31-12-16/'
#SemMed
semCitation = baseDir+'semmedVER30_R_CITATIONS_to12312016_edit.csv.gz'
semPA = baseDir+'semmedVER30_R_PREDICATION_to12312016.csv.gz'

old_pmids='data/old_pmids.txt.gz'
new_pmids='data/new_pmids.txt.gz'

#getData metrics
#memory: 2973Mb
#Time taken: 16 minutes
def getData():
	print "Getting PubMed data from MELODI graph..."
	session2 = driver.session()
	pDic = {}
	start = time.time()

	#check if new pmids already created
	if os.path.isfile(new_pmids):
		print "Already generated new pmids "+new_pmids
	else:
		#check if old pmids already downloaded
		if os.path.isfile(old_pmids):
			print "Pubmed data already downloaded "+old_pmids
		else:
			#com="match (p:Pubmed)-[:SEM]-(s:SDB_triple) return distinct(p.pmid) as pmid;"
			#com="match (p:Pubmed)-[:SEM|:HAS_MESH]-() return distinct(p.pmid) as pmid;"
			com="match (p:Pubmed) where p.dp is not NULL return distinct(p.pmid) as pmid;"
			s = session2.run(com)
			counter=0
			for res in s:
				if counter % 1000000 == 0:
					print counter
					print "\ttime:", round((time.time() - start)/60, 1), "minutes"
					print "\tmemory: "+str(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1000000)+" Mb"
				#print res['pmid']
				counter+=1
				pDic[res['pmid']]=''
			print "Time taken for download:", round((time.time() - start)/60, 1), "minutes"
			print "Writing to file..."
			with gzip.open(old_pmids, 'wb') as f:
				for i in pDic:
					f.write(str(i)+"\n")
			print "Found "+str(len(pDic))+" PubMed IDs."

def getNewPmids():
	print "Finding new PubMed IDs..."
	newPDic = {}
	start = time.time()
	counter=0
	if os.path.isfile(new_pmids):
		print "New pubmed data already created "+new_pmids
	else:
		#get old pubmed ids in memory
		pDic = {}
		with gzip.open(old_pmids, 'rb') as f:
			for line in f:
				pDic[line.rstrip()]=''
		print "Time taken to read from file:", round(time.time() - start, 3), "seconds"

		with gzip.open(semPA, 'r') as f:
			for line in f:
				counter+=1
				if counter % 1000000 == 0:
					print counter
					print str(len(newPDic))
				l = line.split("|")
				pmid = l[2]
				if pmid not in pDic:
					#print l
					newPDic[pmid]=''
		print "Time taken:", round((time.time() - start)/60, 1), "minutes"
		print "Writing to file..."
		with gzip.open(new_pmids, 'wb') as f:
			for i in newPDic:
				f.write(str(i)+"\n")
		print "Time taken for download:", round((time.time() - start)/60, 1), "minutes"
		print "Found "+str(len(newPDic))+" new PubMed IDs"

def addNewPmids():
	pNew={}
	start = time.time()
	with gzip.open(new_pmids, 'rb') as f:
		for line in f:
			pNew[line.rstrip()]=''
	print "Time taken to read from file:", round(time.time() - start, 3), "seconds"

	print "Adding new PubMed data to graph..."
	#pmid:ID(Pubmed)|issn|:IGNORE|dcom|:IGNORE
	counter=0
	countAdd=0
	session2 = driver.session()
	#1|0006-2944|1975 Jun|1976 01 16|1975
	with gzip.open(semCitation, 'rb') as f:
		for line in f:
			counter+=1
			if counter % 1000000 == 0:
				print counter
			l = line.rstrip().split("|")
			pmid = l[0]
			issn = l[1]
			da = l[2]
			dcom = l[3]
			dp = l[4]
			if pmid in pNew:
				countAdd+=1
				if countAdd % 10000 == 0:
					print l
					print "Time taken:", round((time.time() - start)/60, 1), "minutes"
					print "Added "+str(countAdd)
					session2.close()
					session2 = driver.session()
				statement = "MERGE (n:Pubmed {pmid:"+pmid+"}) ON MATCH SET n.issn='"+issn+"',n.da='"+da+"',n.dcom='"+dcom+"',n.dp='"+dp+"' on CREATE SET n.issn='"+issn+"',n.da='"+da+"',n.dcom='"+dcom+"',n.dp='"+dp+"'"
				session2.run(statement)


def addNewSemMed():
	print "Adding new SemMed data to graph..."
	pNew={}
	start = time.time()
	with gzip.open(new_pmids, 'rb') as f:
	#with gzip.open('data/new_pmids_test.txt.gz', 'rb') as f:
		for line in f:
			pNew[line.rstrip()]=''
	print "Time taken to read from file:", round(time.time() - start, 3), "seconds"

	counter=0
	countAdd=0
	session2 = driver.session()
	#117403|248343|13930367|ISA|C0008059|Child|inpr|1|C0018684|Health|idcn|1
	#don't split inside quoted sections, e.g. 49963|341414|1|21065029|COEXISTS_WITH|"708|925"|"C1QBP|CD8A"|gngm|1|C0771648|Poractant alfa|orch|1
	with gzip.open(semPA, 'rb') as f:
		for line in reader(f, delimiter='|'):
			counter+=1
			if counter % 1000000 == 0:
				print "------ "+str(counter)+" ------"
			#l = line.rstrip().split("|")
			l = line
			pid=l[0]
			pmid=l[2]
			s_name = l[5].replace('"','\\"')
			predicate = l[3]
			o_name = l[9].replace('"','\\"')
			s_type = l[6]
			o_type = l[10]
			if pmid in pNew:
				#print pmid
				countAdd+=1
				if countAdd % 10000 == 0:
					print l
					print "Time taken:", round((time.time() - start)/60, 1), "minutes"
					print "Added "+str(countAdd)
					session2.close()
					session2 = driver.session()
				#check for dodgy pubmed ids with [2] in
				if pmid.isdigit():
					#statement="match (p:Pubmed{pmid:"+pmid+"}),(s:SDB_triple{s_name:'"+s_name+"',s_type:'"+s_type+"',o_name:'"+o_name+"',o_type:'"+o_type+"',predicate:'"+predicate+"'}) merge (p)-[:SEM]-(s);"
					statement='match (p:Pubmed{pmid:'+pmid+'}),(s:SDB_triple{s_name:"'+s_name+'",o_name:"'+o_name+'",predicate:"'+predicate+'"}) merge (p)-[:SEM]-(s);'
					session2.run(statement)

def fix():
	print "Fixing..."
	start = time.time()
	session2 = driver.session()
	counter=0
	with gzip.open('data/new_pmids_test.txt.gz', 'rb') as f:
		for line in f:
			pmid = line.rstrip()
			com = "match (p:Pubmed{pmid:"+pmid+"})-[r:SEM]-(s:SDB_triple) delete r;"
			#print com
			session2.run(com)
			counter+=1
			if counter % 100000 == 0:
				print "------ "+str(counter)+" ------"
				#session2.close()
				#session2 = driver.session()

	print "Time taken to read from file:", round(time.time() - start, 3), "seconds"

def main():
	#get the existing set of PubMed IDs
	#~15 minutes
	getData()

	#check for new ones using new SemMedDB data
	#~10 minutes
	getNewPmids()

	#add/update PubMed nodes
	#~130 minutes
	addNewPmids()

	#add new PubMed-SemMed relationships
	addNewSemMed()

	#fix()

if __name__ == "__main__":
    main()

#numbers
#before - match (p:Pubmed)-[:SEM]-(s:SDB_triple) return count(distinct(p.pmid));
#+-------------------------+
#| count(distinct(p.pmid)) |
#+-------------------------+
#| 15841558
