from __future__ import absolute_import
from celery import shared_task, task
from celery.task import periodic_task
from celery.schedules import crontab
from django.core.mail import send_mail
import datetime
from datetime import timedelta
#from py2neo import Graph, Path, Node, Relationship, authenticate

import sys,gzip,time,os,subprocess,re,json,random
import statsmodels.sandbox.stats.multicomp as sm
import logging
import zipfile
import requests
import random
import shutil
import config

from random import randint
from scipy import stats
from browser.models import SearchSet,SearchSetAnalysis,Compare,Overlap
from celery.utils.log import get_task_logger
#from py2neo.packages.httpstream import http
#http.socket_timeout = 9999
from collections import defaultdict
from retrying import retry
from django.conf import settings

logger = logging.getLogger(__name__)

from neo4j.v1 import GraphDatabase,basic_auth
auth_token = basic_auth(config.user, config.password)
driver = GraphDatabase.driver("bolt://"+config.server+":"+config.port,auth=auth_token)

#tmpDir="/vagrant/tmp/"
tmpDir=settings.MEDIA_ROOT

#set semmed freq cutoff
semFreq = 150000
#semFreq = 150000000

#max number of articles
maxA=1000000

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

#fileCompression function
def compressCheck(file_name):
	if file_name.endswith('.gzip') or file_name.endswith('.gz'):
		infile = gzip.open(file_name)
	elif file_name.endswith('.zip'):
		unzipped = zipfile.ZipFile(file_name,'r')
		for name in unzipped.namelist():
			infile = unzipped.open(name)
	else:
		infile = open(file_name, 'r')
	return infile

@task(name='tasks.test_scheduler')
def test():
	t = time.asctime( time.localtime(time.time()) )
	print "Running test schedular",t
	#logger.debug("Running test schedular: "+str(t))

def pmid_get(d,td):
	print "\n### Getting pubmed ids for "+td+" ###"
	start = time.time()

	url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
	payload = {'db': 'pubmed',
               'term': '"'+td+'"[PDAT] : "3000"[PDAT]',
               'retmax': '1000000000'}
				#'retmax': '10'}

	# get the data
	r = requests.get(url, params=payload)

	out = open(d + 'pmids_raw.txt', 'w')
	out.write(r.text)
	end = time.time()
	print "\tTime taken:", round((end - start) / 60, 3), "minutes"


def parse_pmids(d):
	print "\n### Parsing ids ###"
	counter = 0
	start = time.time()
	f = open(d + 'pmids_raw.txt', 'r')
	out = open(d + 'pmids_trimmed.txt', 'w')
	for line in f:
		counter += 1
		l = re.search(r'.*?<Id>(.*?)</Id>', line)
		if l:
			out.write(l.group(1) + "\n")
	end = time.time()
	print "\tTime taken:", round((end - start) / 60, 3), "minutes"
	return counter


def split_pmids(counter, split_num, d):
	print "\n### Splitting ids into separate files ###"
	start = time.time()

	n = counter / split_num
	# max value for retmax is 10000
	if (n > 10000):
		print "\tMore files needed - max number of ids per search is 10,000!"
		n = 10000
		split_num = round(counter / n)
	print "\tSplitting " + str(counter) + " ids into " + str(split_num) + " new files..."
	com = 'split -a 10 -l ' + str(n) + ' ' + d + 'pmids_trimmed.txt ' + d + 'pmid_split.'
	# print com
	os.system(com)
	# need to replace new lines with commas
	end = time.time()
	print "\tEach file has around " + str(n) + " pubmed ids."
	print "\tTime taken:", round((end - start) / 60, 3), "minutes"
	return (n)


def medline_get(f):
	print "\n### Getting medline files for file - ", f + " ###"
	start = time.time()
	ids = open(f).read().replace('\n', ',')
	# print ids

	url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'
	payload = {'db': 'pubmed', 'id': ids, 'retmax': '10000', 'retmode': 'text', 'rettype': 'medline'}

	# POST with data
	r = requests.post(url, data=payload)

	out = open(f + '.medline', 'w')
	out.write(r.text)

	end = time.time()
	print "\tTime taken:", round((end - start) / 60, 3), "minutes"

def load_mesh(file_name):
	print "Loading new mesh data: "+file_name
	session = driver.session()
	tx = session.begin_transaction()
	statement1 = "MATCH (a:Pubmed),(b:Mesh) where a.pmid = {pmid} and and a.da = {da} and a.dp = {dp} and a.dcom = {dcom} and a.issn = {issn} and b.mesh_name={mesh_name} MERGE (a)-[r:HAS_MESH {mesh_type:{mesh_type}}]->(b)"
	start = time.time()
	counter_skip = 1
	counter_add_pm = 1
	#check for file compression again
	infile = compressCheck(file_name)
	pmid = ""
	pub_new = True
	count_line = 0
	issn=title=dcom=jt=da=dp=""
	for line in infile:
		count_line += 1
		line = line.strip("\r\n")
		# print "line = "+line
		if len(line) == 0:
			nothing = 0
		elif line[0:2] == 'IS':
			if re.match('.*?(?:Print|Electronic).*?',line):
				issn = line.split("-", 1)[1].split(" ")[1].strip()
		elif line[0:2] == 'DP':
			dp= line.split("-", 1)[1].strip()
		elif line[0:2] == 'DA':
			da = line.split("-", 1)[1].strip()
			da = da[0:4]+"-"+da[4:6]+"-"+da[6:8]
		elif line[0:4] == 'DCOM':
			dcom = line.split("-", 1)[1].strip()
		elif line[0:4] == "PMID":
			pub_new = True
			pmid = line.split("-", 1)[1].strip()
			# print "search_name=",sp[1],"pmid = ",pmid
			if counter_add_pm % 10000 == 0:
				print round((time.time() - start) / 60, 3)
				print "pm = ", counter_add_pm
				print statement1
			# dont add relationship between pmid and mesh term if already done
		if pub_new == True:
			if line[0:3] == "MH ":
				#print line
				counter_add_pm += 1
				m = line.split("-", 1)[1].strip()
				# print 'mesh name  = ',m
				# split when multiple forward slashes as mesh terms are collapsed by DO ID
				if m.count("/") > 1:
					ms = m.split("/")
					for e in range(1, len(ms)):
						m_new = ms[0] + "/" + ms[e]
						if '*' in m_new:
							m_new = m_new.replace("*", "")
							tx.run(statement1, {"mesh_name": m_new, "pmid": pmid, "issn":issn, "dcom": dcom, "mesh_type": "main"})
						else:
							tx.run(statement1, {"mesh_name": m_new, "pmid": pmid, "issn":issn, "dcom": dcom, "mesh_type": "not_main"})
				else:
					if '*' in m:
						m = m.replace("*", "")
						tx.run(statement1, {"mesh_name": m, "pmid": pmid, "issn":issn, "dcom": dcom, "mesh_type": "main"})
					else:
						tx.run(statement1, {"mesh_name": m, "pmid": pmid, "issn":issn, "dcom": dcom, "mesh_type": "not_main"})
			issn=title=dcom=jt=""

	infile.close()
	# catch the last ones
	tx.commit()
	end = time.time()
	logger.debug("Added "+str(counter_add_pm - 1)+" new pubmed - mesh relationships")
	logger.debug("Total time taken: "+str(round(end - start, 3))+" seconds")
	#logger.debug("Deleting file "+str(file_name))
	#os.remove(file_name)
	return "All done"
	session.close()

def run_pubmed_get(keep_tmp):
	start = time.time()

	#get today's date
	td = time.strftime('%Y/%m/%d')

	# set tmp directory
	d = '/tmp/pubmed_get/'
	num_files = 10

	if not os.path.exists(d):
		os.makedirs(d)

	pmid_get(d,td)
	c = parse_pmids(d)
	split_pmids(c, num_files, d)
	for file in os.listdir(d):
		if file.startswith("pmid_split"):
			if not file.endswith(".medline"):
				file = d + file
				medline_get(file)

	#create output file
	td = time.strftime('%Y_%m_%d')
	oName = "/tmp/pubmed_medline"+td+".txt"
	cat_com = "cat " + d + "/*.medline > "+oName
	os.system(cat_com)

	# clean up
	if (keep_tmp == False):
		shutil.rmtree(d)
	end = time.time()

	#compress data
	com="management/medline_reducer.sh "+oName
	print "Compressing data..."
	print com
	os.system(com)
	load_mesh(oName+".melodi.gz")

	print "\nTotal time taken:", round((end - start) / 60, 3), "minutes"




