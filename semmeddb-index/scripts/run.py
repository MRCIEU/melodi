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

#globals

timeout=300

es = Elasticsearch(
	[{'host': config.elastic_host,'port': config.elastic_port}],
)

#total number of publications
#curl -XGET 'localhost:9200/semmeddb/_search?pretty' -H "Content-Type: application/json" -d '{"size":0, "aggs" : {"type_count":{"cardinality" :{ "field" : "PMID" }}}}'
globalPub=17734131

#time python scripts/run.py -m compare -a 'CR1,CCDC6,KAT8' -b 'Alzheimers_disease'

def run_query(filterData,index,size=100000):
	#print(index)
	start=time.time()
	res=es.search(
		request_timeout=timeout,
		index=index,
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

def get_term_stats(index='semmeddb_triple_freqs',query=[]):
	filterData={"terms":{"SUB_PRED_OBJ":query}}
	start=time.time()
	res=es.search(
		request_timeout=timeout,
		index=index,
		body={
			"size":1000000,
			"query": {
				"bool" : {
					"filter" : filterData
				}
			}
		}
	)
	end = time.time()
	t=round((end - start), 4)
	#print "Time taken:",t, "seconds"
	return res['hits']['hits']

def create_es_filter(pmidList):
	#https://github.com/MRCIEU/melodi/blob/master/data/SRDEF.txt
	#typeFilterList = [
	#	"aapp","amas","anab","bacs","biof","bpoc","celf","chem","comd","dsyn","emod","enzy","genf","gngm","hcpp","hops","horm","imft","inch",
	#	"moft","mosq","neop","nnon","nsba","orch","orgf","ortf","patf","rcpt","sbst","socb","tisu","topp","virs","vita"]

	#typeFilterList = [
	#	"aapp","amas","bacs","celf","enzy","gngm","horm","orch"]
	typeFilterList = [
		"aapp","enzy","gngm"]
	filterOptions = [
			{"terms":{"PMID":pmidList}},
			{"terms":{"OBJECT_SEMTYPE":typeFilterList}},
			{"terms":{"SUBJECT_SEMTYPE":typeFilterList}},
			]
	return filterOptions

def es_query(filterData,index,predCounts,resDic):
	#print(filterData)
	t,resCount,res=run_query(filterData,index)
	print(resCount)
	if resCount>0:
		#print(filterData)
		#print t,resCount
		for r in res:
			PMID=r['_source']['PMID']
			#PREDICATION_ID=r['_source']['PREDICATION_ID']
			PREDICATE=r['_source']['PREDICATE']
			OBJECT_NAME=r['_source']['OBJECT_NAME']
			OBJECT_TYPE=r['_source']['OBJECT_SEMTYPE']
			SUBJECT_NAME=r['_source']['SUBJECT_NAME']
			SUBJECT_TYPE=r['_source']['SUBJECT_SEMTYPE']
			PREDICATION_ID=SUBJECT_NAME+':'+PREDICATE+':'+OBJECT_NAME
			resDic[PREDICATION_ID]={'sub':SUBJECT_NAME,'subType':SUBJECT_TYPE,'pred':PREDICATE,'obj':OBJECT_NAME,'objType':OBJECT_TYPE}
			#print PMID,PREDICATION_ID
			if PREDICATION_ID in predCounts:
				predCounts[PREDICATION_ID]+=1
			else:
				predCounts[PREDICATION_ID]=1
	return t,resCount,resDic,predCounts

def fet(localSem,localPub,globalSem,globalPub):
	#print(localSem,localPub,globalSem,globalPub)
	oddsratio, pvalue = stats.fisher_exact([[localSem, localPub], [globalSem, globalPub]])
	#print(oddsratio, pvalue)
	return oddsratio,pvalue

def pub_sem(query,sem_trip_dic):
	start=time.time()
	print("\n### Getting ids for "+query+" ###")
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
	print("Time taken:",round((end-start)/60,3),"minutes")

	#count the number of pmids
	cmd = "grep -c '<Id>' "+ranFile
	pCount=0
	#print cmd
	#check for empty searches
	try:
		pCount = int(subprocess.check_output(cmd, shell=True))
	except:
		print("No results")

	print("Total pmids: "+str(pCount))
	maxA=1000000
	counter=0
	pmidList=[]
	totalRes=0
	predCounts={}
	resDic={}
	chunkSize=10000
	updateSize=10000
	filterOptions = create_es_filter(pmidList)
	if 0<pCount<maxA:
		print("\n### Parsing ids ###")
		start = time.time()
		f = open('/tmp/'+ran+'.txt', 'r')
		for line in f:
			l = re.search(r'.*?<Id>(.*?)</Id>', line)
			if l:
				pmid = l.group(1)
				pmidList.append(pmid)
				counter+=1
				if counter % updateSize == 0:
					pc = round((float(counter)/float(pCount))*100)
					print(str(pc)+' % : '+str(counter)+' '+str(len(predCounts)))
				if counter % chunkSize == 0:
					#print('Querying ES...')
					t,resCount,resDic,predCounts=es_query(filterData=filterOptions,index='semmeddb',predCounts=predCounts,resDic=resDic)
					totalRes+=resCount
					pmidList=[]
		#print(filterOptions)
		t,resCount,resDic,predCounts=es_query(filterData=filterOptions,index='semmeddb',predCounts=predCounts,resDic=resDic)
		totalRes+=resCount

		pc = round((float(counter)/float(pCount))*100)
		print(str(pc)+' % : '+str(counter)+' '+str(len(predCounts)))
		end = time.time()
		print("\tTime taken:", round((end - start) / 60, 3), "minutes")
		print('Total results:',totalRes)
		outFile=query.replace(' ','_')+'.gz'
		o = gzip.open('data/'+outFile,'w')
		#print(predCounts)

		#get global number of publications
		globalSem=es.count('semmeddb')['count']
		#globalSem=25000000

		#get triple freqs
		tripleFreqs = {}
		print('Geting freqs...',len(predCounts))
		#print(predCounts.keys())
		freq_res = get_term_stats(query=list(predCounts.keys()))
		#print(freq_res)
		for i in freq_res:
			tripleFreqs[i['_source']['SUB_PRED_OBJ']]=i['_source']['frequency']

		print('Doing enrichment...')
		start = time.time()
		counter=0
		for k in sorted(predCounts, key=lambda k: predCounts[k], reverse=True):
			counter+=1
			if counter % chunkSize == 0:
				pc = round((float(counter)/float(len(predCounts)))*100)
				print(str(pc)+' % : '+str(counter))
			if predCounts[k]>1:
				if freq_res:
					odds,pval=fet(predCounts[k],totalRes,tripleFreqs[k],globalSem)
					t = k+'\t'+resDic[k]['sub']+'\t'+resDic[k]['subType']+'\t'+resDic[k]['pred']+'\t'+resDic[k]['obj']+'\t'+resDic[k]['objType']+'\t'+str(predCounts[k])+'\t'+str(totalRes)+'\t'+str(tripleFreqs[k])+'\t'+str(globalPub)+'\t'+str(odds)+'\t'+str(pval)+'\n'
					o.write(t.encode('utf-8'))
				else:
					continue
					#print(k,'has no freq')
		o.close()
		if len(predCounts)>1:
			pc = round((float(counter)/float(len(predCounts)))*100)
		else:
			pc=100
		print(str(pc)+' % : '+str(counter))
		end = time.time()
		print("\tTime taken:", round((end - start) / 60, 3), "minutes")
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
	print("\tTime taken:", round((end - start) / 60, 3), "minutes")
	return sem_trip_dic

def compare(aList,bList):
	pValCut=1e-5
	predIgnore = ['PART_OF','ISA','LOCATION_OF','PROCESS_OF','ADMINISTERED_TO','METHOD_OF','USES','COEXISTS_WITH','ASSOCIATED_WITH','compared_with']

	aDic=defaultdict(dict)
	for a in aList.split(','):
		print(a)
		with gzip.open(os.path.join('data',a+'.gz'),'rb') as f:
			for line in f:
				s,sub,subType,pred,obj,objType,f1,f2,f3,f4,o,p = line.rstrip().split('\t')
				if float(p)<pValCut:
					if pred not in predIgnore:
						aDic[a][s]={'sub':sub,'subType':subType,'obj':obj,'objType':objType,'pred':pred,'localCounts':f1,'localTotal':f2,'globalCounts':f3,'globalTotal':f4,'odds':o,'pval':p}
	bDic=defaultdict(dict)
	for b in bList.split(','):
		print(b)
		with gzip.open(os.path.join('data',b+'.gz')) as f:
			for line in f:
				s,sub,subType,pred,obj,objType,f1,f2,f3,f4,o,p = line.rstrip().split('\t')
				if float(p)<pValCut:
					#ignore less useful predicates
					if pred not in predIgnore:
						bDic[b][s]={'sub':sub,'subType':subType,'obj':obj,'objType':objType,'pred':pred,'localCounts':f1,'localTotal':f2,'globalCounts':f3,'globalTotal':f4,'odds':o,'pval':p}

	print(len(aDic))
	print(len(bDic))

	ignoreTerms=['Patients','Disease']

	#compare two sets of data
	aComDic=defaultdict(dict)
	bComDic=defaultdict(dict)
	joinDic={}
	predDic={}
	joinCount=0
	for a in aDic:
		print(a)
		counter=0
		for s1 in aDic[a]:
			counter+=1
			pc = round((float(counter)/float(len(aDic[a])))*100,1)
			#print(counter,pc,pc%10)
			if pc % 10 == 0:
				print(pc,'%')
			aSub,aPred,aObj = aDic[a][s1]['sub'],aDic[a][s1]['pred'],aDic[a][s1]['obj']
			for b in bDic:
				#print(b)
				for s2 in bDic[b]:
					#print(s1,s2)
					bSub,bPred,bObj = bDic[b][s2]['sub'],bDic[b][s2]['pred'],bDic[b][s2]['obj']
					#print(aObj,bSub)
					#testing removal of words
					if bSub.startswith('Alzheimer'):
						continue
					if bSub in ignoreTerms:
						continue
					if aObj == bSub:
						if aPred in predDic:
							predDic[aPred]+=1
						else:
							predDic[aPred]=1
						if bPred in predDic:
							predDic[bPred]+=1
						else:
							predDic[bPred]=1
						#print a,s1,aDic[a][s1],b,s2,bDic[b][s2]
						aComDic[a][s1]=aDic[a][s1]
						bComDic[b][s2]=bDic[b][s2]
						joinCount+=1
						joinDic[joinCount]={'s1':s1,'aSub':aSub,'aPred':aPred,'aObj':aObj,'s2':s2,'bSub':bSub,'bPred':bPred,'bObj':bObj,'overlap':aObj,'d1':a,'d2':b}
	#get some summaries
	print(predDic)
	for c in aComDic:
		print(c,len(aComDic[c]))

	with open('data/compare/a_nodes.json','w') as outfile:
		#outfile={'source':a:'sem':s1:aDic[a][s1]}
		json.dump(aComDic,outfile)

	with open('data/compare/b_nodes.json','w') as outfile:
		#outfile={'source':a:'sem':s1:aDic[a][s1]}
		json.dump(bComDic,outfile)

	o = open('data/compare/rels.tsv','w')
	for i in joinDic:
	#outfile={'source':a:'sem':s1:aDic[a][s1]}
		o.write(str(i)+'\t'+joinDic[i]['s1']+'\t'+joinDic[i]['aSub']+'\t'+joinDic[i]['aPred']+'\t'+joinDic[i]['aObj']+'\t'+joinDic[i]['s2']+'\t'+joinDic[i]['bSub']+'\t'+joinDic[i]['bPred']+'\t'+joinDic[i]['bObj']+'\t'+joinDic[i]['overlap']+'\t'+joinDic[i]['d1']+'\t'+joinDic[i]['d2']+'\n')
	o.close()

if __name__ == '__main__':

	parser = argparse.ArgumentParser(description='SemMedDB enrichment search')
	#parser.add_argument('integers', metavar='N', type=int, nargs='+',
	#                   help='an integer for the accumulator')
	parser.add_argument('-m,--method', dest='method', help='(get_data, compare)')
	parser.add_argument('-q,--query', dest='query', help='the pubmed query')
	parser.add_argument('-a,--query_a', dest='query_a', help='list of enriched data sets')
	parser.add_argument('-b,--query_b', dest='query_b', help='list of enriched data sets')

	args = parser.parse_args()
	print(args)
	if args.method == None:
		print("Please provide a method (-m): [get_data, compare]")
	else:
		if args.method == 'get_data':
			if args.query == None:
				print('Please provide a query (-q) [e.g. pcsk9]')
			else:
				#sem_trip_dic=read_sem_triples()
				sem_trip_dic={}
				print('creating enriched article set')
				queries=args.query.rstrip().split(',')
				for q in queries:
					pub_sem(q,sem_trip_dic)
		elif args.method == 'compare':
			if args.query_a == None or args.query_b == None:
				print('Please provide two lists of data sets to compare (-a and -b)')
			else:
				print('Comparing data...')
				compare(args.query_a,args.query_b)
				#delete_index(args.index_name)
		else:
			print("Not a good method")

#pub_sem('pcsk9')
#pub_sem('oropharyngeal cancer')
#pub_sem('prostate cancer')
#pub_sem('breast cancer')
#get_term_stats('semmeddb_triple_freqs',filterData={"terms":{"SUB_PRED_OBJ":['Encounter due to counseling:PROCESS_OF:Family']}})
