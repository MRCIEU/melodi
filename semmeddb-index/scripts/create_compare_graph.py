from elasticsearch import Elasticsearch
from random import randint
from collections import defaultdict
import scipy.stats as stats
import requests
import time
import re
import subprocess
import config
import gzip
import argparse
import os
import json

def neo4j_connect():
	from neo4j.v1 import GraphDatabase,basic_auth
	auth_token = basic_auth(config.neo4j_user, config.neo4j_password)
	driver = GraphDatabase.driver("bolt://" + config.neo4j_host + ":" + config.neo4j_port, auth=auth_token, encrypted=False)
	if driver:
		print('Connected')
	return driver

def escape_things(text):
	text = text.replace("'","\\'")
	return text

def load_nodes(session,nodes,type):
	with open(nodes) as json_file:
		data = json.load(json_file)
		for d in data:
			#print(d)
			for s in data[d]:
				sub=escape_things(data[d][s]['sub'])
				subType=data[d][s]['subType']
				pred=data[d][s]['pred']
				obj=escape_things(data[d][s]['obj'])
				objType=data[d][s]['objType']
				triple=sub+':'+pred+":"+obj
				pval,odds = data[d][s]['pval'],data[d][s]['odds']
				d_clean = escape_things(d)
				com="merge (d:DataSet{name:'"+d_clean+"'}) return d;"
				for res in session.run(com): continue;
				com="merge (sem:SemMedTriple{name:'"+triple+"',sub:'"+sub+"',pred:'"+pred+"',obj:'"+obj+"'}) return sem;"
				for res in session.run(com): continue;

				#add enrichment data
				com="match (d:DataSet{name:'"+d_clean+"'}) match (sem:SemMedTriple{name:'"+triple+"'}) merge (d)-[:ENRICHED{pval:"+pval+",odds:"+odds+"}]->(sem) return d,sem;"
				for res in session.run(com): continue;

				com="merge (sub:Concept{name:'"+sub+"',type:'"+subType+"'}) return sub;"
				for res in session.run(com): continue;
				com="merge (obj:Concept{name:'"+obj+"',type:'"+objType+"'}) return obj;"
				for res in session.run(com): continue;
				com="match (sub:Concept{name:'"+sub+"'}) match (obj:Concept{name:'"+obj+"'}) merge (sub)-[:"+pred+"]->(obj);"
				#print(com)
				for res in session.run(com): continue;
				if type == 'a':
					com="match (sem:SemMedTriple{name:'"+triple+"'}) match (sub:Concept{name:'"+sub+"'}) "\
					"merge (sem)-[:CONTAINS]->(sub);"
				else:
					com="match (sem:SemMedTriple{name:'"+triple+"'}) match (obj:Concept{name:'"+obj+"'}) "\
					"merge (sem)<-[:CONTAINS]-(obj);"
				for res in session.run(com): continue;

				# for res in session.run(com): continue;
				# #sep nodes for each part of semmmed
				# com="merge (sub:SemSub{name:'"+sub+"'}) return sub;"
				# for res in session.run(com): continue;
				# com="merge (pred:SemPred{name:'"+pred+"'}) return pred;"
				# for res in session.run(com): continue;
				# com="merge (obj:SemObj{name:'"+obj+"'}) return obj;"
				# for res in session.run(com): continue;
				# com="match (sub:SemSub{name:'"+sub+"'}) match (pred:SemPred{name:'"+pred+"'}) match (obj:SemObj{name:'"+obj+"'}) "\
				#     "merge (sub)-[:SUB_PRED]->(pred) merge (pred)-[:PRED_OBJ]->(obj);"
				# for res in session.run(com): continue;
				# if type == 'a':
				# 	com="match (sem:SemMedTriple{name:'"+triple+"'}) match (sub:SemSub{name:'"+sub+"'}) "\
				# 		"merge (sem)-[:CONTAINS]->(sub);"
				# else:
				# 	com="match (sem:SemMedTriple{name:'"+triple+"'}) match (obj:SemObj{name:'"+obj+"'}) "\
				# 		"merge (sem)<-[:CONTAINS]-(obj);"
				# for res in session.run(com): continue;