@task(name='tasks.daily_mesh')
def daily_mesh():
	run_pubmed_get(keep_tmp=True)

@task(name='tasks.neo4j_check')
def neo4j_check():
	try:
		session = driver.session()
		com = "match (n) return n limit 5;"
		c=session.run(com)
	except:
		logger.debug('session not ok - '+time.strftime("%Y-%m-%d %H:%M:%S"))
		#com = 'echo \'Subject: MELODI graph down\' | "cat - <(echo \'The MELODI neo4j graph is not responding\') | sendmail ben.elsworth@bristol.ac.uk"'
		com = 'echo \'Subject: MELODI graph not responding\' | sendmail ben.elsworth@bristol.ac.uk'
		logger.debug(com)
		subprocess.call(com,shell=True)

#set pubmed set as global
p_set=set()

# create set of pubmed id from Pubmed nodes
def pubmedFind():
	session = driver.session()
	print "Checking pubmed ids"
	start = time.time()
	#check for pubmed entries which have associiated mesh terms
	#pSearch is safe as failures to create realationships will cause problems but it is very slow
	#pSearch_basic is quick and risky
	pSearch = "match (p:Pubmed)-[h:HAS_MESH]->(m:Mesh) with p, COUNT(h) as c where c > 0 return p.pmid"
	pSearch_basic = "MATCH (n:Pubmed) RETURN n.pmid"
	pSearch_processed = "MATCH (n:Pubmed) where n.processed = true return n.pmid"
	for record in session.run(pSearch_processed):
		#p_set.add(record[0].rstrip('\n').encode("ascii"))
		p_set.add(record[0])
	end = time.time()
	session.close()
	print "Time taken:", round(end - start, 3), "seconds"


def addPubmedNodes(file_name,job_name,user_id,pCount):
	session = driver.session()
	print "Adding pubmed data for ", file_name
	start = time.time()
	#check file exists
	if not os.path.isfile(file_name):
		print "The file",file_name,"is missing!"
		exit()
	counter = 0
	tx = session.begin_transaction()
	# check if pubmed node exists
	SearchSet.objects.filter(job_name=job_name,user_id=user_id).update(job_status='Searching graph',job_progress=1)
	pubmedFind()
	SearchSet.objects.filter(job_name=job_name,user_id=user_id).update(job_status='Adding pubmed data',job_progress=10)

	#statement = "MERGE (n:Pubmed {pmid:{pmid},title:{title},dcom:{dcom},jt:{jt}})"
	statement = "MERGE (n:Pubmed {pmid:{pmid}}) ON MATCH SET n.title={title},n.jt={jt} on CREATE SET n.dcom={dcom},n.issn={issn},n.title={title},n.jt={jt}"
	inCount = 0
	passCount = 0
	in_ti = False
	in_jt = False
	pmid=""
	issn=""
	count_pmid=1
	dcom=""
	title=""
	jt=""
	#check for file compression
	infile = compressCheck(file_name)
	for line in infile:
		line = line.strip("\r\n")
		# print "line = "+line
		if len(line) == 0:
			nothing = 0
		elif line[0:3] == "TI ":
			in_ti = True
			title = line.split("-", 1)[1].strip()
		elif line[0:3] == "JT ":
			in_jt = True
			jt = line.split("-", 1)[1].strip()
		elif line[0:2] == 'IS':
			if re.match('.*?(?:Print|Electronic).*?',line):
				issn = line.split("-", 1)[1].strip()
		elif line[0:4] == 'DCOM':
			dcom = line.split("-", 1)[1].strip()
			dcom = dcom[0:4]+"-"+dcom[4:6]+"-"+dcom[6:8]
		elif line[0:4] == "PMID":
			count_pmid+=1
			if count_pmid % 1000 == 0:
				#update db
				pc = round((float(count_pmid)/float(pCount))*100)
				SearchSet.objects.filter(job_name=job_name,user_id=user_id).update(job_progress=pc)
			#add to db data for previous entry
			if pmid != "":
				# create new pubmed node if needed
				if pmid not in p_set:
					tx.run(statement, {"pmid": pmid,'issn':issn,'dcom':dcom,'title':title,'jt':jt})
					dcom=""
					pmid=""
					issn = ""
					title=""
					jt=""
					inCount += 1
					counter += 1
					#if counter % 1000 == 0:
						# print(statement1)
					#	tx.commit()
					#	tx = session.begin_transaction()
				else:
					passCount += 1
			pmid = line.split("-", 1)[1].strip()
		if in_ti == True:
			if line[0] == " ":
				title += " "+line.strip()
			elif line[0:3] != 'TI ':
				in_ti = False
		if in_jt == True:
			if line[0] == " ":
				jt += " "+line.strip()
			elif line[0:3] != 'JT ':
				in_jt = False

	#check for bad files
	if title == "" and pmid == "":
		print "Incorrect file format - "+str(job_name)+":"+str(job_name)
		SearchSet.objects.filter(job_name=job_name,user_id=user_id).update(job_status='Failed - incorrect file format',job_progress=1)
		os.remove(file_name)
		exit()

	infile.close()
	#catch the last one
	print "Running last commit..."
	tx.run(statement, {"pmid": pmid,'issn':issn,'dcom':dcom,'title':title,'jt':jt})
	tx.commit()
	print "Added ", inCount, "new pubmed ids"
	print "Skipped ", passCount, "pubmed ids that were already present"
	end = time.time()
	print "Time taken:", round(end - start, 3), "seconds"
	session.close()

