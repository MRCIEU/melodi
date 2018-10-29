import sys,os,re
import MySQLdb
import config
from neo4j.v1 import GraphDatabase,basic_auth

auth_token = basic_auth(config.user, config.password)
driver = GraphDatabase.driver("bolt://"+config.server,auth=auth_token)

session = driver.session()

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
# 	userDic[str(row[0])]=row[1]
#
# print userDic

cmd="MATCH (s:SearchSet) RETURN distinct(s.name) as s;"
result = session.run(cmd)

f = open('/tmp/user_nodes.csv', 'w')
#f.write('user_id,search_name,pmid\n')
for r in result:
	#f.write(userDic[r['u']]+','+r['s']+','+r['p']+'\n')
	f.write(r['s']+'|\n')

cmd="MATCH (s:SearchSet)--(p:Pubmed) RETURN s.name as s ,p.pmid as p;"
result = session.run(cmd)

f = open('/tmp/user_info.csv', 'w')
#f.write('user_id,search_name,pmid\n')
for r in result:
	#f.write(userDic[r['u']]+','+r['s']+','+r['p']+'\n')
	f.write(r['s']+'|'+str(r['p'])+'\n')
session.close()
