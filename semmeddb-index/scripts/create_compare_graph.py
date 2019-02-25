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

def create_graph(compareData):
	driver=neo4j_connect()
	session = driver.session()

	#add some indexes
	com="CREATE index on :DataSet(name);"
	session.run(com)

	com="CREATE index on :SemMedTriple(name)"
	com="CREATE index on :SemMedTriple(sub)"
	com="CREATE index on :SemMedTriple(pred)"
	com="CREATE index on :SemMedTriple(obj)"

	com="CREATE index on :SemSub(name);"
	session.run(com)
	com="CREATE index on :SemPred(name);"
	session.run(com)
	com="CREATE index on :SemObj(name);"
	session.run(com)

	print('Reading',compareData)
	with open(compareData) as json_file:
		data = json.load(json_file)
		for d in data:
			print(d)
			for s in data[d]:
				com="merge (d:DataSet{name:'"+d+"'}) return d;"
				session.run(com)
				sub=escape_things(data[d][s]['sub'])
				pred=data[d][s]['pred']
				obj=escape_things(data[d][s]['obj'])
				triple=sub+' : '+pred+" : "+obj
				com="merge (sem:SemMedTriple{name:'"+triple+"',sub:'"+sub+"',pred:'"+pred+"',obj:'"+obj+"'}) return sem;"
				session.run(com)

				#add enrichment data
				pval,odds = data[d][s]['pval'],data[d][s]['odds']
				com="match (d:DataSet{name:'"+d+"'}) match (sem:SemMedTriple{name:'"+triple+"'}) merge (d)-[:ENRICHED{pval:"+pval+",odds:"+odds+"}]->(sem) return d,sem;"
				session.run(com)

				#sep nodes for each part of semmmed
				com="merge (sub:SemSub{name:'"+escape_things(data[d][s]['sub'])+"'}) return sub;"
				session.run(com)
				com="merge (pred:SemPred{name:'"+escape_things(data[d][s]['pred'])+"'}) return pred;"
				session.run(com)
				com="merge (obj:SemObj{name:'"+escape_things(data[d][s]['obj'])+"'}) return obj;"
				session.run(com)
				com="match (sem:SemMedTriple{name:'"+triple+"'}) match (sub:SemSub{name:'"+escape_things(data[d][s]['sub'])+"'}) "\
				    "match (pred:SemPred{name:'"+data[d][s]['pred']+"'}) match (obj:SemObj{name:'"+escape_things(data[d][s]['obj'])+"'}) "\
					"merge (sem)-[:CONTAINS]->(sub) with sub,pred,obj merge (sub)-[:SUB_PRED]->(pred) with pred,obj merge (pred)-[:PRED_OBJ]->(obj) return pred,obj;"
				#session.run(com)


	#queries
	#match (d1:DataSet)-[e1:ENRICHED]-(s1:SemMedTriple)-[:CONTAINS]-(sub1:SemSub)-[:SUB_PRED]-(pred1:SemPred)-[:PRED_OBJ]-(obj1:SemObj) where d1.name =~ 'Alzheimer’s_disease' with d1,s1,e1,sub1,obj1,pred1 match (obj2:SemObj)-[:PRED_OBJ]-(pred2:SemPred)-[:SUB_PRED]-(sub2:SemSub)-[:CONTAINS]-(s2:SemMedTriple)-[e2:ENRICHED]-(d2) where d1<>d2 and obj1.name = sub2.name and e1.pval < 1e-20 and e2.pval < 1e-20 return sub1,sub2,obj1,obj2,pred1,pred2,d1,d2,e1,e2;


create_graph('data/compare/exposures.json')
create_graph('data/compare/outcomes.json')