@task
#@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000, stop_max_attempt_number=3)
def db_citations(sp, file_name):
	session = driver.session()
	logger.debug('in db_citations')
	#count number of pubmed entries in file
	if file_name.endswith('.gz') or file_name.endswith('.gz'):
		cmd = "gunzip -c "+file_name+" | grep -c '^PMID' "
		logger.debug("reading gzip file")
	elif file_name.endswith('.zip'):
		cmd = "unzip -c "+file_name+" | grep -c '^PMID' "
		logger.debug("reading zip file")
	else:
		cmd = "grep -c '^PMID' "+file_name
		logger.debug("reading uncompressed file")

	try:
		logger.debug("Counting articles...")
		pCount = int(subprocess.check_output(cmd, shell=True))
		logger.debug("Number of pubmed articles = "+str(pCount))
	except subprocess.CalledProcessError as grepexc:
		logger.debug("error for pmid count", grepexc.returncode, grepexc.output)
		SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='Failed - incorrect file format',job_progress=1)
		os.remove(file_name)
		exit()
	logger.debug(cmd)
	#os.system(grep -c '^PMID')
	#SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='Adding pubmed data',job_progress=1)
	print "Adding data for ", file_name
	start = time.time()
	addPubmedNodes(file_name,sp[0],sp[1],pCount)

	SearchSet.objects.filter(job_name=sp[0]).update(job_status='Adding relationships',job_progress=1)
	session.run("MERGE (n:SearchSet{search_name:'" + sp[0] + "',user_id:'" + sp[1] + "'})")

	tx = session.begin_transaction()

	# create dictionary for mesh summaries
	meshSum = {}

	# pFind = pubmedFind()
	statement1 = "MATCH (a:Pubmed),(b:Mesh) where a.pmid = {pmid} and b.mesh_name={mesh_name} CREATE (a)-[r:HAS_MESH {mesh_type:{mesh_type}}]->(b)"
	statement2 = "MATCH (a:SearchSet),(b:Pubmed) where a.search_name = {search_name} and a.user_id = '"+sp[1]+"' and b.pmid={pmid} CREATE (a)-[r:INCLUDES]->(b)"
	statement3 = "MERGE (a:Pubmed {pmid:{pmid}}) ON MATCH SET a.processed = true"
	#statement3 = "MATCH (a:Pubmed),(b:Sentence) where a.pmid = {pmid} and b.pmid={pmid} CREATE (a)-[r:SEM]->(b)"
	# statement3 = "CREATE p = (a:SearchSet{search_name:{search_name}})-[:INCLUDES]->(b:Pubmed{pmid:{pmid}}->[:HAS_MESH)"
	counter_skip = 1
	counter_add_pm = 1
	counter_add_sp = 1
	#check for file compression again
	infile = compressCheck(file_name)
	pmid = ""
	pub_new = True
	count_line = 0

	for line in infile:
		count_line += 1
		#if count_line % 100000 == 0:
			#print "line:", count_line
		#if counter_add_pm % 10000 == 0 or counter_add_sp % 10000 == 0:
		#	tx.commit()
			#if tx.finished == False:
			#	print "Commit failed, trying again"
			#	raise Exception("Commit failed, trying again")
			#else:
				#tx = session.begin_transaction()
		#	tx = session.begin_transaction()
		if counter_add_sp % 1000 == 0:
			#add to db
			pc = round((float(counter_add_sp)/float(pCount))*100)
			SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_progress=pc)
		line = line.strip("\r\n")
		# print "line = "+line
		if len(line) == 0:
			nothing = 0
		elif line[0:4] == "PMID":
			pub_new = True
			pmid = line.split("-", 1)[1].strip()
			# print "search_name=",sp[1],"pmid = ",pmid
			tx.run(statement2, {"search_name": sp[0], "pmid": pmid})
			counter_add_sp += 1
			if counter_add_sp % 10000 == 0:
				print round((time.time() - start) / 60, 3)
				print "sp = ", counter_add_sp, "pm = ", counter_add_pm
			# dont add relationship between pmid and mesh term if already done
			if pmid in p_set:
				pub_new = False
			else:
				tx.run(statement3, {"pmid": pmid})
		if pub_new == True:
			if line[0:3] == "MH ":
				#print line
				counter_add_pm += 1
				m = line.split("-", 1)[1].strip()
				# print 'mesh name  = ',m
				# split when multiple forward slashes as mesh terms are collapsed by DO ID
				if m.count("/") > 1:
					ms = m.split("/")
					for e in range(1, len(ms)):
						m_new = ms[0] + "/" + ms[e]
						if '*' in m_new:
							m_new = m_new.replace("*", "")
							tx.run(statement1, {"mesh_name": m_new, "pmid": pmid, "mesh_type": "main"})
						else:
							tx.run(statement1, {"mesh_name": m_new, "pmid": pmid, "mesh_type": "not_main"})
				else:
					if '*' in m:
						m = m.replace("*", "")
						tx.run(statement1, {"mesh_name": m, "pmid": pmid, "mesh_type": "main"})
					else:
						tx.run(statement1, {"mesh_name": m, "pmid": pmid, "mesh_type": "not_main"})
	infile.close()
	# catch the last ones
	tx.commit()
	end = time.time()
	logger.debug("Added "+str(counter_add_sp - 1)+" new search set - pubmed relationships")
	logger.debug("Added "+str(counter_add_pm - 1)+" new pubmed - mesh relationships")
	logger.debug("Total time taken: "+str(round(end - start, 3))+" seconds")
	logger.debug("Deleting file "+str(file_name))
	os.remove(file_name)
	SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='Complete',pTotal=counter_add_sp - 1,job_progress=100)
	return "All done"
	session.close()

@task
#@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000, stop_max_attempt_number=3)
def pmid_process(sp, file_name):
	session = driver.session()
	logger.debug('In pmid_process')
	#count number of pubmed entries in file
	if file_name.endswith('.gz') or file_name.endswith('.gz'):
		cmd = "gunzip -c "+file_name+" | grep -c '' "
		logger.debug("reading gzip file")
	elif file_name.endswith('.zip'):
		cmd = "unzip -c "+file_name+" | grep -c '' "
		logger.debug("reading zip file")
	else:
		cmd = "grep -c '' "+file_name
		logger.debug("reading uncompressed file")
	try:
		logger.debug("Counting articles..."+cmd)
		pCount = int(subprocess.check_output(cmd, shell=True))
		logger.debug("Number of pubmed articles = "+str(pCount))
	except subprocess.CalledProcessError as grepexc:
		logger.debug("error for pmid count", grepexc.returncode, grepexc.output)
		SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='File format error',job_progress=1)
		os.remove(file_name)
		exit()
	print "Adding data for ", file_name
	start = time.time()

	#add search set
	session.run("MERGE (n:SearchSet{name:'" + sp[0] + "_"+sp[1]+"'})")

	if pCount<maxA:
		#check if searchset already exists and delete
		com="match (s:SearchSet)-[r]-(p:Pubmed) where s.name = '"+sp[0]+"_"+sp[1]+"' delete s,r;"
		logger.debug(com)
		session.run(com)
		#add new data
		tx = session.begin_transaction()
		statement = "MATCH (a:SearchSet),(b:Pubmed) where a.name = {name} and b.pmid={pmid} CREATE (a)-[r:INCLUDES]->(b)"
		print statement
		counter=0
		SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='Adding relationships',job_progress=1)
		infile = compressCheck(file_name)
		for line in infile:
			line = line.strip("\r\n")
			if line.isdigit():
				tx.run(statement, {"name": sp[0]+"_"+sp[1], "pmid": int(line)})
				counter+=1
				if counter % 1000 == 0:
					pc = round((float(counter)/float(pCount))*100)
					SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_progress=pc)
					logger.debug(pc)
					tx.close()
					tx = session.begin_transaction()
			else:
				print line+"is not a correct PubMed ID"
		tx.commit()
		end = time.time()
		logger.debug("Total time taken: "+str(round(end - start, 3))+" seconds")
		logger.debug("Deleting file "+str(file_name))
		os.remove(file_name)

		#calculate the actual number of publications being used
		s = "MATCH (s:SearchSet)-[:INCLUDES]-(p:Pubmed) where s.name = '"+sp[0] + "_"+sp[1]+"' return count(p) as p;"
		logger.debug(s)
		result = session.run(s)
		record = next(iter(result))
		logger.debug("record = "+str(record[0]))
		pCount = record[0]

		SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='Complete',pTotal=pCount,job_progress=100)
		session.close()
	else:
		SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='Too many articles (max 1 million)',job_progress=0)

	#remove file
	os.remove(file_name)

