import sys,os,re,gzip,time
from collections import defaultdict

home='./'

import config
from neo4j.v1 import GraphDatabase,basic_auth

auth_token = basic_auth(config.user, config.password)
driver = GraphDatabase.driver("bolt://"+config.server,auth=auth_token)

session = driver.session()

#yRange = range(1950,2017)
yRange = range(2016,2018)

def get_mesh(yRange):
	print "Getting MeSH data..."
	cmd="MATCH (p:Pubmed)-[:HAS_MESH]-(m:Mesh) where p.da < '"+str(yRange[-1]+1)+"' RETURN p.pmid,p.da,m.mesh_name;"
	print cmd
	result = session.run(cmd)

	with gzip.open(home+'data/mesh_freqs.tsv.gz', 'wb') as f:
		for r in result:
			f.write(str(r['p.pmid'])+'\t'+r['p.da'].encode('utf-8')+'\t'+r['m.mesh_name'].encode('utf-8')+'\n')

def get_semmed(yRange):
	print "Getting SemMedDB data..."
	cmd="MATCH (p:Pubmed)-[:SEM]-(s:SDB_triple) where p.da > '"+str(yRange[0])+"' and p.da < '"+str(yRange[-1]+1)+"' RETURN p.pmid,p.da,s.pid;"
	print cmd
	result = session.run(cmd)

	with gzip.open(home+'data/semmed_freqs.tsv.gz', 'wb') as f:
		for r in result:
			f.write(str(r['p.pmid'])+'\t'+r['p.da']+'\t'+str(r['s.pid'])+'\n')

def parse(file):
	print "Parsing "+file+" ..."
	counter=0
	dataDic = defaultdict(dict)

	with gzip.open(file+".tsv.gz", 'rb') as f:
		for line in f:
			counter+=1
			if counter % 1000000 == 0:
				print counter
			pmid,da,term = line.rstrip().split("\t")
			da=da.split(" ")[0]
			if da in dataDic[term]:
				dataDic[term][da].append(pmid)
			else:
				dataDic[term][da] = [pmid]
	#print meshDic
	freqDic = {}

	print "Counting..."
	for term in dataDic:
		oldVal = 0
		#print "\t"+term
		freqDic[term] = []
		for i in yRange:
			i = str(i)
			if i in dataDic[term]:
				v = len(dataDic[term][i])
				total = v + oldVal
				#print i + ":" + term + ":" + str(meshDic[term][i]) + ":" + str(v) + ":" + str(oldVal) + ":" + str(total) + "\n"
			else:
				total = oldVal
				#print i + " : " + str(total)
			freqDic[term].append(str(total))
			oldVal = total
	#print meshFreqDic

	print "Writing freqs to file..."
	meshFreqs = file+'_neo4j.psv.gz'
	with gzip.open(meshFreqs, 'wb') as f:
		f.write("Term")
		for i in yRange:
			f.write("|"+str(i))
		for term in freqDic:
			f.write("\n"+term+"|")
			f.write("|".join(freqDic[term]))

def update_graph(file,type):
	meshFreqs = file+'_neo4j.psv.gz'
	countAdd=0
	start = time.time()
	session = driver.session()
	with gzip.open(meshFreqs, 'rb') as f:
		next(f)
		for line in f:
			countAdd += 1
			if countAdd % 10000 == 0:
				print statement
				print "Time taken:", round((time.time() - start) / 60, 1), "minutes"
				print "Added " + str(countAdd)
				session.close()
				session = driver.session()
			data = line.rstrip().split("|")
			name = data[0].replace("'","\\'")
			freqString = ''
			yCount=1
			for y in yRange:
				freqString+='m.freq_'+str(y)+"="+str(data[yCount])+","
				yCount+=1
			freqString = freqString[:-1]+";"
			if type == 'mesh':
				#mesh
				statement = "MERGE (m:Mesh {mesh_name:'" + name + "'}) ON MATCH SET "+freqString+""
			else:
				#semmed triples
				statement = "MERGE (m:SDB_triple {pid:" + name + "}) ON MATCH SET "+freqString+""
			#print statement
			#session.run(statement)



def main():
	get_mesh(yRange)
	get_semmed(yRange)
	#parse(home+'data/mesh_freqs')
	#parse(home+'data/semmed_freqs')
	#update_graph(home+'data/mesh_freqs','mesh')
	#update_graph(home+'data/semmed_freqs','semmed')

if __name__ == "__main__":
	main()
