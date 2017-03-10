import re

from django.core.management.base import BaseCommand, CommandError
from browser.models import Overlap, Compare


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