def create_graph(a_nodes,b_nodes,rels):
	driver=neo4j_connect()
	session = driver.session()

	#add some indexes
	com="CREATE index on :DataSet(name);"
	session.run(com)

	com="CREATE index on :SemMedTriple(name)"
	session.run(com)
	com="CREATE index on :SemMedTriple(sub)"
	session.run(com)
	com="CREATE index on :SemMedTriple(pred)"
	session.run(com)
	com="CREATE index on :SemMedTriple(obj)"
	session.run(com)

	com="CREATE index on :Concept(name);"
	session.run(com)
	#com="CREATE index on :SemSub(name);"
	#session.run(com)
	#com="CREATE index on :SemPred(name);"
	#session.run(com)
	#com="CREATE index on :SemObj(name);"
	#session.run(com)

	print('Reading',a_nodes)
	load_nodes(session,a_nodes,'a')
	print('Reading',b_nodes)
	load_nodes(session,b_nodes,'b')

	print('Adding rels...')
	tx = session.begin_transaction()
	#statement = "MERGE (n:Pubmed {pmid:{pmid}}) ON MATCH SET n.title={title},n.jt={jt} on CREATE SET n.dcom={dcom},n.issn={issn},n.title={title},n.jt={jt}"
	#statement = "match (d1:DataSet{name:{dataName1}})-[:ENRICHED]->(sem1:SemMedTriple{name:{semTriple1}})-[:CONTAINS]-(sub1:SemSub)-[:SUB_PRED]-(pred1:SemPred)-[:PRED_OBJ]-(obj1:SemObj{name:{overlapName}}) "\
	#	"match (d2:DataSet{name:{dataName2}})-[:ENRICHED]->(sem2:SemMedTriple{name:{semTriple2}})<-[:CONTAINS]-(obj2:SemObj)<-[:PRED_OBJ]-(pred2:SemPred)<-[:SUB_PRED]-(sub2:SemSub{name:{overlapName}}) "\
	#	"merge (obj1)-[:OVERLAPS{d1:{dataName1},d2:{dataName2}}]-(sub2) return sem1,sem2,sub2,obj1;"
	statement = "match (d1:DataSet{name:{dataName1}})-[:ENRICHED]->(sem1:SemMedTriple{name:{semTriple1}})-[:CONTAINS]-(sub1:Concept{name:{aSub}})-[rel1:{aPred}]->(obj1:Concept{name:{overlapName}}) "\
		"match (d2:DataSet{name:{dataName2}})-[:ENRICHED]->(sem2:SemMedTriple{name:{semTriple2}})<-[:CONTAINS]-(obj2:Concept{name:{bObj}})<-[rel2:{bPred}]-(sub2:SemSub{name:{overlapName}}) "\
		"merge (obj1)-[:OVERLAPS{d1:{dataName1},d2:{dataName2}}]-(sub2) return sem1,sem2,sub2,obj1;"
	counter=0
	with open(rels) as f:
		for line in f:
			counter+=1
			num,semTriple1,aSub,aPred,aObj,semTriple2,bSub,bPred,bObj,overlapName,dataName1,dataName2 = line.rstrip().split('\t')
			#print(num,s1,aSub,aPred,aObj,s2,bSub,bPred,bObj,overlap,d1,d2)
			#print(statement,{'dataName1':d1,'dataName2':d2,'semTriple1':escape_things(s1),'aSub':aSub,'aPred':aPred,'aObj':aObj,'semTriple2':escape_things(s2),'bSub':bSub,'bPred':bPred,'bObj':bObj,'overlapName':overlap})
			#tx.run(statement,{'dataName1':d1,'dataName2':d2,'semTriple1':escape_things(s1),'aSub':aSub,'aPred':aPred,'aObj':aObj,'semTriple2':escape_things(s2),'bSub':bSub,'bPred':bPred,'bObj':bObj,'overlapName':overlap})
			statement = "match (d1:DataSet{name:'"+escape_things(dataName1)+"'})-[:ENRICHED]->(sem1:SemMedTriple{name:'"+escape_things(semTriple1)+"'})-[:CONTAINS]-(sub1:Concept{name:'"+escape_things(aSub)+"'})-[rel1:"+aPred+"]->(obj1:Concept{name:'"+escape_things(overlapName)+"'}) "\
				"match (d2:DataSet{name:'"+escape_things(dataName2)+"'})-[:ENRICHED]->(sem2:SemMedTriple{name:'"+escape_things(semTriple2)+"'})<-[:CONTAINS]-(obj2:Concept{name:'"+escape_things(bObj)+"'})<-[rel2:"+bPred+"]-(sub2:Concept{name:'"+escape_things(overlapName)+"'}) "\
				"merge (obj1)-[:OVERLAPS{d1:'"+escape_things(dataName1)+"',d2:'"+escape_things(dataName2)+"'}]-(sub2) return sem1,sem2,sub2,obj1;"
			#print(statement)
			tx.run(statement)
			if counter % 1000 == 0:
				print(counter)
				tx.commit()
				tx = session.begin_transaction()
			#print(counter)
			#com="match (d1:DataSet{name:'"+escape_things(d1)+"'})-[:ENRICHED]->(sem1:SemMedTriple{name:'"+escape_things(s1)+"'})-[:CONTAINS]-(sub1:SemSub)-[:SUB_PRED]-(pred1:SemPred)-[:PRED_OBJ]-(obj1:SemObj{name:'"+overlap+"'}) "\
			#    "match (d2:DataSet{name:'"+escape_things(d2)+"'})-[:ENRICHED]->(sem2:SemMedTriple{name:'"+escape_things(s2)+"'})<-[:CONTAINS]-(obj2:SemObj)<-[:PRED_OBJ]-(pred2:SemPred)<-[:SUB_PRED]-(sub2:SemSub{name:'"+overlap+"'}) "\
			#    "merge (obj1)-[:OVERLAPS{d1:'"+d1+"',d2:'"+d2+"'}]-(sub2) return sem1,sem2,sub2,obj1;"

			#com="match (d1:DataSet{name:'"+escape_things(d1)+"'})-[:ENRICHED]->(sem1:SemMedTriple{name:'"+escape_things(s1)+"'}) match (d2:DataSet{name:'"+escape_things(d2)+"'})-[:ENRICHED]->(sem2:SemMedTriple{name:'"+escape_things(s2)+"'}) "\
			#     "merge (sem1)-[:OVERLAPS]-(sem2) return sem1,sem2;"
			#print(com)
			#for res in session.run(com): continue;
	tx.run(statement)
	tx.commit()
	print(counter,'relationships added')


create_graph('data/compare/a_nodes.json','data/compare/b_nodes.json','data/compare/rels.tsv')
