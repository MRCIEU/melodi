import logging,time,os,subprocess,gzip

from neo4j.v1 import GraphDatabase,basic_auth
auth_token = basic_auth(config.user, config.password)
driver = GraphDatabase.driver("bolt://"+config.server,auth=auth_token)

logger = logging.getLogger(__name__)

# use this script to upload a large set of medline data, e.g. all of 2016 up to today's data
# ("2016/01/01"[Date - Completion] : "3000"[Date - Completion])

f='abstracts/pubmed_01_01_2016__27_06_2016.txt.melodi.gz'

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


def run(file_name):
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
		print "Number of pubmed articles = "+str(pCount)
	except subprocess.CalledProcessError as grepexc:
		logger.debug("error for pmid count", grepexc.returncode, grepexc.output)
		exit()
	logger.debug(cmd)
	#os.system(grep -c '^PMID')
	#SearchSet.objects.filter(job_name=sp[0],user_id=sp[1]).update(job_status='Adding pubmed data',job_progress=1)
	print "Adding data for ", file_name
	start = time.time()

	tx = session.begin_transaction()

	statement1 = "MATCH (a:Pubmed),(b:Mesh) where a.pmid = {pmid} and b.mesh_name={mesh_name} MERGE (a)-[r:HAS_MESH {mesh_type:'main'}]->(b)"

	counter_skip = 1
	counter_add_pm = 1
	counter_add_sp = 1
	#check for file compression again
	infile = compressCheck(file_name)
	pmid = ""
	pub_new = True
	count_line = 0
	tCheck = time.time()
	for line in infile:
		count_line += 1
		if counter_add_sp % 1000 == 0:
			#add to db
			pc = round((float(counter_add_sp)/float(pCount))*100)
			#print pc
		line = line.strip("\r\n")
		# print "line = "+line
		if len(line) == 0:
			nothing = 0
		elif line[0:4] == "PMID":
			pub_new = True
			pmid = line.split("-", 1)[1].strip()
			# print "search_name=",sp[1],"pmid = ",pmid
			counter_add_sp += 1
			if counter_add_sp % 10000 == 0:
				print "Total minutes: ",round((time.time() - start) / 60, 3)
				print "sp = ", counter_add_sp, "pm = ", counter_add_pm, "pc = ",pc
				tx.commit()
				tx.success = True
				session.close()
				session = GraphDatabase.driver("bolt://10.0.2.2",auth=auth_token).session()
				#tx.success();
				tx = session.begin_transaction()
				print "Step time: "+str(round(time.time() - tCheck, 3))+" seconds"
				tCheck = time.time()
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
							tx.run(statement1, {"mesh_name": m_new, "pmid": pmid})
						#else:
						#	tx.run(statement1, {"mesh_name": m_new, "pmid": pmid, "mesh_type": "not_main"})
				else:
					if '*' in m:
						m = m.replace("*", "")
						tx.run(statement1, {"mesh_name": m, "pmid": pmid})
					#else:
					#	tx.run(statement1, {"mesh_name": m, "pmid": pmid, "mesh_type": "not_main"})
	infile.close()
	# catch the last ones
	tx.commit()
	end = time.time()
	print "Added "+str(counter_add_sp - 1)+" new search set - pubmed relationships"
	print "Added "+str(counter_add_pm - 1)+" new pubmed - mesh relationships"
	print "Total time taken: "+str(round(end - start, 3))+" seconds"
	session.close()

run(f)