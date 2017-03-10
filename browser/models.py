import uuid
from django.db import models

class SearchSet(models.Model):
	user_id = models.CharField(max_length=200)
	job_name = models.CharField(max_length=200)
	job_id = models.CharField(max_length=200)
	job_start = models.CharField(max_length=30)
	job_status = models.CharField(max_length=20)
	job_progress = models.IntegerField()
	ss_file = models.FileField(upload_to='/var/django/melodi/abstracts')
	ss_desc = models.CharField(max_length=5000)
	pTotal = models.IntegerField()

	class Meta:
		unique_together = ('user_id', 'job_name',),

	#def __str__(self):
	#	return "User: " + self.user_id

class SearchSetAnalysis(models.Model):
	ss_id = models.ForeignKey(SearchSet)
	job_type =  models.CharField(max_length=20)
	complete = models.BooleanField(default=False)
	year_range = models.CharField(max_length=12)

class Compare(models.Model):
	user_id = models.CharField(max_length=200)
	job_name = models.CharField(max_length=200)
	job_desc = models.CharField(max_length=400)
	job_start = models.CharField(max_length=30)
	job_status = models.CharField(max_length=20)
	job_progress = models.IntegerField()
	job_type = models.CharField(max_length=20)
	year_range = models.CharField(max_length=12)
	share = models.BooleanField(default=False)
	hash_id = models.UUIDField(default=uuid.uuid4, editable=False)

#class Fet(models.Model):
#	ssa_id = models.ForeignKey(SearchSetAnalysis)
#	odds = models.FloatField()
#	pval = models.FloatField()
#	cpval = models.FloatField()

class Overlap(models.Model):
	mc_id = models.ForeignKey(Compare)
	name = models.CharField(max_length=500,blank=True,db_index=True)
	name1 = models.CharField(max_length=200,blank=True,db_index=True)
	name2 = models.CharField(max_length=50,blank=True,db_index=True)
	name3 = models.CharField(max_length=200,blank=True,db_index=True)
	name4 = models.CharField(max_length=50,blank=True,db_index=True)
	name5 = models.CharField(max_length=200,blank=True,db_index=True)
	mean_cp = models.FloatField()
	mean_odds = models.FloatField()
	uniq_a = models.IntegerField()
	uniq_b = models.IntegerField()
	shared = models.IntegerField()
	score = models.FloatField()
	treeLevel = models.FloatField()

	class Meta:
		unique_together = ('name', 'mc_id',)

class Filters(models.Model):
	com = models.ForeignKey(Compare)
	version = models.IntegerField()
	type = models.CharField(max_length=20)
	num = models.IntegerField()
	value = models.CharField(max_length=200)
	location = models.IntegerField()
	ftype = models.CharField(max_length=3)

class Sliders(models.Model):
	com = models.ForeignKey(Compare)
	version = models.IntegerField()
	type = models.CharField(max_length=20)
	pval = models.FloatField(blank=True)
	odds = models.FloatField(blank=True)
	level = models.IntegerField(blank=True)
	top = models.IntegerField(blank=True)

