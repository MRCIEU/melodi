import sys,os,re,subprocess
# import MySQLdb
#
# #get user info from mysql
# mcnf = open('mysql.cnf','r')
# for line in mcnf:
# 	s = re.search('database = (.+?)$', line)
# 	if s:
# 		dbName = s.group(1)
# 	s = re.search('user = (.+?)$', line)
# 	if s:
# 		user = s.group(1)
# 	s = re.search('password = (.+?)$', line)
# 	if s:
# 		pwd = s.group(1)
# 	s = re.search('host = (.+?)$', line)
# 	if s:
# 		host = s.group(1)
#
# db = MySQLdb.connect(host,user,pwd,dbName)
# cursor = db.cursor()
# cursor.execute("SELECT user_id,uid from social_auth_usersocialauth")
# data = cursor.fetchall()
# userDic = {}
# for row in data:
# 	userDic[str(row[1])]=row[0]
#
# print userDic

#add the exported user info file to the neo4j import directory then add the data to the graph
cmd = 'USING PERIODIC COMMIT 10000 load csv with headers from "file:///user_info.csv" as line FIELDTERMINATOR \'|\' MERGE (s:SearchSet {search_name:line.name}) MERGE (p:Pubmed {pmid:toInt(line.pmid)}) MERGE (s)-[:INCLUDES]->(p);'
print cmd

subprocess.call('neo4j-shell -c '+cmd)