@task
#@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000, stop_max_attempt_number=3)
def pub_sem(sp):
	session = driver.session()
	logger.debug('in db_pub')
	logger.debug('id = '+str(sp[0]))
	logger.debug('user_id = '+str(sp[1]))
	logger.debug('desc = '+sp[2])

	#check if searchset already exists and delete
	com="match (s:SearchSet)-[r]-(p:Pubmed) where s.name = '"+sp[0]+"_"+sp[1]+"' delete s,r;"
	logger.debug(com)
	session.run(com)

	#create searchset
	session.run("MERGE (n:SearchSet{name:'" + sp[0] + "_"+sp[1] + "'})")

	start=time.time()
	print "\n### Getting ids for "+sp[2]+" ###"
	url="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
	params = {'db': 'pubmed', 'term': sp[2],'retmax':'1000000000','rettype':'uilist'}

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

	tx = session.begin_transaction()
	statement = "MATCH (a:SearchSet),(b:Pubmed) where a.name = {name} and b.pmid={pmid} CREATE (a)-[r:INCLUDES]->(b)"
	print statement
	counter=0
	SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='Adding relationships',job_progress=1)

	#count the number of pmids
	cmd = "grep -c '<Id>' "+ranFile
	print cmd
	#check for empty searches
	try:
		pCount = int(subprocess.check_output(cmd, shell=True))
	except subprocess.CalledProcessError as grepexc:
		print "error code", grepexc.returncode, grepexc.output
		SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='Complete',pTotal=0,job_progress=100)


	print "Total pmids: "+str(pCount)

	if pCount<maxA:
		#add to the session
		print "\n### Parsing ids ###"
		start = time.time()
		f = open('/tmp/'+ran+'.txt', 'r')
		for line in f:
			l = re.search(r'.*?<Id>(.*?)</Id>', line)
			if l:
				tx.run(statement, {"name": sp[0]+"_"+sp[1], "pmid": int(l.group(1))})
				counter+=1
				if counter % 1000 == 0:
					pc = round((float(counter)/float(pCount))*100)
					SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_progress=pc)
					#this releases the lock on the database and allows multiple inserts at the same time
					tx.commit()
					tx = session.begin_transaction()
		tx.commit()


		SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='Counting',job_progress=99)

		#calculate the actual number of publications being used
		s = "MATCH (s:SearchSet)-[:INCLUDES]-(p:Pubmed) where s.name = '"+sp[0] + "_"+sp[1]+"' return count(p) as p;"
		logger.debug(s)
		result = session.run(s)
		record = next(iter(result))
		logger.debug("record = "+str(record[0]))
		pCount = record[0]

		SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='Complete',pTotal=pCount,job_progress=100)

		end = time.time()
		print "\tTime taken:", round((end - start) / 60, 3), "minutes"
		session.close()
		return counter
	else:
		SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='Too many articles',job_progress=0)


@task
#@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000, stop_max_attempt_number=3)
def db_sem(sp):
	session = driver.session()
	logger.debug('in db_sem')
	print('id = '+str(sp[0]))
	print('user_id = '+str(sp[1]))
	print('sem_location = '+sp[2])
	print('desc = '+sp[3])

	#check if searchset already exists and delete
	com="match (s:SearchSet)-[r]-(p:Pubmed) where s.name = '"+sp[0]+"_"+sp[1]+"' delete s,r;"
	logger.debug(com)
	session.run(com)

	#create searchset
	session.run("MERGE (n:SearchSet{name:'" + sp[0] + "_"+sp[1] + "'})")


	semSearch = list()
	for i in sp[3].split(','):
		if len(i)>0:
			semSearch.append(i.encode("ascii").strip())
	print('semSearch = '+str(semSearch))
	SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='Searching the graph',job_progress=1)
	#match (sem:SDB_triple) where sem.o_name in ['Renal Cell Carcinoma'] return sem.pid union match (sem:SDB_triple) where sem.s_name in ['Renal Cell Carcinoma'] return sem.pid;
	semString = ''
	if sp[2] == 'Subject':
		semString = 'match (p:Pubmed)-[sem1:SEM]->(sem:SDB_triple) where sem.s_name in '+str(semSearch)+' return p.pmid;'
	elif sp[2] == 'Object':
		semString = 'match (p:Pubmed)-[sem1:SEM]->(sem:SDB_triple) where sem.o_name in '+str(semSearch)+' return p.pmid;'
	elif sp[2] == 'Either':
		semString = 'match (p:Pubmed)-[sem1:SEM]->(sem:SDB_triple) where sem.s_name in '+str(semSearch)+' return p.pmid union match (p:Pubmed)-[sem1:SEM]->(sem:SDB_triple) where sem.o_name in '+str(semSearch)+' return p.pmid;'
	print('semString = '+semString)

	pmidDic = {}
	for res in session.run(semString):
		pmidDic[res[0]]=''

	#get number of pmids
	pCount = len(pmidDic)
	print "pCount = "+str(pCount)

	if pCount<maxA:

		tx = session.begin_transaction()
		statement = "MATCH (a:SearchSet),(b:Pubmed) where a.name = {name} and b.pmid={pmid} CREATE (a)-[r:INCLUDES]->(b)"
		print statement
		counter=0
		SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='Adding relationships')
		for pmid in pmidDic:
			#print 'pmid = '+pmid
			tx.run(statement, {"name": sp[0]+"_"+sp[1], "pmid": int(pmid)})
			counter+=1
			if counter % 1000 == 0:
				pc = round((float(counter)/float(pCount))*100)
				SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_progress=pc)
				#this releases the lock on the database and allows multiple inserts at the same time
				tx.commit()
				tx = session.begin_transaction()
		tx.commit()

		#calculate the actual number of publications being used
		s = "MATCH (s:SearchSet)-[:INCLUDES]-(p:Pubmed) where s.name = '"+sp[0] + "_"+sp[1]+"' return count(p) as p;"
		logger.debug(s)
		result = session.run(s)
		record = next(iter(result))
		logger.debug("record = "+str(record[0]))
		pCount = record[0]

		SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='Complete',pTotal=pCount,job_progress=100)
		session.close()
	else:
		SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='Too many articles',job_progress=0)


def do_fet(a1,a2,b1,pmid_total):
	#print("a1 = ",a1,"a2 = ",a2,"b1 = ",b1)
	#logger.debug("a1 = ",a1,"a2 = ",a2,"b1 = ",b1)
	#add 1 to freq value if zero
	if b1 == 0:
		b1 = 1
	if int(a1)>0 and int(a2-a1)>0 and b1>0 and (pmid_total-b1)>0:
		#oddsratio, pvalue = stats.fisher_exact([[int(a1),int(a2-a1)],[b1,pmid_total-b1]],alternative="greater")
		oddsratio, pvalue = stats.fisher_exact([[int(a1),int(a2-a1)],[b1,pmid_total-b1]])
		#print "fet = ",pvalue, oddsratio, "\n"
		#logger.debug("fet = "+str(pvalue)+":"+str(oddsratio))
		return(a1,a2,b1,pmid_total,oddsratio,pvalue)
	else:
		print "something is wrong with this FET:",a1,a2,b1
		return(a1,a2,b1,pmid_total,0,1)

