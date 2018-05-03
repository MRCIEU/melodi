import sys,gzip,time,resource,os

#from mrcoc_parser import *
from add_new_semmed_v3 import getpubmedData
sys.path.append("/Users/be15516/projects/melodi/")
import config

#steps
# 1. Get data for existing mesh-pmid
# 2. Get data for existing mesh terms
# 3. Get new data
# wget https://mbr.nlm.nih.gov/Download/RawData/
# 4. Edit data
# gunzip -c Full_MH_SH_items.gz | awk -F '|' '$3==1' | gzip > Full_MH_SH_items_main.gz
# 5. Run this script

from neo4j.v1 import GraphDatabase,basic_auth
auth_token = basic_auth(config.user, config.password)
driver = GraphDatabase.driver("bolt://"+config.server+":"+config.port,auth=auth_token)

def get_data_from_graph(dType):
	print "Getting",dType,"data from MELODI graph..."
	session2 = driver.session()
	valDic = {}
	start = time.time()

	old_data='data/old_'+dType+'.txt.gz'

	#check if data already downloaded
	if os.path.isfile(old_data):
		print "Already retrieved",dType,"data"
	else:
		if dType == 'pmids':
		#com="match (p:Pubmed)-[:SEM]-(s:SDB_triple) return distinct(p.pmid) as pmid;"
			com="match (p:Pubmed)-[:HAS_MESH]-(m:Mesh) return distinct(p.pmid) as val;"
		elif dType == 'mesh':
			com="match (m:Mesh) return distinct(m.mesh_name) as val;"

		print com
		#com="match (p:Pubmed) where p.dp is not NULL return distinct(p.pmid) as pmid;"
		s = session2.run(com)
		counter=0
		for res in s:
			if counter % 1000000 == 0:
				print counter
				print "\ttime:", round((time.time() - start)/60, 1), "minutes"
				print "\tmemory: "+str(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1000000)+" Mb"
			#print res['pmid']
			counter+=1
			valDic[res['val']]=''
		print "Time taken for download:", round((time.time() - start)/60, 1), "minutes"
		print "Writing to file..."
		with gzip.open(old_data, 'wb') as f:
			for i in valDic:
				f.write(str(i)+"\n")
		print "Found "+str(len(valDic))+" values."


#get pubmed IDs
def getpubmedData():
	get_data_from_graph('pmids')


def getMeshData():
	get_data_from_graph('mesh')

#read new mesh data
mesh_file='/Users/be15516/mounts/rdfs_mrc/users/be15516/data/mesh/raw_data/2017/Full_MH_SH_items_main.gz'
def parse_mesh():

	print 'Reading in old pmids...'
	pDic = {}
	with gzip.open('data/old_pmids.txt.gz', 'rb') as f:
		for line in f:
			pDic[line.rstrip()]=''

	print 'Reading in old mesh terms...'
	mDic = {}
	with gzip.open('data/old_mesh.txt.gz', 'rb') as f:
		for line in f:
			mDic[line.rstrip()]=''

	print 'parsing ',mesh_file
	o1 = gzip.open('data/new_pmids.txt.gz', 'wb')
	o2 = gzip.open('data/new_mesh_and_pmids.txt.gz', 'wb')
	with gzip.open(mesh_file, 'r') as f:
		for line in f:
				t,q,main,pmid,y1,y2,y3 = line.split('|')
				if pmid not in pDic:
					meshName = t
					if len(q)>0:
						meshName = t+'/'+q
					if meshName not in mDic:
						o2.write(meshName+'\t'+pmid+'\n')
					else:
						o1.write(meshName+'\t'+pmid+'\n')
	o.close()

if __name__ == "__main__":
	#getpubmedData()
	getMeshData()
	parse_mesh()
