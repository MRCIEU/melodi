import re
import config

from django.core.management.base import BaseCommand, CommandError
from browser.models import Overlap, Compare

from neo4j.v1 import GraphDatabase,basic_auth
auth_token = basic_auth(config.user, config.password)
driver = GraphDatabase.driver("bolt://"+config.server+":"+config.port,auth=auth_token)


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
			session = driver.session()
			counter=0
			print "Getting semmed types.."
			sConcepts = {}
			com = "match (s:SDB_item) return s.name,s.type";
			for res in session.run(com):
				sConcepts[res['s.name']] = res['s.type']
				if counter % 10000 == 0:
					print counter
				counter+=1
			print len(sConcepts)

			print "Updating names with semmed types"
			for o in Overlap.objects.all().iterator():
				#fibrillin||ASSOCIATED_WITH||Marfan Syndrome||4965773:Marfan Syndrome||PROCESS_OF||Sister||83749
				if o.mc_id.job_type == 'semmed_t':
					s1,s2,s3,s4,s5,s6,s7 = o.name.split('||')
					if s1 in sConcepts:
						newName = s1+' ('+sConcepts[s1]+')||'+s2+'||'+s3+' ('+sConcepts[s3]+')||'\
							  +s4+' ('+sConcepts[s4.split(':')[1]]+')||'+s5+'||'+s6+' ('+sConcepts[s6]+')||'+s7
						print newName
						Overlap.objects.filter(id=o.id).update(name=newName)

						Overlap.objects.filter(id=o.id).update(
							name1=o.name1+' ('+sConcepts[o.name1.split(':')[0]]+'):0',
							name3=o.name3+' ('+sConcepts[o.name3.split(':')[0]]+'):0',
							name5=o.name5+' ('+sConcepts[o.name5.split(':')[0]]+'):0',)

				elif o.mc_id.job_type == 'semmed_c':
					name = o.name.split(':')[0]
					if name in sConcepts:
						newName = name+' ('+sConcepts[name]+'):0'
						print newName
						Overlap.objects.filter(id=o.id).update(name=newName)