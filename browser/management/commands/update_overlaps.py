import re,os
import config
import gzip
import time

from django.core.management.base import BaseCommand, CommandError
from browser.models import Overlap, Compare
from django.core.paginator import Paginator

from neo4j.v1 import GraphDatabase,basic_auth
auth_token = basic_auth(config.user, config.password)
driver = GraphDatabase.driver("bolt://"+config.server+":"+config.port,auth=auth_token)

def chunked_iterator(queryset, chunk_size=100000):
    paginator = Paginator(queryset, chunk_size)
    for page in range(1, paginator.num_pages + 1):
        for obj in paginator.page(page).object_list:
            yield obj

class Command(BaseCommand):
	def add_arguments(self, parser):
		parser.add_argument('type', type=str)

	def handle(self, *args, **options):
		type = options['type']
		print "type = "+type
		if type == 'names':
			print "Updating names"
			for o in Overlap.objects.all().iterator():
				if o.mc_id.job_type == 'semmed' or o.mc_id.job_type == 'semmed_t':
					if o.name1 == '':
						print o.id,o.name,o.name1
						nSplit = o.name.split('||')
						if len(nSplit) == 7:
							n1,n2,n3,nid,n4,n5,sid = o.name.split('||')
							Overlap.objects.filter(id=o.id).update(name1=n1,name2=n2,name3=n3,name4=n4,name5=n5)
							print n1,n2,n3,n4,n5

		elif type == 's_types':
			print "Getting semmed types.."
			sConcepts = {}
			semFile = 'data/semTypes.txt.gz'
			if os.path.exists(semFile):
				print 'Reading from file'
				f = gzip.open(semFile,'r')
				for line in f:
					l = line.split('\t')
					sConcepts[l[0]]=l[1].rstrip()
			else:
				print 'Getting data from graph...'
				sOut = gzip.open(semFile,'w')
				session = driver.session()
				counter=0

				com = "match (s:SDB_item) return s.name,s.type";
				for res in session.run(com):
					sOut.write(res['s.name']+'\t'+res['s.type']+'\n')
					sConcepts[res['s.name']] = res['s.type']
					if counter % 10000 == 0:
						print counter
					counter+=1
				sOut.close()

			print len(sConcepts)
			print "Updating names with semmed types"
			counter=0
			for o in chunked_iterator(Overlap.objects.all()):
				if counter % 10000 == 0:
					t = time.asctime( time.localtime(time.time()) )
					print t,o.id,counter
				counter+=1
			#for o in Overlap.objects.all().iterator():
				#fibrillin||ASSOCIATED_WITH||Marfan Syndrome||4965773:Marfan Syndrome||PROCESS_OF||Sister||83749
				if o.mc_id.job_type == 'semmed_t' or o.mc_id.job_type == 'semmed':
					oSplit = o.name.split('||')
					if len(oSplit)==7:
						#print o.id
						s1,s2,s3,s4,s5,s6,s7 = o.name.split('||')
						s_type1 = s_type3 = s_type4 = s_type6 = 'n/a'
						if s1 in sConcepts:
							s_type1 = sConcepts[s1]
						if s3 in sConcepts:
							s_type3 = sConcepts[s3]
						if s4 in sConcepts:
							s_type4 = sConcepts[s4.split(':')[1]]
						if s6 in sConcepts:
							s_type6 = sConcepts[s6]
						if s1 in sConcepts or s3 in sConcepts or s6 in sConcepts:
							newName = s1+' ('+s_type1+')||'+s2+'||'+s3+' ('+s_type3+')||'\
								  +s4+' ('+s_type4+')||'+s5+'||'+s6+' ('+s_type6+')||'+s7
							#print newName
							Overlap.objects.filter(id=o.id).update(name=newName)
							Overlap.objects.filter(id=o.id).update(
								name1=o.name1+' ('+s_type1+')',
								name3=o.name3+' ('+s_type3+')',
								name5=o.name5+' ('+s_type6+')',)
					else:
						print len(oSplit),o.name

				elif o.mc_id.job_type == 'semmed_c':
					name = o.name.split(':')[0]
					s_type = 'n/a'
					if name in sConcepts:
						s_type = sConcepts[name]
					newName = name+' ('+s_type+'):0'
					print newName
					Overlap.objects.filter(id=o.id).update(name=newName)