from elasticsearch import Elasticsearch
from elasticsearch import helpers
from collections import deque

import config
import datetime
import time
import gzip
import requests

#could be over 17 million of these
batch_size=100000

url="http://localhost:9200/semmeddb/_search/"
headers = {'Content-Type': 'application/json'}
payload = { "aggs" : { "my_buckets" : { "composite": { "size":batch_size, "sources": [{"sub-pred-obj":{"terms" : { "field" : "SUB_PRED_OBJ"}}} ] }}}}

#initial query
#curl -X GET "localhost:9200/semmeddb/_search?pretty" -H 'Content-Type: application/json' -d '{ "aggs" : { "my_buckets" : { "composite": { "size":100, "sources": [{"sub-pred-obj":{"terms" : { "field" : "SUB_PRED_OBJ"}}} ] }}}} '

#after query
#curl -X GET "localhost:9200/semmeddb/_search?pretty" -H 'Content-Type: application/json' -d '{ "aggs" : { "my_buckets" : { "composite": { "size":100, "sources": [{"sub-pred-obj":{"terms" : { "field" : "SUB_PRED_OBJ"}}} ],"after":{"sub-pred-obj":"\"\"\"U\"\" lymphocyte\":LOCATION_OF:receptor"} }}}} '

r = requests.post(url, json=payload, headers=headers)
res=r.json()
masterDic={}
for r in res['aggregations']['my_buckets']['buckets']:
	val = r['key']['sub-pred-obj']
	count = r['doc_count']
	masterDic[val]=count
last_entry=res['aggregations']['my_buckets']['buckets'][-1]['key']['sub-pred-obj']
#print('last - ',last_entry)

pageCount=0
while True:
	now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	print(now,pageCount,len(masterDic))
	payload = { "aggs" : { "my_buckets" : { "composite": { "size":batch_size, "sources": [{"sub-pred-obj":{"terms" : { "field" : "SUB_PRED_OBJ"}}} ],"after":{"sub-pred-obj":last_entry}}}}}
	r = requests.post(url, json=payload, headers=headers)
	res=r.json()
	for r in res['aggregations']['my_buckets']['buckets']:
		val = r['key']['sub-pred-obj']
		count = r['doc_count']
		if val in masterDic:
			print val,'already exists'
			break
		masterDic[val]=count
	if len(res['aggregations']['my_buckets']['buckets'])>1:
		last_entry=res['aggregations']['my_buckets']['buckets'][-1]['key']['sub-pred-obj']
		#print('last - ',last_entry)
		pageCount+=1
	else:
		print 'Done'
		break

print len(masterDic)
print('Writing to file...')
o=gzip.open('data/semmeddb_triple_freqs.txt.gz','w')
for m in masterDic:
	o.write(m+'\t'+str(masterDic[m])+'\n')