def setup_fet(c,ss,job_name,ssNum):
	session = driver.session()
	jobType = c.job_type
	userID = c.user_id
	#get year range
	year1 = c.year_range.split("-")[0].strip()
	year2 = c.year_range.split("-")[1].strip()
	logger.debug('year1 = '+year1+' year2 = '+year2)
	yearString = ''
	if year1 != '1950' or year2 != '2017':
		yearString = "p.dp < '"+year2+"' "
		if jobType != "semmed_t" and jobType != "semmed_c":
			yearString = " where "+yearString
		else:
			yearString = " and "+yearString
	print "Running FET on",ss,"with job name",job_name,"and job type",jobType

	#mnimum number of publications
	minP=0

	#filter semmed to ignore high freq items
	#keep semmed pmid counts as non-unique to include multiple occurences per article and title
	#semString = ''
	#if ssNum == 1:
		#semString = "-[:SEMO]-(si:SDB_item) where si.i_freq<"+semFreq
	#	semString = "-[:SEMO]-(si:SDB_item)"+yearString+"with count(p.pmid) as pc,se,si where pc>"+str(minP)+" and si.s_freq<"+str(semFreq)+" and si.o_freq<"+str(semFreq)
	#else:
		#semString = "-[:SEMS]-(si:SDB_item) where si.i_freq<"+str(semFreq)
	#	semString = "-[:SEMS]-(si:SDB_item)"+yearString+"with count(p.pmid) as pc,se,si where pc>"+str(minP)+" and si.s_freq<"+str(semFreq)+" and si.o_freq<"+str(semFreq)

	#count articles with search - need to consider how this changes with a time restriction!
	article_number=SearchSet.objects.get(id=ss).pTotal
	if year2 != '2017':
		aCom = "match (s:SearchSet{name:'"+job_name+"_"+userID+"'})-[:INCLUDES]-(p:Pubmed) where p.dp < '"+year2+"' return count(distinct(p)) as pCount;"
		aRes=session.run(aCom)
		article_number=next(iter(aRes))['pCount']
		logger.debug(aCom)
		logger.debug('article_number = '+str(article_number))

	if jobType == "meshMain":
		comm= "match (s:SearchSet{name:'"+job_name+"_"+userID+"'})<-[r:INCLUDES]->(p:Pubmed)"
		comm += "<-[:HAS_MESH{mesh_type:'main'}]->(m:Mesh)"+yearString+" with count(distinct(p.pmid)) as pc,m "
		#comm += "return pc, m.mesh_id, m.mesh_name, m.freq_main;"
		comm += "return pc, m.mesh_id, m.mesh_name, m.freq_"+str(int(year2)-1)
	elif jobType == "notMeshMain":
		comm = "match (s:SearchSet{name:'"+job_name+"_"+userID+"'})<-[r:INCLUDES]->(p:Pubmed)"
		comm += "<-[h:HAS_MESH]->(m:Mesh)"+yearString+" with count(distinct(p.pmid)) as pc,m "
		comm += " return pc, m.mesh_id, m.mesh_name, m.freq;"
	elif jobType == "semmed_c":
		comm = "match (s:SearchSet{name:'"+job_name+"_"+userID+"'})-[r:INCLUDES]-(p:Pubmed)-[:SEM]-(st:SDB_triple)-[:SEMS|:SEMO]-(si:SDB_item) where si.i_freq <"+str(semFreq)+" return count(distinct(p)) as pc,si.name,si.i_freq;"
	elif jobType == "semmed_t":
		#count(distinct) avoids issues with multiple triples called per article - not sure if this is the right thing to do...?
		comm = "match (s:SearchSet{name:'"+job_name+"_"+userID+"'})-[r:INCLUDES]-(p:Pubmed)-[:SEM]-(st:SDB_triple)-[:SEMO]-(si1:SDB_item) "
		comm += "where si1.i_freq <"+str(semFreq)+yearString+" with distinct p,si1,st match (st)-[:SEMS]-(si2:SDB_item) where si2.i_freq <"+str(semFreq)+" with "
		comm += " count(distinct(p)) as pc,st,si1,si2 return pc,st.pid,st.s_name,st.predicate,st.o_name,st.freq_"+str(int(year2)-1)+";"

	print(comm)
	logger.debug(comm)
	t=session.run(comm)

	#get citation total for year
	pFile='data/semmed_citation_totals.txt'
	infile = open(pFile, 'r')
	for line in infile:
		if not line.startswith("#"):
			y,c = line.split(":")
			#print y,c
			if y == year2:
				pmid_total=int(c)
				break
			else:
				pmid_total=int(c)
	print year2,pmid_total
	logger.debug('pmid_total for '+year2+' = '+str(pmid_total))

	fet_dict = {}
	if t:
		for res in t:
			#print(res)
			#fet for ss
			obsCount=res[0]
			if jobType == 'meshMain' or jobType == 'notMeshMain':
				ID = res[1].rstrip('\n').encode("ascii")
				r=res[2].rstrip('\n').encode("ascii")
				mFreq = res[3]
			elif jobType == "semmed_c":
				ID = 0
				r=res[1].rstrip('\n').encode("ascii")
				mFreq = res[2]
			elif jobType == "semmed_t":
				ID = res[1]
				r=res[2].rstrip('\n').encode("ascii")+"||"+res[3].rstrip('\n').encode("ascii")+"||"+res[4].rstrip('\n').encode("ascii")
				mFreq = res[5]
			#logger.debug('job'+jobType)
			a=do_fet(obsCount,article_number,mFreq,pmid_total)
			fet_dict[r+':'+str(ID)]=a
	#logger.debug(fet_dict)
	#print fet_dict

	#do correction for multiple testing (pvalus is 6the element in array)
	v=[item[5] for item in fet_dict.values()]
	if len(v)>0:
		logger.debug('Correcting pvals with '+str(len(v))+' values')
		#vc=sm.multipletests(pvals=v,method='bonferroni')
		vc=sm.multipletests(pvals=v,method='fdr_bh')
		c=0
		#add new pvals to dictionary
		for k in fet_dict:
			fet_dict[k]=fet_dict[k]+(vc[1][c],)
			c+=1
		print 'len(fet_dict) = '+str(len(fet_dict))
		#set min corrected pval
		#cor_pval=0.005
		cor_pval = 1e-5
		#print the results to file
		for record in session.run("match (s:SearchSet{name:'"+job_name+"_"+userID+"'}) return ID(s)"):
			ss_id=record[0]
		print "ss_id = ",ss_id
		filter_fet_dict = {}
		with gzip.open(tmpDir+'saved_data/fet/'+str(ss)+'_'+year2+'.'+jobType+'.fet.gz', 'wb') as f:
			f.write("term\ta1\ta2\tb1\tb2\todds_ratio\tpvalue\tcor_pvalue\n")
			for res in fet_dict:
				if float(fet_dict[res][6]) < cor_pval:
					filter_fet_dict[res] = fet_dict[res]
					f.write(res+"\t"+str(fet_dict[res][0])+"\t"+str(fet_dict[res][1])+"\t"+str(fet_dict[res][2])+"\t"+str(fet_dict[res][3])+"\t"+str(fet_dict[res][4])+"\t"+str(fet_dict[res][5])+"\t"+str(fet_dict[res][6])+"\n")

		print "Finished FET"
	else:
		filter_fet_dict = {}
	session.close()
	#logger.debug(filter_fet_dict)
	logger.debug('Number of FET after cpval = '+str(len(filter_fet_dict)))
	return(filter_fet_dict)

def run_fet(c,ss1,ss2):
	userID = c.user_id
	jobType = c.job_type
	yearRange = c.year_range
	year2 = c.year_range.split("-")[1].strip()
	Compare.objects.filter(id=c.id).update(job_status='Running FET 1',job_progress=10)
	start = time.time()

	#d=""
	print "Time taken:", round(time.time() - start, 3), "seconds"
	start = time.time()
	s1=SearchSet.objects.get(id=ss1)
	ss1_name = s1.job_name
	s1Check = SearchSetAnalysis.objects.filter(ss_id=s1,job_type=jobType,complete=True,year_range=yearRange)

	print "s1Check = ",len(s1Check)

	if len(s1Check)==0:
		#if d=="":
		#	d=get_mesh_freqs()
		ss1_fet=setup_fet(c,ss1,ss1_name,1)
		s=SearchSetAnalysis(ss_id=s1,job_type=jobType,complete=True,year_range=yearRange)
		s.save()
	else:
		print ss1,"already analysed, getting from file."
		ss1_fet=dict()
		f=tmpDir+'saved_data/fet/'+str(ss1)+'_'+year2+'.'+str(jobType)+'.fet.gz'
		if os.path.isfile(f):
			with gzip.open(f, 'rb') as f:
				next(f)
				for line in f:
					l=line.rstrip('\n').encode("ascii").split("\t")
					ss1_fet[l[0]]=(int(l[1]),int(l[2]),float(l[3]),int(l[4]),float(l[5]),float(l[6]),float(l[7]))

	if ss2 != '':
		s2=SearchSet.objects.get(id=ss2)
		ss2_name = s2.job_name
		s2Check = SearchSetAnalysis.objects.filter(ss_id=s2,job_type=jobType,complete=True,year_range=yearRange)
		Compare.objects.filter(id=c.id).update(job_status='Running FET 2',job_progress=50)
		if len(s2Check)==0:
			#if d=="":
			#	d=get_mesh_freqs()
			ss2_fet=setup_fet(c,ss2,ss2_name,2)
			s=SearchSetAnalysis(ss_id=s2,job_type=jobType,complete=True,year_range=yearRange)
			s.save()
		else:
			print ss2,"already analysed, getting from file."
			ss2_fet=dict()
			f=tmpDir+'saved_data/fet/'+str(ss2)+'_'+year2+'.'+str(jobType)+'.fet.gz'
			if os.path.isfile(f):
				with gzip.open(f, 'rb') as f:
					next(f)
					for line in f:
						l=line.rstrip('\n').encode("ascii").split("\t")
						ss2_fet[l[0]]=(int(l[1]),int(l[2]),float(l[3]),int(l[4]),float(l[5]),float(l[6]),float(l[7]))
		print "Time taken:", round(time.time() - start, 3), "seconds"
		return (ss1_fet,ss2_fet)
	else:
		return (ss1_fet)

