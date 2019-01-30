from elasticsearch import Elasticsearch
from random import randint

import requests
import time
import re
import subprocess

def run_query(filterData,index,size=1000):
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
	print "Time taken:",t, "seconds"
	print res['hits']['total']
	return t,res['hits']['total']


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
	if 0<pCount<maxA:
		print "\n### Parsing ids ###"
		start = time.time()
		f = open('/tmp/'+ran+'.txt', 'r')
		for line in f:
			l = re.search(r'.*?<Id>(.*?)</Id>', line)
			if l:
				pmid = l.group(1)
				filterData={"terms":{"pmid":[pmid]}}
				t,time=run_query(filterData)
				print t,time
				counter+=1
				if counter % 1000 == 0:
					pc = round((float(counter)/float(pCount))*100)
					print(pc)
		pc = round((float(counter)/float(pCount))*100)
		print(pc)
		end = time.time()
		print "\tTime taken:", round((end - start) / 60, 3), "minutes"
		return counter
	else:
		SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='Too many articles',job_progress=0)

pub_sem('pcsk9')
