import sys,os,re
#import MySQLdb
import config

from neo4j.v1 import GraphDatabase,basic_auth
auth_token = basic_auth(config.user, config.password)
driver = GraphDatabase.driver("bolt://"+config.server+":"+config.port,auth=auth_token)

session = driver.session()

cmd="match (st:SDB_triple)--(p:Pubmed) where (st.s_name = 'Interleukin-1 beta|IL1B' or st.s_name = 'IL1B gene|IL1B' or st.s_name = 'IL1B') and st.o_type = 'dsyn' return st.s_name, st.predicate, st.o_name,count(p);"
result = session.run(cmd)

f = open('query_results.tsv', 'w')
#f.write('user_id,search_name,pmid\n')
for r in result:
	#f.write(userDic[r['u']]+','+r['s']+','+r['p']+'\n')
	f.write(r[0]+'\t'+r[1]+'\t'+r[2]+'\t'+str(r[3])+'\n')

session.close()