def overlap_query(query):
	session = driver.session()
	oDic = defaultdict(dict)
	for res in session.run(query):
		ss = res[0].encode("ascii")
		mn = res[1].encode("ascii")
		pm = res[2]
		if mn in oDic:
			if ss in oDic[mn]:
				a = oDic[mn][ss]
				if pm not in a:
					a.append(pm)
					oDic[mn][ss] = a
			else:
				oDic[mn][ss] = [pm]
		else:
			oDic[mn][ss] = [pm]
	return oDic

def overlapper(c,fet_1,fet_2):
	session = driver.session()
	jobType = c.job_type
	userID = c.user_id
	logger.debug(jobType+" - Finding shared terms")
	s = c.job_desc.split(":")
	s1 = s[0].strip()+"_"+c.user_id
	s2 = s[1].strip()+"_"+c.user_id
	share_keys = fet_1.viewkeys() & fet_2.viewkeys()
	logger.debug(jobType+" - Number of shared sig terms = "+str(len(share_keys)))
	#print 'share_keys = ',list(share_keys)
	share_keys_list = list()
	for i in share_keys:
		share_keys_list.append(i.split(":")[0])
	#print "share_keys_list = ",share_keys_list

	#get year range
	year1 = c.year_range.split("-")[0].strip()
	year2 = c.year_range.split("-")[1].strip()
	logger.debug('year1 = '+year1+' year2 = '+year2)
	yearString = ''
	if year1 != '1950' or year2 != '2017':
		yearString = "p.dp >= '"+year1+"' and p.dp < '"+year2+"' and"

	tDict = dict()
	if jobType == "meshMain" or jobType == "notMeshMain":
		#get meshTree location data
		#remove subheadings from shared keys
		share_keys_list_no_sh = list()
		for i in share_keys_list:
			s = i.split("/")[0]
			share_keys_list_no_sh.append(s)

		tCom = "match (m:MeshTree) where m.mesh_name in "+str(share_keys_list_no_sh)+" return m.mesh_name,m.tree_id;"
		#logger.debug(jobType+" - "+tCom)
		print tCom
		for res in session.run(tCom):
			#print res
			mesh_name = res[0]
			tree_id = res[1]
			treeLevel = tree_id.count('.')
			if treeLevel > 0:
				treeLevel += 1
			else:
				treeLevel = 1

			if mesh_name in tDict:
				t=tDict[mesh_name]
				t.append(treeLevel)
			else:
				tDict[mesh_name]=[treeLevel]
		logger.debug(jobType+" - Created tDict")

	oDic = defaultdict(dict)

	qChunks = chunks(share_keys_list,1000)
	counter=0
	for chunk in qChunks:
		counter+=1
		if jobType == "meshMain":
			gCom = "match (s:SearchSet)<-[r:INCLUDES]->(p:Pubmed)<-[h:HAS_MESH{mesh_type:'main'}]->(m:Mesh) using index s:SearchSet(name) where "+yearString+" s.name in ['"+s1+"','"+s2+"'] and m.mesh_name in "+str(chunk)+" return s.name,m.mesh_name,p.pmid;"
		elif jobType == "notMeshMain":
			gCom = "match (s:SearchSet)<-[r:INCLUDES]->(p:Pubmed)<-[h:HAS_MESH]->(m:Mesh) using index s:SearchSet(name) where "+yearString+" s.name in ['"+s1+"','"+s2+"'] and m.mesh_name in "+str(chunk)+" return s.name,m.mesh_name,p.pmid;"
		elif jobType == "semmed_c":
			gCom = "match (s:SearchSet)<-[r:INCLUDES]->(p:Pubmed)<-[:SEM]->(st:SDB_triple)-[:SEMS|:SEMO]-(si:SDB_item) using index s:SearchSet(name) where "+yearString+" s.name in ['"+s1+"','"+s2+"'] and si.name in "+str(chunk)+" return distinct s.name,si.name,p.pmid;"
		logger.debug(jobType+' chunk '+str(counter)+" : "+str(len(chunk)))
		o = overlap_query(gCom)
		oDic.update(o)

	#print oDic
	#logger.debug(jobType+" - "+str(len(oDic)))
	logger.debug(jobType+" - Created oDic ("+str(len(oDic))+"), adding data to Overlap")
	if len(oDic)>0:
		oDicSum = defaultdict(dict)
		for i in oDic:
			j1 = []
			j2 = []
			if s1 in oDic[i]:
				j1 = oDic[i][s1]
			if s2 in oDic[i]:
				j2 = oDic[i][s2]
			ii = set(j1).intersection(j2)
			oDicSum[i][s1] = len(j1) - len(ii)
			oDicSum[i][s2] = len(j2) - len(ii)
			oDicSum[i][s1 + ":" + s2] = len(ii)

		for i in share_keys:
			pMean=(float(fet_1[i][6])+float(fet_2[i][6]))/2
			oMean = (float(fet_1[i][4])+float(fet_2[i][4]))/2
			mesh_name = i.split(":")[0]

			#not sure why this check is necessary
			if s1 in oDicSum[mesh_name]:
				uniq_a = float(oDicSum[mesh_name][s1])
			if s2 in oDicSum[mesh_name]:
				uniq_b = float(oDicSum[mesh_name][s2])

			# add min/mean location in mesh tree
			s = mesh_name.split("/")[0]
			if s in tDict:
				lData = tDict[s]
				# mean position
				# m=float(sum(lData))/len(lData)
				# min position
				m = float(min(lData))
				treeMean = "%.2f" % float(m)
			else:
				treeMean = 1

			# calculate temmpo1 style score
			# score1 = min(bf,df)/max(bf,df)*(bf+df)
			if (uniq_a and uniq_b) > 0.0:
				score = min(uniq_a, uniq_b) / max(uniq_a, uniq_b) * (uniq_a + uniq_b)
				score = ("%4.2f" % score)
			else:
				score = 0
			# ignore cases where no uniques in one search set
			if score > 0:
				shared = s1 + ":" + s2
				if shared in oDicSum[mesh_name]:
					shareScore = oDicSum[mesh_name][shared]
				else:
					shareScore = 0
				s = Overlap(name=i, mc_id=c, mean_cp=("%03.02e" % float(pMean)), mean_odds=("%4.2f" % float(oMean)),
							uniq_a=uniq_a, uniq_b=uniq_b, shared=shareScore, score=score,
							treeLevel=treeMean)
				s.save()
		logger.debug(jobType+" - Finished")
	else:
		logger.debug("There were no overlapping FETs for "+str(s1)+" and "+str(s2))
	session.close()

def semmed_concept_process(c,fet_1,fet_2):
	session = driver.session()
	jobType = c.job_type
	userID = c.user_id
	logger.debug("Processing SemMed concept data...")
	s = c.job_desc.split(":")
	s1_name = s[0].strip()+"_"+c.user_id
	s2_name = s[1].strip()+"_"+c.user_id

