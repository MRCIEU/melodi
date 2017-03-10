import sys, gzip, os, time

# first convert MRCOC file to redued format
# wget https://mbr.nlm.nih.gov/MRCOC/detailed_CoOccurs_2016.txt.gz
# gunzip -c detailed_CoOccurs_2016.txt.gz | awk -F '|' '$10==1' | cut -d "|" -f 1,9,14 | grep '|1:' | sort | uniq | gzip > detailed_CoOccurs_2016_uniq_main.txt.gz

# 1000000|D004259|1:ME:Q000378|D004717|1:EN:Q000201
# 1000000|D004259|1:ME:Q000378|D011270|
# 1000000|D004259|1:ME:Q000378|D012316|1:ME:Q000378
# 1000000|D004259|1:ME:Q000378|D012324|1:ME:Q000378
# 1000000|D004259|1:ME:Q000378|D047108|
# 1000000|D004717|1:EN:Q000201|D011270|
# 1000000|D004717|1:EN:Q000201|D012316|1:ME:Q000378
# 1000000|D004717|1:EN:Q000201|D012324|1:ME:Q000378
# 1000000|D011270||D012316|1:ME:Q000378
# 1000000|D011270||D012324|1:ME:Q000378
# 1000000|D012316|1:ME:Q000378|D012324|1:ME:Q000378
# 1000000|D047108||D004717|1:EN:Q000201
# 1000000|D047108||D011270|
# 1000009|D012739|0:ME:Q000378,1:PD:Q000494|D013094|0:DE:Q000187,1:ME:Q000378

# 127809617 entries

cfile='detailed_CoOccurs_2016_uniq_zy.txt.gz'
ofile='detailed_CoOccurs_2016_uniq_zy.neo4j.txt'
def create_neo4j_data(cfile,ofile):
	counter=0
	mData=set()
	pCheck=''
	meshType='main'
	#remove old output file just in case
	os.system('rm '+ofile+'.gz')
	with gzip.open(cfile, 'rb') as fi:
		for line in fi:
			#print 'line: '+line
			counter += 1
			if counter % 1000000 == 0:
				print counter / 1000000,"million"
			s = line.split('|')
			pmid=s[0]
			m1=s[1]
			q1=s[2]
			m2=s[3]
			q2=s[4]
			#print 'q1:',len(q1)
			#print 'q2:',len(q2)

			if pmid != pCheck and pCheck != '':
				#print len(mData)
				with open(ofile, 'a') as fo:
					for i in mData:
						fo.write(i+"\n")
				mData = set()


			if len(q1)>1:
				for i in q1.split(','):
					a=i.split(':')
					#check for main
					if a[0]=='1':
						mData.add(pmid+'|'+m1+'/'+a[2].rstrip()+'|'+meshType)
			else:
				mData.add(pmid+'|'+m1.rstrip()+'|'+meshType)
			if len(q2)>1:
				for i in q2.split(','):
					a=i.split(':')
					if a[0]=='1':
						mData.add(pmid+'|'+m2+'/'+a[2].rstrip()+'|'+meshType)
			else:
				mData.add(pmid+'|'+m2.rstrip()+'|'+meshType)

			pCheck = pmid
	os.system("gzip "+ofile)


create_neo4j_data(cfile,ofile)