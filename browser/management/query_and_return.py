import sys,os,re
#import MySQLdb
import config

from neo4j.v1 import GraphDatabase,basic_auth
auth_token = basic_auth(config.user, config.password)
driver = GraphDatabase.driver("bolt://"+config.server+":"+config.port,auth=auth_token)

session = driver.session()

cmd="match (st:SDB_triple)--(p:Pubmed) where (st.s_name = 'Interleukin-1 beta|IL1B' or st.s_name = 'IL1B gene|IL1B' or st.s_name = 'IL1B') and st.o_type = 'dsyn' "\
	"with st, p match (st2:SDB_triple) where st2.o_name = st.o_name "\
	"return st.s_name, st.predicate, st.o_name,count(distinct(p)), count(distinct(st2)), "\
	"(count(distinct(p))* 1.0)/count(distinct(st2)) as score order by score desc;"
print cmd
result = session.run(cmd)

f = open('query_results.tsv', 'w')
f.write('object\tpredicate\tsubject\t#object\t#subject\tfreq\n')
#f.write('user_id,search_name,pmid\n')
for r in result:
	#f.write(userDic[r['u']]+','+r['s']+','+r['p']+'\n')
	f.write(r[0]+'\t'+r[1]+'\t'+r[2]+'\t'+str(r[3])+'\t'+str(r[4])+'\t'+str(r[5])+'\n')

session.close()