def semmed_triple_process(c,fet_1,fet_2):
	session = driver.session()
	jobType = c.job_type
	userID = c.user_id
	logger.debug("Processing SemMed triple data...")
	s = c.job_desc.split(":")
	s1_name = s[0].strip()+"_"+c.user_id
	s2_name = s[1].strip()+"_"+c.user_id

	#read predicates data
	#pFile='data/predicates_filtered.txt'
	#pFile='data/predicates.txt'
	#infile = open(pFile, 'r')
	#predList = list()
	#for line in infile:
	#	if not line.startswith("#"):
	#		predList.append(line.split("\t")[0])
	#print predList

	#create filtered set of fet data based on 'useful' predicates
	# fet_1_keep = {}
	# fet_2_keep = {}
	# print "Reading "+s1_name+" data..."
	# for i in fet_1.viewkeys():
	# 	s = i.split("||")
	# 	if s[1] in predList:
	# 		fet_1_keep[i]=fet_1[i]
	# 		#print i
	# print "Reading "+s2_name+" data..."
	# for i in fet_2.viewkeys():
	# 	s = i.split("||")
	# 	if s[1] in predList:
	# 		fet_2_keep[i]=fet_2[i]
	# 		#print i

	fet_1_keep = fet_1
	fet_2_keep = fet_2

	#find overlapping subject/objects
	print "Finding overlapping objects..."
	overlapping_pids_1 = {}
	overCount = 1
	shared_pids_1_1 = {}
	shared_pids_1_2 = {}
	shared_pids_2 = {}
	semDic = {}
	#check that the filtered dictionaries have data
	print "len fet_1_keep:"+str(len(fet_1_keep))
	print "len fet_2_keep:"+str(len(fet_2_keep))

	#this loop is very slow! - must be a better way
	if len(fet_1_keep) >0 and len(fet_2_keep) >0:
		for i in fet_1_keep.viewkeys():
			s1_reg = re.match(r'(.*?):([0-9]*)$', i)
			s1 = s1_reg.group(1).split("||")
			pid1 = int(s1_reg.group(2))
			if s1[0] != s1[2]:
				for j in fet_2_keep.viewkeys():
					s2_reg = re.match(r'(.*?):([0-9]*)$', j)
					s2 = s2_reg.group(1).split("||")
					pid2 = int(s2_reg.group(2))
					#ignore identical overlaps within triple and at start and end of overlapping triples
					#if s2[0] != s2[2] and s1[0] != s2[2]:
					if s2[0] != s2[2]:
						semDic[pid1]=s1_reg.group(1)
						semDic[pid2]=s2_reg.group(1)
						#print "Comparing "+s1[2]+" and "+s2[0]
						#get overlapping triples and ignore overlaps with same start and end
						if s1[2] == s2[0] and s1[0] != s2[2]:
							#add pids to dictionary
							shared_pids_1_1[pid1]=''
							shared_pids_1_2[pid2]=''
							overlapping_pids_1[overCount]=[pid1,pid2]
							overCount+=1
							#print "s1:object - s2:subject - "+str(s1)+" - "+str(s2)+" pids: "+pid1+"-"+pid2

						#add cases where concept1 overlaps with concept 4
						#elif s1[0] == s2[2]:
							#add pids to dictionary
						#	shared_pids_1_1[pid1]=''
						#	shared_pids_1_2[pid2]=''
						#	overlapping_pids_1[overCount]=[pid1,pid2]
						#	overCount+=1

								#print "s1:subject - s2:object - "+str(s1)+" - "+str(s2)+" pids: "+pid1+"-"+pid2
						#elif s1[0] == s2[0]:
						#	print "s1:subject - s2:subject - "+str(s1)+" - "+str(s2)
						#elif s1[2] == s2[2]:
						#	print "s1:object - s2:object - "+str(s1)+" - "+str(s2)


		s1_keys = shared_pids_1_1.keys()
		s2_keys = shared_pids_1_2.keys()

		#print "shared pids_1_1:"+s1_keys
		#print "shared pids_1_2:"+s2_keys

		#convert strings to ints
		s1_keys = [int(i) for i in s1_keys]
		s2_keys = [int(i) for i in s2_keys]

		#create queries
		year1 = c.year_range.split("-")[0].strip()
		year2 = c.year_range.split("-")[1].strip()
		logger.debug('year1 = '+year1+' year2 = '+year2)
		yearString = ''
		if year1 != '1950' or year2 != '2017':
			yearString = "p.dp >= '"+year1+"' and p.dp < '"+year2+"' and"
		#pCom="match (s:SearchSet)<-[i:INCLUDES]->(p:Pubmed)<-[se:SEM]->(sem:SDB_triple)-[so:SEMO]->(si:SDB_item) where "+yearString+" s.user_id = '"+userID+"' and s.search_name = '"+s1_name+"' and toInt(si.i_freq)<"+str(semFreq)+" and sem.pid in "+str(shared_pids_1_1.keys())+" return s.search_name,sem.pid,p.pmid"
		#pCom+=" UNION match (s:SearchSet)<-[i:INCLUDES]->(p:Pubmed)<-[se:SEM]->(sem:SDB_triple)-[so:SEMS]->(si:SDB_item) where "+yearString+" s.user_id = '"+userID+"' and s.search_name = '"+s2_name+"' and toInt(si.i_freq)<"+str(semFreq)+" and sem.pid in "+str(shared_pids_1_2.keys())+" return s.search_name,sem.pid,p.pmid;"

		pCom="match (s:SearchSet)<-[i:INCLUDES]->(p:Pubmed)<-[se:SEM]->(sem:SDB_triple) where "+yearString+" s.name = '"+s1_name+"' and sem.pid in "+str(s1_keys)+" return s.name,sem.pid,p.pmid"
		pCom+=" UNION match (s:SearchSet)<-[i:INCLUDES]->(p:Pubmed)<-[se:SEM]->(sem:SDB_triple) where "+yearString+" s.name = '"+s2_name+"' and sem.pid in "+str(s2_keys)+" return s.name,sem.pid,p.pmid;"

		print pCom
		logger.debug('semmed overlapper')
		logger.debug(pCom)
		#share_keys = fet_1.viewkeys() & fet_2.viewkeys()
		oDic = defaultdict(dict)

		for res in session.run(pCom):
			ss = res[0].encode("ascii")
			mn = res[1]
			pm = res[2]
			if mn in oDic:
				if ss in oDic[mn]:
					a = oDic[mn][ss]
					if pm not in a:
						a.append(pm)
						oDic[mn][ss] = a
				else:
					oDic[mn][ss] = [pm]
			else:
				oDic[mn][ss] = [pm]
		#print oDic
		#logger.debug(jobType+" - "+str(oDic))
		logger.debug(jobType+" - Created oDic ("+str(len(oDic))+"), adding data to Overlap")

		#get semmed predicate rank info
		pfDic={}
		pFile='data/predicates.txt'
		infile = open(pFile, 'r')
		predList = list()
		for line in infile:
			if not line.startswith("#"):
				p,count,rank = line.split("\t")
				pfDic[p]=int(rank)

		if len(oDic)>0:
			#create object list for bulk insert
			bi = []
			oDicSum = defaultdict(dict)
			for i in overlapping_pids_1:
				#print "i:"+str(i)
				sKey1 = overlapping_pids_1[i][0]
				#print "sKey1:"+sKey1
				sKey2 = overlapping_pids_1[i][1]
				#print "sKey2:"+sKey2
				if s1_name in oDic[sKey1] and s2_name in oDic[sKey2]:
					j1 = oDic[sKey1][s1_name]
					# print "j1:"+str(j1)
					j2 = oDic[sKey2][s2_name]
					# print "j2:"+str(j2)
					ii = set(j1).intersection(j2)
					# print "ii:"+str(ii)
					oDicSum[i][s1_name] = len(j1) - len(ii)
					oDicSum[i][s2_name] = len(j2) - len(ii)
					oDicSum[i][s1_name + ":" + s2_name] = len(ii)

				#for i in overlapping_pids_1:
				#	sKey1 = overlapping_pids_1[i][0]
				#	sKey2 = overlapping_pids_1[i][1]
					sFull1 = semDic[sKey1] + ":" + str(sKey1)
					sFull2 = semDic[sKey2] + ":" + str(sKey2)
					pMean = (float(fet_1[sFull1][6]) + float(fet_2[sFull2][6])) / 2
					#logger.debug('p1 = '+str(float(fet_1[sFull1][6]))+" : p1 = "+str(float(fet_2[sFull2][6]))+ " - mean = "+str(pMean))
					oMean = (float(fet_1[sFull1][4]) + float(fet_2[sFull2][4])) / 2
					uniq_a = float(oDicSum[i][s1_name])
					uniq_b = float(oDicSum[i][s2_name])

					#get minimum predicate frequency rank
					p1 = semDic[sKey1].split("||")[1]
					p2 = semDic[sKey2].split("||")[1]
					#print "p1 = "+p1+":"+str(pfDic[p1])
					#print "p2 = "+p2+":"+str(pfDic[p2])

					if pfDic[p1]>pfDic[p2]:
						pfVal = pfDic[p2]
					else:
						pfVal = pfDic[p1]
					#print "pfVal = "+str(pfVal)

					# calculate temmpo1 style score
					# score1 = min(bf,df)/max(bf,df)*(bf+df)
					if (uniq_a and uniq_b) > 0.0:
						score = min(uniq_a, uniq_b) / max(uniq_a, uniq_b) * (uniq_a + uniq_b)
						score = ("%4.2f" % score)
					else:
						score = 0
					# ignore cases where no uniques in one search set
					if score > 0:
						#s = Overlap(name=semDic[sKey1] + "||" + str(sKey1) + ":" + semDic[sKey2] + "||" + str(sKey2), mc_id=c,
						#			mean_cp=("%03.02e" % float(pMean)), mean_odds=("%4.2f" % float(oMean)), uniq_a=uniq_a,
						#			uniq_b=uniq_b, shared=oDicSum[i][s1_name + ":" + s2_name], score=score, treeLevel=pfVal)
						s1,s2,s3 = semDic[sKey1].split("||")
						s3,s4,s5 = semDic[sKey2].split("||")
						s = Overlap(name=semDic[sKey1] + "||" + str(sKey1) + ":" + semDic[sKey2] + "||" + str(sKey2),
									name1=s1,name2=s2,name3=s3,name4=s4,name5=s5, mc_id=c,
									mean_cp=("%03.02e" % float(pMean)), mean_odds=("%4.2f" % float(oMean)), uniq_a=uniq_a,
									uniq_b=uniq_b, shared=oDicSum[i][s1_name + ":" + s2_name], score=score, treeLevel=pfVal)
						bi.append(s)
						#s.save()
			#add in bulk
			Overlap.objects.bulk_create(bi,batch_size=1000)
			logger.debug(jobType+" - Finished")
		else:
			logger.debug("There were no overlapping FETs for "+str(s1_name)+" and "+str(s2_name))
	else:
		print "There were no entries in the filtered dictionary for either "+str(s1_name)+" or "+str(s2_name)
		logger.debug("There were no entries in the filtered dictionary for either "+str(s1_name)+" or "+str(s2_name))
	session.close()

