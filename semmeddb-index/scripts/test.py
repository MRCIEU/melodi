from elasticsearch import Elasticsearch
from random import randint

import requests
import time
import re
import subprocess
import config

timeout=300

es = Elasticsearch(
	[{'host': config.elastic_host,'port': config.elastic_port}],
)

def run_query(filterData,index,size=100000):
	#print(index)
	start=time.time()
	res=es.search(
		request_timeout=timeout,
		index=index,
		#index="ukb-b",
		#index="pqtl-a",
		#index="mrb-original",
		#index="mrbase-opt-disk",
		#doc_type="assoc",
		body={
			"size":size,
			#{}"profile": True,
			"query": {
				"bool" : {
					"filter" : filterData
				}
			}

		})
	end = time.time()
	t=round((end - start), 4)
	#print "Time taken:",t, "seconds"
	#print res['hits']['total']
	return t,res['hits']['total'],res['hits']['hits']


def pub_sem(query):
	start=time.time()
	print "\n### Getting ids for "+query+" ###"
	url="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
	params = {'db': 'pubmed', 'term': query,'retmax':'1000000000','rettype':'uilist'}

	#r = requests.post(url)

	# GET with params in URL
	r = requests.get(url, params=params)

	#create random file name
	n = 10
	ran=''.join(["%s" % randint(0, 9) for num in range(0, n)])

	ranFile = '/tmp/'+ran+'.txt'
	out = open(ranFile, 'w')
	out.write(r.text)
	out.close()
	r.status_code
	end=time.time()
	print "Time taken:",round((end-start)/60,3),"minutes"

	#count the number of pmids
	cmd = "grep -c '<Id>' "+ranFile
	pCount=0
	#print cmd
	#check for empty searches
	try:
		pCount = int(subprocess.check_output(cmd, shell=True))
	except:
		print "No results"

	print "Total pmids: "+str(pCount)
	maxA=1000000
	counter=0
	pmidList=[]
	totalRes=0
	predCounts={}
	if 0<pCount<maxA:
		print "\n### Parsing ids ###"
		start = time.time()
		f = open('/tmp/'+ran+'.txt', 'r')
		for line in f:
			l = re.search(r'.*?<Id>(.*?)</Id>', line)
			if l:
				pmid = l.group(1)
				pmidList.append(pmid)
				counter+=1
				if counter % 1000 == 0:
					filterData={"terms":{"PMID":pmidList}}
					#print(filterData)
					t,resCount,res=run_query(filterData,'semmeddb')
					if res>0:
						#print(filterData)
						print t,resCount
						for r in res:
							PMID=r['_source']['PMID']
							#PREDICATION_ID=r['_source']['PREDICATION_ID']
							PREDICATE=r['_source']['PREDICATE']
							OBJECT_NAME=r['_source']['OBJECT_NAME']
							SUBJECT_NAME=r['_source']['SUBJECT_NAME']
							PREDICATION_ID=SUBJECT_NAME+':'+PREDICATE+':'+OBJECT_NAME
							#print PMID,PREDICATION_ID
							if PREDICATION_ID in predCounts:
								if PMID not in predCounts[PREDICATION_ID]:
									predCounts[PREDICATION_ID].append(PMID)
									predCounts[PREDICATION_ID].append(PMID)
							else:
								predCounts[PREDICATION_ID]=[PMID]
						totalRes+=resCount
					pc = round((float(counter)/float(pCount))*100)
					print(pc,'%')
					pmidList=[]
		pc = round((float(counter)/float(pCount))*100)
		print(pc,'%')
		end = time.time()
		print "\tTime taken:", round((end - start) / 60, 3), "minutes"
		print('Total results:',totalRes)
		#print(predCounts)
		for k in sorted(predCounts, key=lambda k: len(predCounts[k]), reverse=True):
			if len(predCounts[k])>1:
				print k,len(predCounts[k])
	else:
		print('Too many articles')

#pub_sem('pcsk9')
pub_sem('oropharyngeal cancer')
#pub_sem('prostate cancer')
