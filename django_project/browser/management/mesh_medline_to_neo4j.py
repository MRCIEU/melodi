import logging,time,os,subprocess,gzip,re

#f='abstracts/test_update.txt'
f='pubmed_01_01_2016__03_08_2016.txt.gz'

from neo4j.v1 import GraphDatabase,basic_auth
auth_token = basic_auth(config.user, config.password)
driver = GraphDatabase.driver("bolt://"+config.server,auth=auth_token)
#driver = GraphDatabase.driver("bolt://IT017354.users.bris.ac.uk",auth=auth_token)

logger = logging.getLogger(__name__)

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

def getMeshData():
	session = driver.session()
	result = session.run("match (m:Mesh) return m.mesh_name as mesh_name, m.mesh_id as mesh_id")
	meshDic = {}
	for record in result:
		meshDic[record["mesh_name"]] = record["mesh_id"]
	return meshDic

def run(file_name):
	#count number of pubmed entries in file
	if file_name.endswith('.gz') or file_name.endswith('.gunzip'):
		cmd = "gunzip -c "+file_name+" | grep -c '^PMID' "
		print "Reading gzip file"
	elif file_name.endswith('.zip'):
		cmd = "unzip -c "+file_name+" | grep -c '^PMID' "
		print "Reading zip file"
	else:
		cmd = "grep -c '^PMID' "+file_name
		print "Reading uncompressed file"

	try:
		print "Counting articles..."
		pCount = int(subprocess.check_output(cmd, shell=True))
		print "Number of pubmed articles = "+str(pCount)
	except subprocess.CalledProcessError as grepexc:
		print "error for pmid count", grepexc.returncode, grepexc.output
		exit()
	#print cmd

	#open output file
	ofile = '/tmp/mesh_2016.txt'
	pfile = '/tmp/pubmed_2016.txt'
	o = open(ofile, 'w')
	p = open(pfile, 'w')

	#get mesh id data
	print "Getting mesh ID data..."
	meshDic = getMeshData()

	print "Reading data: ", file_name
	start = time.time()

	counter_pm = 1
	#check for file compression again
	infile = compressCheck(file_name)
	pmid = ""
	pub_new = True
	count_line = 0
	tCheck = time.time()
	issn=title=dcom=jt=da=dp=""
	for line in infile:
		count_line += 1
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
				issn = line.split("-", 1)[1].split(" ")[1].strip()
		elif line[0:2] == 'DP':
			dp = line.split("-", 1)[1].strip()
		elif line[0:2] == 'DA':
			da = line.split("-", 1)[1].strip()
			da = da[0:4]+"-"+da[4:6]+"-"+da[6:8]
		elif line[0:4] == 'DCOM':
			dcom = line.split("-", 1)[1].strip()
			dcom = dcom[0:4]+"-"+dcom[4:6]+"-"+dcom[6:8]
		elif line[0:4] == "PMID":
			pub_new = True
			pmid = line.split("-", 1)[1].strip()
			#p.write(pmid+"|"+issn+"|"+title+"|"+dcom+"|"+jt+"\n")
			p.write(pmid+"|"+issn+"|"+dcom+"|"+dp+"|"+da+"\n")
			issn=title=dcom=jt=da=dp=""
			# print "search_name=",sp[1],"pmid = ",pmid
			counter_pm += 1
			if counter_pm % 10000 == 0:
				pc = round((float(counter_pm)/float(pCount))*100)
				#print "Total minutes: ",round((time.time() - start) / 60, 3)
				print "pm = ", counter_pm, "pc = ",pc
				print "Step time: "+str(round(time.time() - tCheck, 3))+" seconds"
				tCheck = time.time()
		if pub_new == True:
			if line[0:3] == "MH ":
				m = line.split("-", 1)[1].strip()
				# print 'mesh name  = ',m
				# split when multiple forward slashes as mesh terms are collapsed by DO ID
				if m.count("/") > 1:
					ms = m.split("/")
					for e in range(1, len(ms)):
						m_new = ms[0] + "/" + ms[e]
						if '*' in m_new:
							m_new = m_new.replace("*", "")
							if m_new in meshDic:
								o.write(pmid+"|"+meshDic[m_new]+"|main\n")
				else:
					if '*' in m:
						m = m.replace("*", "")
						if m in meshDic:
							o.write(pmid+"|"+meshDic[m]+"|main\n")
					#else:
					#	tx.run(statement1, {"mesh_name": m, "pmid": pmid, "mesh_type": "not_main"})
	infile.close()
	os.system("gzip "+ofile)
	os.system("gzip "+pfile)
run(f)