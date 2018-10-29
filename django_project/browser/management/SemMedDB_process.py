import sys, gzip, os, time
import pandas as pd
from collections import defaultdict

#first transform sql to pipe separated
#for i in *sql.gz; do echo $i; python ~/scripts/bristol/mysql_to_csv.py <(gunzip -c $i) | gzip > ${i%%.*}.psv.gz; done

#python management/SemMedDB_process.py semmedVER25_PREDICATION_AGGREGATE_to06302015.psv.gz

c_file = 'semmedVER26_CITATIONS_R_to04302016.psv.gz'
s_file = 'semmedVER26_PREDICATION_AGGREGATE_R_to04302016.psv.gz'

#edits
# 25/07/16 - just for fun ver 26 added some dcom values with space delimiber, edited countPubs()

yRange = range(1950,2017)
print yRange

outDir="semmed_processed/"
if not os.path.exists(outDir):
	os.makedirs(outDir)

def countPubs():
	counter=0
	print "Reading citations file"
	start = time.time()
	pDic = {}
	with gzip.open(c_file, 'rb') as f:
		for line in f:
			counter += 1
			if counter % 1000000 == 0:
				print counter / 1000000,"million"
			# print line
			pmid = line.split('|')[0].replace("'", "")
			dcom = line.split('|')[3]
			# print "pmid:"+pmid
			pDic[pmid] = dcom
		# print pDic
	out = open(outDir+'pDic.txt', 'w')
	out.write(pDic)
	end = time.time()
	print "Time taken:", round(end - start, 3), "seconds"
	print "Reading in summary file"
	# df = pd.read_table(s_file, header=None,names=['PID','SID','PNUMBER','PMID','predicate','s_cui','s_name','s_type','s_novel','o_cui','o_name','o_type','o_novel'],sep='|')
	# print df.shape
	sDic = {}
	counter = 0
	start = time.time()
	with gzip.open(s_file, 'rb') as f:
		for line in f:
			counter += 1
			if counter % 1000000 == 0:
				print counter / 1000000,"million"
				end = time.time()
				print "Time taken:", round(end - start, 3), "seconds"
				start = time.time()
			# print line
			pid = line.split('|')[0]
			pmid = line.split('|')[3]
			#check if pubmed id is in citations file
			if pmid in pDic:
				dcom = pDic[pmid]
				if len(dcom.split(" ")) == 3:
					year = dcom.split(" ")[0].encode("ascii")
				else:
					year = dcom.split("-")[0].encode("ascii")
				# print "pmid:"+pmid
				if pid in sDic:
					a = sDic[pid]
					if year not in a:
						a[year] = 1
					else:
						a[year] += 1
					sDic[pid] = a
				else:
					sDic[pid] = {year: 1}
			else:
				print pmid, "not in citations file"
	out = open(outDir+'semmed_pubCounts.txt', 'w')
	for i in sDic:
		out.write(i + ":")
		for j in sDic[i]:
			out.write("\t" + j + "-" + str(sDic[i][j]))
		out.write("\n")

def makeFreqs():
	print "makeFreqs"
	f = outDir+'semmed_pubCounts.txt'
	counter=0
	start = time.time()
	yFreqAll = defaultdict(dict)
	with open(f, 'rb') as f:
		for line in f:
			# print line
			counter += 1
			line = line.rstrip('\n')
			pid = line.split(":")[0]
			# print 'pid = ',pid
			d = line.split(":")[1].split("\t")
			print d
			yFreq = {}
			for i in d:
				if len(i) > 0:
					y = i.split("-")[0]
					print "y: "+y
					f = i.split("-")[1]
					print "f: "+f
					try:
						int_y = int(y)
						if int_y in yRange:
							yFreq[int(y)] = int(f)
					except ValueError:
						print "Error", line, " contains a bad a year"
						pass
					# print yFreq
			fTotal = 0
			t = False
			for i in yRange:
				if i in yFreq:
					fTotal += yFreq[i]
				yFreqAll[pid][i] = fTotal
			if counter % 1000000 == 0:
				print counter/1000000,"million"
				end = time.time()
				print "Time taken:", round((end - start) / 60, 3), "minutes"
				start = time.time()
			# tx.append(statement)
	#print yFreqAll
	print len(yFreqAll)
	return yFreqAll

