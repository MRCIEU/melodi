import sys,os,re
import MySQLdb
import config
import argparse
from neo4j.v1 import GraphDatabase,basic_auth

#takes arguement of user id and article set name

#neo4j
auth_token = basic_auth(config.user, config.password)
driver = GraphDatabase.driver("bolt://"+config.server+":"+config.port,auth=auth_token)
session = driver.session()

#arguments
parser = argparse.ArgumentParser()
parser.parse_args()


cmd="match (s:SearchSet) where s.name = 'firework_trauma2_10' return s;"
result = session.run(cmd)
print result

#f = open('/tmp/user_info.csv', 'w')
#f.write('user_id,search_name,pmid\n')
#for r in result:
	#f.write(userDic[r['u']]+','+r['s']+','+r['p']+'\n')
#	f.write(r['s']+'|'+str(r['p'])+'\n')
session.close()