@task
#def comWrapper(userID,ss1,ss2,jobType,yearRange):
def comWrapper(c_id):
	compare = Compare.objects.get(pk=c_id)
	ss1=compare.job_name.split("_")[0]
	ss2=compare.job_name.split("_")[1]
	userID=compare.user_id
	jobType=compare.job_type
	yearRange=compare.year_range
	logger.debug("Comparing search sets "+ss1+" and "+ss2+" : "+jobType)
	#get compare object
	year2 = int(yearRange.split("-")[1].strip())+1
	#run fet
	fet_1,fet_2=run_fet(compare,ss1,ss2)
	Compare.objects.filter(id=c_id).update(job_status='Looking for overlaps',job_progress=90)
	if len(fet_1) > 0 and len(fet_2) >0:
		#do overlap
		if jobType == "meshMain" or jobType == "notMeshMain":
			overlapper(compare,fet_1,fet_2)
		elif jobType == 'semmed_c':
			overlapper(compare,fet_1,fet_2)
		elif jobType == 'semmed_t':
			semmed_triple_process(compare,fet_1,fet_2)
		Compare.objects.filter(id=compare.id).update(job_status='View results',job_progress=100)
	else:
		Compare.objects.filter(id=compare.id).update(job_status='No results',job_progress=100)

@task
def single_ss_Wrapper(userID,ss1,jobType,yearRange):
	print "Running single ss analysis",ss1
	c=Compare.objects.get(year_range=yearRange,user_id=userID,job_name=str(ss1),job_type=jobType)
	fet_1 = run_fet(c,ss1,'')
	if len(fet_1)>0:
		Compare.objects.filter(id=c.id).update(job_status='View results',job_progress=100)
	else:
		Compare.objects.filter(id=c.id).update(job_status='No results',job_progress=100)

@task
def temmpo_task(c_id,intData):
	session = driver.session()
	compare = Compare.objects.get(pk=c_id)
	ss1=compare.job_name.split("_")[0]
	ss2=compare.job_name.split("_")[1]
	s = compare.job_desc.split(":")
	s1_name = s[0].strip()+"_"+compare.user_id
	s2_name = s[1].strip()+"_"+compare.user_id
	userID=compare.user_id
	logger.debug("Running temmpo task with "+ss1+" and "+ss2)
	#intData = int_file.read().replace("\n","','")[:-2]
	#logger.debug(intData)
	Compare.objects.filter(id=compare.id).update(job_status='Getting data',job_progress=10)
	#com = "match (s1:SearchSet)--(p1:Pubmed)--(m:Mesh) where s1.name = '"+s1_name+"' and m.mesh_name in ['"+intData+"] with s1,count(distinct(p1.pmid)) as c1,m match (s2:SearchSet)--(p2:Pubmed)--(m:Mesh) where s2.name = '"+s2_name+"' return c1,m.mesh_name as name,count(distinct(p2)) as c2 ;"
	com = "match (s:SearchSet)--(p:Pubmed)--(m:Mesh) where s.name = '"+s1_name+"' and m.mesh_name in ['"+intData+"] return s.name as ss,m.mesh_name as name,p.pmid as p "
	com+= "UNION match (s:SearchSet)--(p:Pubmed)--(m:Mesh) where s.name = '"+s2_name+"' and m.mesh_name in ['"+intData+"] return s.name as ss,m.mesh_name as name, p.pmid as p;"
	#logger.debug(com)
	oDic = defaultdict(dict)
	for res in session.run(com):
		ss = res['ss'].encode("ascii")
		mn = res['name']
		pm = res['p']
		if mn in oDic:
			if ss in oDic[mn]:
				a = oDic[mn][ss]
				if pm not in a:
					a.append(pm)
					oDic[mn][ss] = a
			else:
				oDic[mn][ss] = [pm]
		else:
			oDic[mn][ss] = [pm]
	#logger.debug(oDic)
	Compare.objects.filter(id=compare.id).update(job_status='Parsing data',job_progress=50)
	if len(oDic) > 0:
		oDicSum = defaultdict(dict)
		for i in oDic:
			j1 = []
			j2 = []
			if s1_name in oDic[i]:
				j1 = oDic[i][s1_name]
			if s2_name in oDic[i]:
				j2 = oDic[i][s2_name]
			ii = set(j1).intersection(j2)
			oDicSum[i][s1_name] = len(j1) - len(ii)
			oDicSum[i][s2_name] = len(j2) - len(ii)
			oDicSum[i][s1_name + ":" + s2_name] = len(ii)
		Compare.objects.filter(id=compare.id).update(job_status='Adding to db',job_progress=70)
		for mesh_name in oDic:
			if s1_name in oDicSum[mesh_name]:
				uniq_a = float(oDicSum[mesh_name][s1_name])
			if s2_name in oDicSum[mesh_name]:
				uniq_b = float(oDicSum[mesh_name][s2_name])

			# calculate temmpo style score
			# score1 = min(bf,df)/max(bf,df)*(bf+df)
			if (uniq_a and uniq_b) > 0.0:
				score = min(uniq_a, uniq_b) / max(uniq_a, uniq_b) * (uniq_a + uniq_b)
				score = ("%4.2f" % score)
			else:
				score = 0

			shared = s1_name + ":" + s2_name
			if shared in oDicSum[mesh_name]:
				shareScore = oDicSum[mesh_name][shared]
			else:
				shareScore = 0
			s = Overlap(name=mesh_name, mc_id=compare, mean_cp=0, mean_odds=0,uniq_a=uniq_a, uniq_b=uniq_b, shared=shareScore, score=score, treeLevel=0)
			s.save()

	Compare.objects.filter(id=compare.id).update(job_status='View results',job_progress=100)
	#context=''
	#return render_to_response('temmpo_res.html', context, context_instance=RequestContext(request))