def createFiles(yFreqAll):
	#read in data
	print "Reading in",s_file
	df = pd.read_table(s_file, header=None,names=['PID','SID','PNUMBER','PMID','predicate','s_cui','s_name','s_type','s_novel','o_cui','o_name','o_type','o_novel'],sep='|')
	print df.shape

	#delete SID and PNUMBER columns
	df.drop(['SID','PNUMBER','PMID'],inplace=True,axis=1)
	print df.shape
	#print df.iloc[0:5,0:5]

	#remove duplicates
	df_unique = df.drop_duplicates()
	print df_unique.shape
	#df_unique['freq'] = df_unique['PID'].map(fCounts)
	#df_unique['freq']=fCounts.values()
	print df_unique.iloc[0:5,:]
	print df_unique.shape

	#get freq counts
	fCounts = df_unique['PID'].value_counts(sort=False).to_dict()
	sCounts = df_unique['s_name'].value_counts(sort=False).to_dict()
	oCounts = df_unique['o_name'].value_counts(sort=False).to_dict()
	sTypeCounts = df_unique['s_type'].value_counts(sort=False).to_dict()
	oTypeCounts = df_unique['o_type'].value_counts(sort=False).to_dict()

	print len(fCounts)
	#print fCounts.values()

	def addFreqs(x,year):
		#print x,year
		#check for occasions where citation in predicates but not in citations!!
		if year not in yFreqAll[str(x)]:
			print str(x),yFreqAll[str(x)],year,' has no data'
			return 0
		else:
			return yFreqAll[str(x)][year]
	for i in yRange:
		df_unique['freq_'+str(i)]=df_unique['PID'].apply(addFreqs,args=(i,))
		print i,df_unique.shape

	#add frequencies to semmed triple data!!!
	df_unique['s_freq'] = df_unique['s_name'].map(sCounts)
	df_unique['o_freq'] = df_unique['o_name'].map(oCounts)

	df_unique.to_csv(outDir+'semmed_triple.txt.gz',compression='gzip',sep='|',header=False)
	h=open(outDir+"semmed_triple_headers.psv",'w')
	fString = ''
	for i in yRange:
		fString += '|freq_'+str(i)+':double'
	h.write(':IGNORE|pid:ID(SDB_triple)|predicate|s_cui|s_name|s_type|s_novel:double|o_cui|o_name|o_type|o_novel:double'+fString+"|s_freq|o_freq")

	#drop freq columns
	for i in yRange:
		df_unique = df_unique.drop('freq_'+str(i),axis=1)


	##########################
	#create subject data
	print "Creating subject data.."
	df_sub = df_unique
	print df_sub.shape
	df_sub = df_sub.drop(['PID','predicate','o_name','o_type','o_novel','o_cui','o_freq'],axis=1)
	print df_sub.shape
	df_sub = df_sub.drop_duplicates()
	print df_sub.shape
	df_sub['s_freq'] = df_sub['s_name'].map(sCounts)
	print df_sub.shape
	#df_sub['st_freq'] = df_sub['s_name'].map(sTypeCounts)
	#print df_sub.shape
	df_sub.to_csv(outDir+'semmed_subject_data.txt.gz',compression='gzip',sep='|',header=False)
	
	#create object data
	print "Creating object data.."
	df_obj = df_unique
	print df_obj.shape
	df_obj = df_obj.drop(['PID', 'predicate', 's_name', 's_type', 's_novel','s_cui','s_freq'], axis=1)
	print df_obj.shape
	df_obj = df_obj.drop_duplicates()
	print df_obj.shape
	df_obj['o_freq'] = df_obj['o_name'].map(oCounts)
	print df_obj.shape
	#df_obj['ot_freq'] = df_obj['o_name'].map(oTypeCounts)
	#print df_obj.shape
	df_obj.to_csv(outDir+'semmed_object_data.txt.gz', compression='gzip', sep='|', header=False)
	
	#merge subject and object data
	print "Merging data..."
	df_sub = df_sub.set_index(df_sub['s_name'])
	df_obj = df_obj.set_index(df_obj['o_name'])
	#df_all = pd.merge(df_sub,df_obj, how='outer',left_on='s_name',right_on='o_name')
	df_all = df_sub.join(df_obj, how='outer')
	print df_all.shape
	#replace empty types
	df_all['s_type'] = df_all['s_type'].fillna(df_all['o_type'])
	df_all['o_type'] = df_all['o_type'].fillna(df_all['s_type'])
	df_all = df_all.drop(['s_name','o_name','o_type'],axis=1)
	df_all.rename(columns={'s_type':'type'},inplace=True)
	#remove NaNs from freq columns
	df_all.iloc[:,1:5] = df_all.iloc[:,1:5].fillna(0)
	#add freq column
	df_all['i_freq']=df_all['s_freq']+df_all['o_freq']
	print df_all.iloc[0:50,:]
	print df_all.shape	
	
	df_all.to_csv(outDir+'semmed_merged_data.txt.gz',compression='gzip',sep='|',header=False)
	h=open(outDir+"semmed_item_headers.psv",'w')
	h.write('name:ID(SDB_item)|type|s_novel|s_freq|o_novel|o_freq|i_freq')

if __name__ == '__main__':
	if os.path.isfile(outDir+'semmed_pubCounts.txt'):\
		print "Already generated pub counts"
	else:
		countPubs()
	yFreqAll = makeFreqs()
	createFiles(yFreqAll)
	# s_file=sys.argv[1]
	# fDict = {}
	# #create freq hash
	# with gzip.open(s_file,'rb') as f:
	# 	for line in f:
	# 		s=line.split("|")[0]
	# 		if s in fDict:
	# 			fDict[s] += 1
	# 		else:
	# 			fDict[s] = 1
	# print len(fDict)



