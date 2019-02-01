from elasticsearch import Elasticsearch
from random import randint

import requests
import time
import re
import subprocess
import config
import gzip
import argparse


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

def es_query(filterData,index,predCounts):
	#print(filterData)
	t,resCount,res=run_query(filterData,index)
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
	return t,resCount,res,predCounts

def fet(localPub,localSem,globalPub,globalSem):
	print(localPub,localSem,globalPub,globalSem)
	return 1,1

def pub_sem(query):
	sem_trip_dic=read_sem_triples()

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
	chunkSize=5000
	updateSize=1000
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
				if counter % chunkSize == 0:
					print('Querying ES...')
					filterData={"terms":{"PMID":pmidList}}
					t,resCount,res,predCounts=es_query(filterData=filterData,index='semmeddb',predCounts=predCounts)
					totalRes+=resCount
					pmidList=[]
				if counter % updateSize == 0:
					pc = round((float(counter)/float(pCount))*100)
					print(str(pc)+' % : '+str(len(pmidList)))
		print('Querying ES...')
		filterData={"terms":{"PMID":pmidList}}
		t,resCount,res,predCounts=es_query(filterData=filterData,index='semmeddb',predCounts=predCounts)
		totalRes+=resCount

		pc = round((float(counter)/float(pCount))*100)
		print(str(pc)+' %')
		end = time.time()
		print "\tTime taken:", round((end - start) / 60, 3), "minutes"
		print('Total results:',totalRes)
		outFile=query.replace(' ','_')+'.gz'
		o = gzip.open('data/'+outFile,'w')
		#print(predCounts)

		#get global number of semmed triples
		globalSem=es.count('semmeddb')['count']

		for k in sorted(predCounts, key=lambda k: len(predCounts[k]), reverse=True):
			if len(predCounts[k])>1:
				#print k,len(predCounts[k])
				#do FET
				f1,f2=fet(totalRes,len(predCounts[k]),sem_trip_dic[k],globalSem)

				o.write(k+'\t'+str(len(predCounts[k]))+'\t'+sem_trip_dic[k]+'\n')
		o.close()
	else:
		print('Too many articles')

def read_sem_triples():
	print('getting background freqs...')
	sem_trip_dic={}
	start = time.time()
	with gzip.open('data/semmeddb_triple_freqs.txt.gz') as f:
		for line in f:
			s,f = line.rstrip().split('\t')
			sem_trip_dic[s]=f
	print(len(sem_trip_dic))
	end = time.time()
	print "\tTime taken:", round((end - start) / 60, 3), "minutes"
	return sem_trip_dic

def compare(q1,q2):
	q1Dic={}
	with gzip.open(q1) as f:
		for line in f:
			s,l,g = line.rstrip().split('\t')
			q1Dic[s]={'local':l,'global':g}
	q2Dic={}
	with gzip.open(q1) as f:
		for line in f:
			s,l,g = line.rstrip().split('\t')
			q1Dic[s]={'local':l,'global':g}

if __name__ == '__main__':

	parser = argparse.ArgumentParser(description='SemMedDB enrichment search')
	#parser.add_argument('integers', metavar='N', type=int, nargs='+',
	#                   help='an integer for the accumulator')
	parser.add_argument('-m,--method', dest='method', help='(get_data, compare)')
	parser.add_argument('-q,--query', dest='query', help='the pubmed query')

	args = parser.parse_args()
	print(args)
	if args.method == None:
		print("Please provide a method (get_data, compare)")
	else:
		if args.method == 'get_data':
			if args.query == None:
				print('Please provide a query')
			else:
				print('creating enriched article set')
				pub_sem(args.query)
		elif args.method == 'compare':
			if args.query_1 == None:
				print('Please provide a name')
			else:
				print('Comparing data...')
				#delete_index(args.index_name)
		else:
			print("Not a good method")

#pub_sem('pcsk9')
#pub_sem('oropharyngeal cancer')
#pub_sem('prostate cancer')
#pub_sem('breast cancer')
