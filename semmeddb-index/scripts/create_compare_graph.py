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

def create_graph(nodes,rels):
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

	com="CREATE index on :SemSub(name);"
	session.run(com)
	com="CREATE index on :SemPred(name);"
	session.run(com)
	com="CREATE index on :SemObj(name);"
	session.run(com)

	print('Reading',nodes)
	with open(nodes) as json_file:
		data = json.load(json_file)
		for d in data:
			#print(d)
			for s in data[d]:
				com="merge (d:DataSet{name:'"+d+"'}) return d;"
				for res in session.run(com): continue;
				sub=escape_things(data[d][s]['sub'])
				pred=data[d][s]['pred']
				obj=escape_things(data[d][s]['obj'])
				triple=sub+':'+pred+":"+obj
				com="merge (sem:SemMedTriple{name:'"+triple+"',sub:'"+sub+"',pred:'"+pred+"',obj:'"+obj+"'}) return sem;"
				for res in session.run(com): continue;

				#add enrichment data
				pval,odds = data[d][s]['pval'],data[d][s]['odds']
				com="match (d:DataSet{name:'"+d+"'}) match (sem:SemMedTriple{name:'"+triple+"'}) merge (d)-[:ENRICHED{pval:"+pval+",odds:"+odds+"}]->(sem) return d,sem;"
				for res in session.run(com): continue;

				#sep nodes for each part of semmmed
				com="merge (sub:SemSub{name:'"+escape_things(data[d][s]['sub'])+"'}) return sub;"
				for res in session.run(com): continue;
				com="merge (pred:SemPred{name:'"+escape_things(data[d][s]['pred'])+"'}) return pred;"
				for res in session.run(com): continue;
				com="merge (obj:SemObj{name:'"+escape_things(data[d][s]['obj'])+"'}) return obj;"
				for res in session.run(com): continue;
				com="match (sem:SemMedTriple{name:'"+triple+"'}) match (sub:SemSub{name:'"+escape_things(data[d][s]['sub'])+"'}) "\
				    "match (pred:SemPred{name:'"+data[d][s]['pred']+"'}) match (obj:SemObj{name:'"+escape_things(data[d][s]['obj'])+"'}) "\
					"merge (sem)-[:CONTAINS]->(sub)-[:SUB_PRED]->(pred)-[:PRED_OBJ]->(obj) return pred,obj;"
				for res in session.run(com): continue;

	print('Adding rels...')
	with open(rels) as f:
		for line in f:
			num,s1,s2,d1,d2 = line.rstrip().split('\t')
			com="match (d1:DataSet{name:'"+escape_things(d1)+"'})-[:ENRICHED]->(sem1:SemMedTriple{name:'"+escape_things(s1)+"'})-[:CONTAINS]-(:SemSub)-[:SUB_PRED]-(:SemPred)-[:PRED_OBJ]-(obj:SemObj) "\
			    "match (d2:DataSet{name:'"+escape_things(d2)+"'})-[:ENRICHED]->(sem2:SemMedTriple{name:'"+escape_things(s2)+"'})-[:CONTAINS]-(sub:SemSub) "\
			    "merge (obj)-[:OVERLAPS{d1:'"+d1+"',d2:'"+d2+"'}]-(sub) return sem1,sem2,sub,obj;"
			#com="match (d1:DataSet{name:'"+escape_things(d1)+"'})-[:ENRICHED]->(sem1:SemMedTriple{name:'"+escape_things(s1)+"'}) match (d2:DataSet{name:'"+escape_things(d2)+"'})-[:ENRICHED]->(sem2:SemMedTriple{name:'"+escape_things(s2)+"'}) "\
			#     "merge (sem1)-[:OVERLAPS]-(sem2) return sem1,sem2;"
			print(com)
			for res in session.run(com): continue;


create_graph('data/compare/nodes.json','data/compare/rels.tsv')
