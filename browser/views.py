import sys
import gzip
import time
import numpy
import json
import time
import logging
import operator
import config
import csv
import StringIO
import subprocess
import HTMLParser

#from py2neo import Graph, Path, Node, Relationship,authenticate
from scipy import stats

from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404, render
from browser.forms import (CreateSemSet,ComSearchSets,CreateSearchSet,CreatePubSet)
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
#from browser.medline_parser import *
from browser.tasks import *
from browser.models import SearchSet,Compare,Overlap,Filters
from django.template.defaulttags import register
#from django.template.context_processors import csrf
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist
from math import exp
from django_datatables_view.base_datatable_view import BaseDatatableView
from collections import defaultdict
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.core.serializers.json import DjangoJSONEncoder
from django.core import serializers
from sets import Set
from settings import DATA_FOLDER

#neo4j
from neo4j.v1 import GraphDatabase,basic_auth
auth_token = basic_auth(config.user, config.password)
driver = GraphDatabase.driver("bolt://"+config.server+":"+config.port,auth=auth_token)

#===============GoogleAuth Start
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.views.generic.base import View
from social_auth.backends import AuthFailed
from social_auth.views import complete
from django.contrib.auth.decorators import login_required
from django.conf import settings

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)
#logging.basicConfig(filename='run.log',level=logging.DEBUG)


class AuthComplete(View):
    def get(self, request, *args, **kwargs):
		logging.warning('error')
		backend = kwargs.pop('backend')
		try:
			return complete(request, backend, *args, **kwargs)
		except AuthFailed:
			logging.warning('error')
			messages.error(request, "Your Google Apps domain isn't authorized for this app")
			return HttpResponseRedirect(reverse('gauth_login'))

class LoginError(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(status=401)

#===============GoogleAuth End

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
@register.filter
def mysplit(value, sep = "."):
    parts = value.split(sep)
    return (parts)

tmpDir=settings.MEDIA_ROOT

def people(request):
	#example query
	sem="match (s:SearchSet)--(p:Pubmed)--(st:SDB_triple)--(si:SDB_item) where s.name = 'tom gaunt_2' return count(distinct(p)) as c,si order by c;"
	mesh="match (s:SearchSet)--(p:Pubmed)--(m:Mesh) where s.name = 'tom gaunt_2' return count(distinct(p)) as c,m order by c;"


def ajax_graph_metrics(request):
	session = driver.session()
	logger.debug('getting graph metrics')
	uAll=SearchSet.objects.order_by().values_list('user_id',flat=True).exclude(user_id='2').distinct().count()
	if request.is_ajax():
		# get data for graph
		# only want search sets that I (user 2) haven't created
		#gCom = "match (s:SearchSet) where not s.name =~ '.*_2' return count(s) as s union match (s:Pubmed) return count(s) as s union match (s:Mesh) return count(s) as s union match (s:SDB_triple) return count(s) as s union match (s:SDB_item) return count(s) as s;"
		gCom = "match (s:Pubmed) return count(s) as s union match (s:Mesh) return count(s) as s union match (s:SDB_triple) return count(s) as s union match (s:SDB_item) return count(s) as s;"
		logger.debug(gCom)
		#data = [int(uAll)]
		data = []
		for res in session.run(gCom):
			data.append(res[0])
		metrics = data
		logger.debug(data)

		# get user and article set over time
		# select user_id,job_start from browser_searchset where user_id != 2 and job_status = 'Complete';
		logger.debug("getting time data...")
		s = SearchSet.objects.filter(job_status='Complete').exclude(user_id='2')
		tData = []
		aDic = {}
		for i in s:
			u = i.user_id
			t = i.job_start.split(" ")[0].split("-")[0:2]
			t = "-".join(t)
			if t in aDic:
				aDic[t].append(u)
			else:
				aDic[t] = [u]

		c = Compare.objects.filter(job_status='View results').exclude(user_id='2')
		cDic = {}
		for i in c:
			#id = i.id
			id = i.job_name
			t = i.job_start.split(" ")[0].split("-")[0:2]
			t = "-".join(t)
			if t in cDic:
				cDic[t].append(id)
			else:
				cDic[t] = [id]

		cats = []
		uCounts = []
		aCounts = []
		cCounts = []
		cCountOld = []
		oldCount = []
		for a in sorted(aDic):
			cats.append(a)
			#logger.debug(a)
			if a in aDic:
				uCount = len(list(set(aDic[a] + oldCount)))
				uCounts.append(uCount)

				aCount = len(aDic[a] + oldCount)
				aCounts.append(aCount)
				oldCount = aDic[a] + oldCount
			else:
				uCounts.append(0)
				aCounts.append(0)
			if a in cDic:
				cCount = len(list(set(cDic[a] + cCountOld)))
				cCounts.append(cCount)
				cCountOld = cDic[a] + cCountOld
			else:
				cCounts.append(0)

	else:
		data = 'fail'
		logger.debug('not ajax request')
	mimetype = 'application/json'
	session.close()
	return HttpResponse(json.dumps({'metrics':metrics,'uCounts':uCounts,'aCounts':aCounts,'cCounts':cCounts,'cats':cats}), mimetype)


def ajax_test(request):
	object = ''
	f = tmpDir+'/new.txt'
	logger.debug('looking for file ',f)
	if os.path.isfile(f):
		object = "file exists"
		logger.debug('object exists')
	return HttpResponse(object)

def issn_to_name(iList):
	logger.debug('Running issn_to_name'+str(iList))
	#check for null entries
	if 'null' in iList:
		iList.remove('null')
	iString = ",".join(iList)
	start=time.time()
	print "\n### Getting ids ###"
	url="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
	#params = {'term': '0140-6736+OR+0022-2275'}
	params = {'term': iString}

	r = requests.post(url)

	# GET with params in URL
	r = requests.get(url, params=params)

	#create random file name
	n = 10
	ran=''.join(["%s" % randint(0, 9) for num in range(0, n)])
	rSplit = r.text.split("<")

	iDic = {}
	iName = []
	for i in rSplit:
		l = re.match(r'To>(.*?)$', i)
		if l:
			m = l.group(1).replace('[Journal]','').replace('"','').strip().encode("ascii")
			iName.append(m)

	for i in range(0,len(iList)):
		iDic[iList[i]]=iName[i]
	logger.debug(iDic)
	return iDic

def pubmed_id_details(pList):
	logger.debub('Getting pubmed info')

def pmid_to_info(pList):
	#logger.debug('Running pmid_to_info'+str(pList))
	iString = ",".join(pList)
	start=time.time()
	print "\n### Getting ids ###"
	url="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?"
	#params = {'term': '0140-6736+OR+0022-2275'}
	params = {'db':'pubmed','id': iString}

	# GET with params in URL
	r = requests.get(url, params=params)

	#print r.text
	rSplit = r.text.split("<")

	ptDic = {}
	pjDic = {}
	t = jt = 'n/a'
	for i in rSplit:
		#print "i",i
		#check pubmed id
		pmid_match = re.match(r'Item Name="pubmed" Type="String">(.*?)$', i)
		if pmid_match:
			pmid = pmid_match.group(1)
			#print pmid

		#get title
		t_match = re.match(r'Item Name="Title" Type="String">(.*?)$', i)
		if t_match:
			t = t_match.group(1)
			#print t

		#get jorunal name
		jt_match = re.match(r'Item Name="FullJournalName" Type="String">(.*?)$', i)
		if jt_match:
			jt =  jt_match.group(1)
			#print jt

		entry_match = re.match(r'/DocSum>', i)
		if entry_match:
			#print "\n"
			ptDic[pmid]=t
			pjDic[pmid]=jt
			jt='n/a'
			t='n/a'

	#print pDic
	return [ptDic,pjDic]

def about(request):
	context = {'nbar': 'about'}
	return render_to_response('about.html', context, context_instance=RequestContext(request))

def help(request):
	context = {'nbar': 'help'}
	return render_to_response('help.html', context, context_instance=RequestContext(request))

def dt_test_page(request):
	return render_to_response('dt_test_page.html')

def contact(request):
	context = {'nbar': 'contact'}
	return render_to_response('contact.html', context, context_instance=RequestContext(request))

def get_semmed_items(request):
	session = driver.session()
	if request.is_ajax():
		q = request.GET.get('term', '').split(',')[-1].strip()
		logger.debug('q = '+q)
		#get data for autocomplete
		gCom = "match (sem:SDB_item) where sem.name =~ '(?i)"+q+".*' return sem.name;"
		logger.debug(gCom)
		sList = []
		for res in session.run(gCom):
			v=res[0].encode("ascii")
			json_data = {}
			json_data['id']=v
			json_data['label']=v
			json_data['value']=v
			sList.append(json_data)
		sList_json = json.dumps(sList)
		logger.debug(len(sList))
	else:
		data = 'fail'
		logger.debug('not ajax request')
	mimetype = 'application/json'
	session.close()
	return HttpResponse(sList_json, mimetype)

def index(request):
	userInfo = "UserID:"+str(request.user.id)+" - "
	logger.debug(userInfo+"In index")

	form1 = CreateSearchSet()
	form_sem = CreateSemSet()
	form2 = ComSearchSets()
	form_pub = CreatePubSet()
	if request.method == 'POST':
		# create a form instance and populate it with data from the request:
		if request.POST['formType'] == "ss":
			if request.user.is_authenticated():
				form1 = CreateSearchSet(request.POST, request.FILES)
				#print "f = ",request.FILES
				# check whether it's valid:
				if form1.is_valid():
					# process the data in form.cleaned_data as required
					ss_file = request.FILES['ss_file']
					#save to file
					fileStore = tmpDir+'abstracts/'+str(ss_file)

					id=form1.cleaned_data['job_name'].strip()
					#remove special characters
					id = re.sub('[^A-Za-z0-9 _-]+', '', id)
					desc=form1.cleaned_data['ss_desc'].strip()
					searchParams=[id,str(request.user.id)]

					#add job and user data to sqlite db
					q = SearchSet(user_id=str(request.user.id), job_name=id, job_start=time.strftime("%Y-%m-%d %H:%M:%S"),job_status='Pending',ss_desc=desc,pTotal=0,ss_file=ss_file,job_progress=0)
					q.save()

					#run job in background
					#j = db_citations.delay(searchParams,fileStore)
					j = pmid_process.delay(searchParams,fileStore)

					SearchSet.objects.filter(user_id=str(request.user.id),job_name=id).update(job_id=j)

					# redirect to a new URL:
					return HttpResponseRedirect('jobs/')
			else:
				logger.debug(userInfo+"User authentication problem")
				return HttpResponseRedirect('/')
		if request.POST['formType'] == "ss_sem":
			if request.user.is_authenticated():
				form_sem = CreateSemSet(request.POST)
				#print "f = ",request.FILES
				# check whether it's valid:
				if form_sem.is_valid():
					# process the data in form.cleaned_data as required
					#add to graph db
					id=form_sem.cleaned_data['job_name'].strip()
					#remove special characters
					id = re.sub('[^A-Za-z0-9 _-]+', '', id)
					desc=form_sem.cleaned_data['ss_desc'].strip()
					sem_location = request.POST["ss_sem"]
					logger.debug('job_name = '+id)
					logger.debug('desc = '+desc)
					logger.debug('sem location = '+sem_location)
					searchParams=[id,str(request.user.id), sem_location,desc]

					#add job and user data to sqlite db
					descWithSem = sem_location+": "+desc
					q = SearchSet(user_id=str(request.user.id), job_name=id, job_start=time.strftime("%Y-%m-%d %H:%M:%S"),job_status='Pending',ss_desc=descWithSem,pTotal=0,ss_file='',job_progress=0)
					q.save()

					#run job in background
					logger.debug(userInfo+"Running db_sem")
					j = db_sem.delay(searchParams)

					SearchSet.objects.filter(user_id=str(request.user.id),job_name=id).update(job_id=j)

					# redirect to a new URL:
					return HttpResponseRedirect('jobs/')
			else:
				logger.debug(userInfo+"User authentication problem")
				return HttpResponseRedirect('/')
		if request.POST['formType'] == "ss_pub":
			if request.user.is_authenticated():
				form_pub = CreatePubSet(request.POST)
				#print "f = ",request.FILES
				# check whether it's valid:
				if form_pub.is_valid():
					# process the data in form.cleaned_data as required
					#add to graph db
					id=form_pub.cleaned_data['job_name'].strip()
					#remove special characters
					id = re.sub('[^A-Za-z0-9 _-]+', '', id)
					desc=form_pub.cleaned_data['ss_desc'].strip()
					logger.debug('job_name = '+id)
					logger.debug('desc = '+desc)
					searchParams=[id,str(request.user.id),desc]


					q = SearchSet(user_id=str(request.user.id), job_name=id, job_start=time.strftime("%Y-%m-%d %H:%M:%S"),job_status='Pending',ss_desc=desc,pTotal=0,ss_file='',job_progress=0)
					q.save()

					#run job in background
					logger.debug(userInfo+"Running pub_sem")
					j = pub_sem.delay(searchParams)

					SearchSet.objects.filter(user_id=str(request.user.id),job_name=id).update(job_id=j)

					# redirect to a new URL:
					return HttpResponseRedirect('jobs/')
			else:
				logger.debug(userInfo+"User authentication problem")
				return HttpResponseRedirect('/')
		if request.POST['formType'] == "com":
			logger.debug(userInfo+"Comparing search sets")
			form2 = ComSearchSets(request.POST)
			if form2.is_valid():
				ass=form2.cleaned_data['a']
				bss=form2.cleaned_data['b']
				comType = form2.cleaned_data['comType']

				#get year range data
				yearRange = request.POST["yearRange"]
				logger.debug('yearRange:'+yearRange)
				#add one year to upper bound to make it inclusive
				year2 = int(yearRange.split("-")[1].strip())
				yearRange = yearRange.split("-")[0].strip()+" - "+str(year2)
				logger.debug('yearRange corrected:'+yearRange)


				#check if analysing one or two search sets
				if len(ass)>1 and len(bss)==0:
					logger.debug(userInfo+"analysing single search set")
					logger.debug("ss1 - "+str(ass))
					s1=SearchSet.objects.get(job_name=ass,user_id=str(request.user.id))
					jobName = str(s1.id)
					for c in comType:
						print "c = ",c
						try:
							jCheck = Compare.objects.get(job_name=jobName,year_range=yearRange,user_id=str(request.user.id),job_type=c)
							logger.debug(userInfo+"job_status = "+str(jCheck.job_status))
							#delete entry if not complete and resubmitted
							if jCheck.job_progress != 100:
								logger.debug(userInfo+"Deleting job: "+str(jCheck.job_name))
								jCheck.delete()
								jCheck = False
						except ObjectDoesNotExist:
							jCheck = False
						if jCheck==False:
							jobDesc = str(s1.job_name)
							q = Compare(user_id=str(request.user.id), year_range=yearRange, job_desc=jobDesc, job_name=jobName, job_start=time.strftime("%Y-%m-%d %H:%M:%S"), job_status='Pending',job_type=c,job_progress=0)
							q.save()
							j=single_ss_Wrapper.delay(str(request.user.id),s1.id,c,yearRange)
						else:
							logger.debug(userInfo+"Search set comparison already run")
				elif len(ass)>1 and len(bss)>1:
					logger.debug(userInfo+"analysing two search sets")
					logger.debug("ss1 - "+str(ass))
					logger.debug("ss2 - "+str(bss))

					#get ids for search sets
					s1=SearchSet.objects.get(job_name=ass,user_id=str(request.user.id))
					s2=SearchSet.objects.get(job_name=bss,user_id=str(request.user.id))

					#include year2 to deal with year filtering option
					jobName = str(s1.id)+"_"+str(s2.id)+"_"+str(year2)
					for jobType in comType:
						logger.debug("jobType = "+jobType)
						try:
							jCheck = Compare.objects.get(job_name=jobName,year_range=yearRange,user_id=str(request.user.id),job_type=jobType)
							logger.debug(userInfo+"job_status = "+str(jCheck.job_status))
							#removed this section as allows same job to run if already running.
							#delete entry if not complete and resubmitted
							#if jCheck.job_progress != 100:
							#	logger.debug(userInfo+"Deleting job: "+str(jCheck.job_name))
							#	jCheck.delete()
							#	jCheck = False
						except ObjectDoesNotExist:
							jCheck = False
						if jCheck==False:
							jobDesc = str(s1.job_name)+" : "+str(s2.job_name)
							q = Compare(user_id=str(request.user.id), job_desc=jobDesc, year_range=yearRange, job_name=jobName, job_start=time.strftime("%Y-%m-%d %H:%M:%S"), job_status='Pending',job_type=jobType,job_progress=0)
							q.save()
							#j=comWrapper.delay(str(request.user.id),s1.id,s2.id,jobType,yearRange)
							j=comWrapper.delay(q.id)
						else:
							logger.debug(userInfo+"Search set comparison already run")
				return HttpResponseRedirect('jobs/')
	else:
		form1 = CreateSearchSet()
		form_sem = CreateSemSet()
		form2 = ComSearchSets()
		form_pub = CreatePubSet()

	#get search set data for table
	s = list()
	j=SearchSet.objects.filter(user_id=str(request.user.id),job_status='Complete')


	context = {'s': j, 'form1': form1, 'form2': form2, 'form_sem':form_sem, 'form_pub':form_pub, 'nbar': 'home'}
	return render_to_response('index.html', context, context_instance=RequestContext(request))

@cache_page(None)
def articleDetails(request,num):
	session = driver.session()
	userInfo = "UserID:"+str(request.user.id)+" - "
	logger.debug(userInfo+"In article details")
	resID=num
	logger.debug(userInfo+str(resID))
	q = SearchSet.objects.get(id=resID)

	gCom = "match (s:SearchSet)<-[r:INCLUDES]->(p:Pubmed) where s.name = '"+q.job_name+"_"+q.user_id+"' return p.dp,p.issn;"
	logger.debug(userInfo+"gCom:"+gCom)
	years = set()
	yearCounts = defaultdict(dict)
	for res in session.run(gCom):
		if type(res[0]) != type(None):
			#logger.debug(res)
			y = res[0].split(" ")[0]
			j = res[1]
			if type(y) != type(None) and type(j) != type(None) and y != '':
				y = int(y)
				j = j.encode("ascii")
				years.add(y)
				if y in yearCounts:
					if j in yearCounts[y]:
						yearCounts[y][j]+=1
					else:
						yearCounts[y][j]=1
				else:
					yearCounts[y][j]=1
	#logger.debug(years)
	article_data=[]
	if len(years)>0:
		years = range(min(years),max(years)+1)
		logger.debug(years)
		#logger.debug(len(yearCounts))
		#'1995': {'1040-872X': 1, '0090-3493': 2
		jTotals = {}
		for i in yearCounts:
			#logger.debug('i = '+str(i))
			for j in yearCounts[i]:
				if j in jTotals:
					jTotals[j] = jTotals[j]+1
				else:
					jTotals[j]=1
				jTotals[j]
				#logger.debug(str(j)+":"+str(yearCounts[i][j]))
		numTopJ = 10
		topJs = dict(sorted(jTotals.items(), key=operator.itemgetter(1),reverse=True)[0:numTopJ])
		#logger.debug(topJs)

		#create top counts
		topCounts = defaultdict(dict)
		for i in years:
			topCounts[i]['Other']=0
			for j in topJs:
				if i in yearCounts:
					if j in yearCounts[i]:
						topCounts[i][j] = yearCounts[i][j]
					else:
						topCounts[i][j] = 0
				else:
					topCounts[i][j] = 0
		#logger.debug(topCounts)

		#add counts not in the top set as 'Other'
		for i in yearCounts:
			for j in yearCounts[i]:
				if j not in topCounts[i]:
					topCounts[int(i)]['Other'] += yearCounts[i][j]
		#logger.debug(topCounts)

		#convert ISSN to name
		iList = []
		for i in topJs:
			iList.append(i)
		iName = issn_to_name(iList)

		topJs['Other']=0
		for t in topJs:
			if t in iName:
				a = {'name':iName[t],'data':[]}
			else:
				a = {'name':t,'data':[]}
			for i in topCounts:
				a['data'].append(topCounts[i][t])
			article_data.append(a)
		#logger.debug(article_data)




	context = {'years':years,'aData':json.dumps(article_data),'ss':q.job_name,'nbar': 'results'}
	session.close()
	return render_to_response('articles.html', context, context_instance=RequestContext(request))


#@login_required
def jobs(request):
	userInfo = "UserID:"+str(request.user.id)+" - "
	logger.debug(userInfo+"In jobs")
	context = {'nbar': 'results'}
	return render_to_response('jobs.html', context, context_instance=RequestContext(request))

#@login_required
#@cache_page(None)
def results(request,num):
	userInfo = "UserID:"+str(request.user.id)+" - "
	logger.debug(userInfo+"In results")
	resID=num
	logger.debug(userInfo+str(resID))
	#find out if it's a shared result
	uuid_regex = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
	r =  re.match(uuid_regex,num)
	userStatus = 'user'
	if r:
		logger.debug('Results page URL is a UUID')
		q = Compare.objects.get(hash_id=resID)
		#set resID back to ID
		resID=q.id
		if str(q.user_id) != str(request.user.id) and q.share==False:
			logger.debug('wrong user access - user id = '+str(request.user.id)+' data id = '+str(q.user_id))
			return HttpResponseRedirect('/')
		elif str(q.user_id) != str(request.user.id) and q.share==True:
			userStatus = 'guest'
	else:
		q = Compare.objects.get(id=resID)
		if str(q.user_id) != str(request.user.id):
			logger.debug('wrong user access - user id = '+str(request.user.id)+' data id = '+str(q.user_id))
			return HttpResponseRedirect('/')

	shareStatus = q.share

	jobDir = ""
	d1 = {}
	d2 = {}
	#cor_pval=1e-5
	jobDir = q.job_name
	d = str(q.job_name)

	#get hash_id
	hash_id = q.hash_id

	#get year end
	year2 = int(q.year_range.split('-')[1].strip())-1

	#check for single sarch set jobs
	if '_' in d:
		#get search set names
		s1_name = q.job_desc.split(":")[0]
		s2_name = q.job_desc.split(":")[1]
		logger.debug(userInfo+"two ss results")
		if  q.job_type == 'Temmpo':
			#o = Overlap.objects.filter(mc_id=resID)
			#o_json = []
			#for i in o:
			#	dic = {}
			#	dic['uniq_a']=i.uniq_a
			#	dic['uniq_b']=i.uniq_b
			#	o_json.append(dic)
			#o_json = json.dumps(o_json)
			#o_json = serializers.serialize('json', o, fields=('name','uniq_a','uniq_b'))
			context={'hash_id':hash_id, 'res':resID,'resA':d1,'resB':d2, 'nbar': 'results', 's1_name':s1_name, 's2_name':s2_name, 'year2':year2,'userStatus':userStatus,'shareStatus':shareStatus}
		else:
			o = Overlap.objects.filter(mc_id=resID).count()
			#get semmed concepts
			cFile=DATA_FOLDER+'SRDEF.txt'
			infile = open(cFile, 'r')
			cDic = {}
			for line in infile:
				if not line.startswith("#"):
					cDic[(line.split("|")[0])]=line.split("|")[1]
			#convert to JSON
			cDic_json = json.dumps(cDic)

			#check if files exist
			f=tmpDir + 'saved_data/fet/' + str(d.split("_")[0]) + '_'+str(year2+1) + '.' + q.job_type + '.fet.gz'
			logger.debug('Reding data from '+f)
			if os.path.isfile(f):
				with gzip.open(f, 'rb') as f:
					next(f)
					for line in f:
						l = line.rstrip('\n').encode("ascii").split("\t")
						#if float(l[7]) <= cor_pval:
						d1[l[0]] = ["{:,}".format(int(l[1])) + "/" + "{:,}".format(int(l[2])),
									"{:,}".format(int(float(l[3]))) + "/" + "{:,}".format(int(float(l[4]))), ("%4.2f" % float(l[5])),
									("%03.02e" % float(l[6])), ("%03.02e" % float(l[7]))]
			f=tmpDir + 'saved_data/fet/' + str(d.split("_")[1]) + '_'+str(year2+1) + '.' + q.job_type + '.fet.gz'
			if os.path.isfile(f):
				with gzip.open(f, 'rb') as f:
					next(f)
					for line in f:
						l = line.rstrip('\n').encode("ascii").split("\t")
						#if float(l[7]) <= cor_pval:
						d2[l[0]] = ["{:,}".format(int(l[1])) + "/" + "{:,}".format(int(l[2])),
									"{:,}".format(int(float(l[3]))) + "/" + "{:,}".format(int(float(l[4]))), ("%4.2f" % float(l[5])),
									("%03.02e" % float(l[6])), ("%03.02e" % float(l[7]))]
						# d['pTotal']="{:,}".format(int(r[3]))
			context={'hash_id':hash_id, 'res':resID,'resA':d1,'resB':d2, 'nbar': 'results', 's1_name':s1_name, 's2_name':s2_name, 'overlap':o,'year2':year2,'cDic':cDic_json,'userStatus':userStatus,'shareStatus':shareStatus}

		if q.job_type == 'meshMain':
			return render_to_response('mesh.html', context, context_instance=RequestContext(request))
		elif q.job_type == 'semmed_t' or q.job_type == 'semmed':
			return render_to_response('semmed.html', context, context_instance=RequestContext(request))
		elif q.job_type == 'semmed_c':
			return render_to_response('semmed_c.html', context, context_instance=RequestContext(request))
		elif q.job_type == 'semmed_c':
			return render_to_response('semmed_c.html', context, context_instance=RequestContext(request))
		elif q.job_type == 'Temmpo':
			return render_to_response('temmpo_res.html', context, context_instance=RequestContext(request))
	else:
		logger.debug(userInfo+"single ss results")
		f=tmpDir + 'saved_data/fet/' + str(d) + '_'+str(year2+1)+ '.' + q.job_type + '.fet.gz'
		if os.path.isfile(f):
			with gzip.open(f, 'rb') as f:
				next(f)
				for line in f:
					l = line.rstrip('\n').encode("ascii").split("\t")
					#if float(l[7]) <= cor_pval:
					d1[l[0]] = ["{:,}".format(int(l[1])) + "/" + "{:,}".format(int(l[2])),
								"{:,}".format(float(l[3])) + "/" + "{:,}".format(float(l[4])), ("%4.2f" % float(l[5])),
								("%03.02e" % float(l[6])), ("%03.02e" % float(l[7]))]
		context={'hash_id':hash_id, 'res':resID,'resA':d1, 'nbar': 'results','s1_name':q.job_desc,'year2':year2,'userStatus':userStatus,'shareStatus':shareStatus}
		if q.job_type == 'meshMain':
			return render_to_response('mesh_single.html', context, context_instance=RequestContext(request))
		elif q.job_type == 'semmed_t' or q.job_type == 'semmed_c':
			return render_to_response('semmed_single.html', context, context_instance=RequestContext(request))

class OrderListJson(BaseDatatableView):
	# The model we're going to show
	model=Compare
	columns = ['user_id', 'job_name', 'job_desc']
	order_columns = ['user_id']
	max_display_length = 500

	def get_initial_queryset(self):
		return Compare.objects

	def prepare_results(self, qs):

		# prepare list with output column data
		# queryset is already paginated here
		json_data = []
		for item in qs:
			json_data.append([
				'fish',
				item.user_id,
				item.job_name,
				item.job_desc,
			])
		return json_data

class ajax_searchset(BaseDatatableView):

	#get the user id
	#user_id = 'None'
	#def __init__(self, *args, **kwargs):
	#	self.request = kwargs.pop('request', None)
	#	super(ajax_searchset, self).__init__(*args, **kwargs)

	# The model we're going to show
	#model=SearchSet
	#model=SearchSet.objects.filter(user_id=str(2))
	columns = ['job_name', 'ss_desc', 'job_start', 'job_status','job_progress','id']
	order_columns = ['job_name', 'ss_desc', 'job_start', 'job_status','job_progress','id']
	max_display_length = 500

	def get_initial_queryset(self):
		user_id = self.request.user.id
		return SearchSet.objects.filter(user_id=str(user_id))

	def prepare_results(self, qs):

		# prepare list with output column data
		# queryset is already paginated here
		json_data = []
		for item in qs:
			json_data.append([
				item.job_name,
				item.ss_desc,
				item.job_start,
				item.job_status,
				item.job_progress,
				item.id
			])
		return json_data

class ajax_compare(BaseDatatableView):
	# The model we're going to show
	model=Compare
	#model=SearchSet.objects.filter(user_id=str(request.user.id))
	columns = ['job_desc','job_type','job_start', 'job_status','job_progress','id']
	order_columns = ['job_desc','job_type','job_start', 'job_status','job_progress','']
	max_display_length = 500

	def get_initial_queryset(self):
		user_id = self.request.user.id
		return Compare.objects.filter(user_id=str(user_id))

	def prepare_results(self, qs):

		# prepare list with output column data
		# queryset is already paginated here
		json_data = []
		for item in qs:
			job_desc = item.job_desc
			if item.year_range != '1950 - 2017':
				year1 = item.year_range.split('-')[0].strip()
				year2 = int(item.year_range.split('-')[1].strip())-1
				#logger.debug('y1:'+year1+' y2:'+str(year2))
				#year2 = int(item.year_range.split('-')[1].strip())+1
				job_desc = job_desc+' ('+year1+'-'+str(year2)+')'

			json_data.append([
				job_desc,
				item.job_type,
				item.job_start,
				item.job_status,
				item.job_progress,
				item.id
			])
		return json_data

class ajax_overlap(BaseDatatableView):
	# The model we're going to show
	model=Overlap
	#model=SearchSet.objects.filter(user_id=str(request.user.id))
	columns = ['name', 'uniq_a','uniq_b','shared','score','mean_cp','mean_odds','treeLevel','id']
	order_columns = ['name', 'uniq_a','uniq_b','shared','score','mean_cp','mean_odds','treeLevel','id']
	max_display_length = 500

	def get_initial_queryset(self):
		#resID = 926
		#user_id = self.request.user.id
		resID = self.request.GET.get('resID',None)
		logger.debug('resID: '+resID)
		return Overlap.objects.filter(mc_id=resID)

	def filter_queryset(self, qs):
		logger.debug('filter_queryset')
		# use request parameters to filter queryset

		# using standard filter
		search = self.request.GET.get(u'search[value]', None)
		if search:
			search = search
			logger.debug('Searching with filter '+search)
			qs = qs.filter(name__icontains=search)

		#get analysis type
		aType = self.request.GET.get('t', None)
		logger.debug('Filter query on '+aType)

		#filter using negative search terms
		negVals = self.request.GET.get('n',None)
		if negVals:
			negVals = json.loads(negVals)
			#deal with thml
			negVals = HTMLParser.HTMLParser().unescape(negVals)
			#logger.debug('nVals = '+str(negVals))

		if aType == 'semmed':
			for i in negVals:
				if len(negVals[i])>0:
					#neg = negVals[i]
					#negList = negVals[i].replace('(','\(').replace(')','\)').split('||')
					negList = negVals[i].split('||')
					logger.debug(i+":"+str(negList))
					if i == 's1':
						qs = qs.exclude(name1__in=negList)
					elif i == 's2':
						qs = qs.exclude(name2__in=negList)
					elif i == 's3':
						qs = qs.exclude(name3__in=negList)
					elif i == 's4':
						qs = qs.exclude(name4__in=negList)
					elif i == 's5':
						qs = qs.exclude(name5__in=negList)
		else:
			if len(negVals)>0:
				negVals = negVals.replace('(','\(').replace(')','\)')
				logger.debug('filtering on negVals '+negVals)
				qs = qs.exclude(name__iregex=r''+negVals+'')
				negList = negVals.split('||')

		#filter using positive search terms
		posVals = self.request.GET.get('p',None)
		if posVals:
			posVals = json.loads(posVals)
			posVals = HTMLParser.HTMLParser().unescape(posVals)

		#logger.debug('pVals = '+str(posVals))
		if aType == 'semmed':
			for i in posVals:
				if len(posVals[i])>0:
					#p = posVals[i]
					#posList = posVals[i].replace('(','\(').replace(')','\)').split('||')
					posList = posVals[i].split('||')
					#logger.debug(i+":"+p)
					if i == 's1':
						qs = qs.filter(name1__in=posList)
					elif i == 's2':
						qs = qs.filter(name2__in=posList)
					elif i == 's3':
						qs = qs.filter(name3__in=posList)
					elif i == 's4':
						qs = qs.filter(name4__in=posList)
					elif i == 's5':
						qs = qs.filter(name5__in=posList)
					#reg = r'^'+r1+'\|\|'+r2+'\|\|'+r3+'\|\|'+r4+'\|\|'+r5
					#logger.debug(reg)
					#qs = qs.filter(name__iregex=r''+reg+'')
		else:
			if len(posVals)>0:
				posVals = posVals.replace('(','\(').replace(')','\)')
				#posList = posVals.split('||')
				logger.debug('filtering on posVals ' +posVals)
				qs = qs.filter(name__iregex=r''+posVals+'')
				#qs = qs.filter(name__in=posList)

		#filter using sliders
		pval = self.request.GET.get('pval',None)
		odds = self.request.GET.get('odds',None)
		pfr = self.request.GET.get('pfr',None)
		#logger.debug('pval:'+pval+' odds:'+odds+' pfr:'+pfr)
		if pval and pval != 'NaN':
			qs = qs.filter(mean_cp__lte=pval)
		if odds and odds != 'NaN':
			qs = qs.filter(mean_odds__gte=odds)
		if pfr and pfr != 'NaN':
			qs = qs.filter(treeLevel__gte=pfr)

		logger.debug('len(qs)='+str(len(qs)))
		return qs

	def prepare_results(self, qs):

		# prepare list with output column data
		# queryset is already paginated here
		json_data = []
		#top = self.request.GET.get('top',None)
		#logger.debug('top:'+top)
		#tCount=0

		#get SemMedDB concept terms
		aType = self.request.GET.get('t', None)
		if aType == 'semmed':

			#Milk||PART_OF||Breast||261943:Breast||LOCATION_OF||Diphosphonates||10722541
			# termDic = {}
			# termSet = Set()
			#
			# for item in qs:
			# 	#s = item.name.split("||")
			# 	termSet.add(item.name1)
			# 	termSet.add(item.name3)
			# 	termSet.add(item.name5)
			# termString = ', '.join('"' + item + '"' for item in termSet)
			# logger.debug('termString = '+str(termString))
			# session = driver.session()
			#
			# gCom = "match (s:SDB_item) where s.name in ["+termString+"] return s.name,s.type";
			# logger.debug("gCom:"+gCom)
			# for res in session.run(gCom):
			# 	if res["s.name"] in termDic:
			# 		a=termDic[res["s.name"]]
			# 		termDic[res["s.name"]] = a+","+res["s.type"]
			# 	else:
			# 		termDic[res["s.name"]]=res["s.type"]
			# logger.debug(termDic)

			for item in qs:
				#create type string
				#s = item.name.split("||")
				#ts = termDic[s[0]]+"||"+termDic[s[2]]+"||"+termDic[s[5]]
				#if tCount<int(top):
				json_data.append([
					item.name,
					item.uniq_a,
					item.uniq_b,
					item.shared,
					item.score,
					item.mean_cp,
					item.mean_odds,
					item.treeLevel,
					item.id,
					#ts
				])
				#tCount+=1
		elif aType == 'semmed_c':
			# termDic = {}
			# termSet = Set()
			#
			# for item in qs:
			# 	#s = item.name.split("||")
			# 	termSet.add(item.name.split(":")[0])
			# termString = ', '.join('"' + item + '"' for item in termSet)
			# logger.debug('termString = '+str(termString))
			# session = driver.session()
			#
			# gCom = "match (s:SDB_item) where s.name in ["+termString+"] return s.name,s.type";
			# logger.debug("gCom:"+gCom)
			# for res in session.run(gCom):
			# 	name = res["s.name"].split(":")[0]
			# 	if name in termDic:
			# 		a=termDic[name]
			# 		termDic[name] = a+","+res["s.type"]
			# 	else:
			# 		termDic[name]=res["s.type"]
			# logger.debug(termDic)

			for item in qs:
				#create type string
				s = item.name.split(":")[0]
				#ts = termDic[s]
				#if tCount<int(top):
				json_data.append([
					s,
					item.uniq_a,
					item.uniq_b,
					item.shared,
					item.score,
					item.mean_cp,
					item.mean_odds,
					item.treeLevel,
					item.id,
					#ts
				])
		else:
			for item in qs:
				#if tCount<int(top):
				json_data.append([
					item.name,
					item.uniq_a,
					item.uniq_b,
					item.shared,
					item.score,
					item.mean_cp,
					item.mean_odds,
					item.treeLevel,
					item.id
				])

		return json_data

@cache_page(None)
def pubDetails(request,num):
	session = driver.session()
	userInfo = "UserID:"+str(request.user.id)+" - "
	logger.debug(userInfo+"In pubDetails")
	p_id = num.split("_")[0]
	tab = num.split("_")[1]
	if tab == '0':
		tab = 's1'
	elif tab == '1':
		tab = 's2'
	elif tab == '2':
		tab = 'shared'
	o = Overlap.objects.get(pk=p_id)
	m = o.mc_id
	logger.debug(m)
	c = Compare.objects.get(pk=m.id)

	#get year range data
	year1 = c.year_range.split("-")[0].strip()
	year2 = c.year_range.split("-")[1].strip()
	logger.debug('year1 = '+year1+' year2 = '+year2)
	yearString = ''
	if year1 != '1960' or year2 != '2016':
		yearString = "p.dcom >= '"+year1+"' and p.dcom <= '"+year2+"' and"

	#check user ids match
	if str(c.user_id) != str(request.user.id):
		logger.debug('wrong user access - user id = '+str(request.user.id)+' data id = '+c.user_id)
		return HttpResponseRedirect('/')

	ss1=c.job_desc.split(":")[0].strip()+"_"+c.user_id
	ss2=c.job_desc.split(":")[1].strip()+"_"+c.user_id

	mName = o.name.split(":")[0].split('(',1)[0].strip()

	jobType = m.job_type

	if jobType == "meshMain":
		gCom = "match (s:SearchSet)<-[r:INCLUDES]->(p:Pubmed)<-[h:HAS_MESH{mesh_type:'main'}]->(m:Mesh) where "+yearString+" s.name in ['"+ss1+"','"+ss2+"'] and m.mesh_name = '"+mName+"' return s.name,p.pmid,p.dcom;"
	elif jobType == "notMeshMain":
		gCom = "match (s:SearchSet)<-[r:INCLUDES]->(p:Pubmed)<-[h:HAS_MESH]->(m:Mesh) where "+yearString+" s.name in ['"+ss1+"','"+ss2+"'] and m.mesh_name = '"+mName+"' return s.name,p.pmid,p.dcom;"
	elif jobType == "semmed_t" or jobType == 'semmed':
		sem_1_ID = o.name.split(":")[0].split("||")[3]
		sem_2_ID = o.name.split(":")[1].split("||")[3]
		t1 = o.name.split(":")[0].split("||")[0]
		t2 = o.name.split(":")[0].split("||")[1]
		t3 = o.name.split(":")[0].split("||")[2]
		t4 = o.name.split(":")[1].split("||")[0]
		t5 = o.name.split(":")[1].split("||")[1]
		t6 = o.name.split(":")[1].split("||")[2]
		logger.debug(t1+"|"+t6)
		#if t1 == t6:
		#	mName = "(REVERSE) "+t4+" || "+t5+" || "+t6+" || "+t2+" || "+t3
		#else:
		mName = t1+" || "+t2+" || "+t3+" || "+t5+" || "+t6
		gCom = "match (s:SearchSet)<-[r:INCLUDES]->(p:Pubmed)<-[h:SEM]->(sdb:SDB_triple) where "+yearString+" s.name = '"+ss1+"' and sdb.pid = "+sem_1_ID+" return s.name,p.pmid,p.dp " \
		"UNION match (s:SearchSet)<-[r:INCLUDES]->(p:Pubmed)<-[h:SEM]->(sdb:SDB_triple) where "+yearString+" s.name = '"+ss2+"' and sdb.pid = "+sem_2_ID+" return s.name,p.pmid,p.dp;"
	elif jobType == "semmed_c":
		gCom = "match (s:SearchSet)-[r:INCLUDES]-(p:Pubmed)-[:SEM]-(st:SDB_triple)-[:SEMS|:SEMO]-(si:SDB_item) where "+yearString+" s.name in ['"+ss1+"','"+ss2+"'] and si.name = '"+mName+"' return s.name,p.pmid,p.dcom;"

	logger.debug(userInfo+"gCom:"+gCom)

	pAllDic = {}
	pDic = {}
	pmidList = []
	for res in session.run(gCom):
		ss=res[0].encode("ascii")
		pm=str(res[1])
		pd=res[2].encode("ascii")
		pmidList.append(pm)

		pAllDic[pm] = pd
		if ss in pDic:
			a = pDic[ss]
			if pm not in a:
				a.append(pm)
		else:
			pDic[ss] = [pm]

	#get titles
	ptDic,pjDic = pmid_to_info(pmidList)

	for i in pAllDic:
		a = pAllDic[i]
		t = 'n/a'
		j = 'n/a'
		if i in ptDic:
			t = ptDic[i]
		if i in pjDic:
			j = pjDic[i]
		b = (t,j,a)
		pAllDic[i] = b


	#print pDic
	#logger.debug(userInfo+"pDic:"+str(pDic))
	sDic = {}
	s1List = list()
	s2List = list()
	shareList = list()
	for i in pDic:
		j1 = pDic[ss1]
		j2 = pDic[ss2]
		sDic['o'] = list(set(j1).intersection(j2))
		sDic[ss1] = list(set(j1) - set(j2))
		sDic[ss2] = list(set(j2) - set(j1))
	if 'o' in sDic:
		for i in sDic['o']:
			e = {'pmid':i}
			shareList.append(e)
	if ss1 in sDic:
		for i in sDic[ss1]:
			e = {'pmid':i}
			s1List.append(e)
	if ss2 in sDic:
		for i in sDic[ss2]:
			e = {'pmid':i}
			s2List.append(e)
	ss1_name = ss1.rsplit("_",1)[0]
	ss2_name = ss2.rsplit("_",1)[0]

	context = {'s1':s1List,'s2':s2List,'share':shareList,'ss1':ss1_name, 'ss2':ss2_name, 'tab':tab,'mName':mName, 'pAllDic':pAllDic, 'nbar': 'results'}
	session.close()
	return render_to_response('pubs.html', context, context_instance=RequestContext(request))

def get_task_status(task_id):
	# If you have a task_id, this is how you query that task
	#print "in get_task_status"
	#print task_id
	task = db_citations.AsyncResult(task_id)

	status = task.status
	progress = 0
	stage=""

	if status == 'SUCCESS':
		progress = 100
		stage = 'Complete'
	elif status == 'FAILURE':
		#progress = 0
		stage = "Failed"
	elif status == 'PROGRESS':
		progress = task.info['progress']
		stage = task.info['stage']
	return {'status': status, 'progress': progress, 'stage':stage}

def ajax_share(request):
	resID = request.GET['resID']
	status = request.GET['status']
	if status == 'True':
		logger.debug('Sharing results - '+resID)
		Compare.objects.filter(hash_id=resID).update(share=True)
	else:
		logger.debug('Unsharing results - '+resID)
		Compare.objects.filter(hash_id=resID).update(share=False)
	#SearchSet.objects.filter(job_name=job_name,user_id=user_id).update(job_status='Adding pubmed data',job_progress=10)
	mimetype = 'application/json'
	context={}
	return HttpResponse(json.dumps(context), mimetype)

def export_to_csv(request, queryset, fields, resID):
	fName = 'melodi_result_'+str(resID)+'.csv'
	output = StringIO.StringIO() ## temp output file
	response = HttpResponse(content_type='application/zip')
	response['Content-Disposition'] = 'attachment;filename='+fName+'.zip'
	writer = csv.writer(output, dialect='excel')
	writer.writerow(fields)
	for obj in queryset:
		writer.writerow([getattr(obj, f) for f in fields])
	z = zipfile.ZipFile(response,'w')   ## write zip to response
	z.writestr(fName, output.getvalue())  ## write csv file to zip
	return response

def download_result(request):
	resID = request.POST.get('resID')
	type = request.POST.get('type')
	res_type = request.POST.get('download_res')
	logger.debug('Downloading - '+str(resID)+' : '+type+ ' : '+res_type)

	resID = request.POST.get('resID')
	type = request.POST.get('type')

	qs = Overlap.objects.filter(mc_id_id=resID)

	# using standard filter
	#search = request.GET.get(u'search[value]', None)
	#if search:
	#	logger.debug('Searching with filter '+search)
	#	qs = qs.filter(name__icontains=search)

	#get analysis type
	#aType = request.GET.get('t', None)
	#logger.debug('Filter query on '+aType)

	if res_type == 'filt':
		logger.debug('Downloading filtered - '+str(resID)+' : '+type)
		#filter using negative search terms
		negVals = request.POST.get('filt_results_n',None)
		logger.debug(negVals)
		if negVals:
			negVals = json.loads(negVals)
			#deal with thml
			negVals = HTMLParser.HTMLParser().unescape(negVals)
			#logger.debug('nVals = '+str(negVals))

		if type == 'st':
			for i in negVals:
				if len(negVals[i])>0:
					#neg = negVals[i]
					negList = negVals[i].split('||')
					#logger.debug(i+":"+str(negList))
					if i == 's1':
						qs = qs.exclude(name1__in=negList)
					elif i == 's2':
						qs = qs.exclude(name2__in=negList)
					elif i == 's3':
						qs = qs.exclude(name3__in=negList)
					elif i == 's4':
						qs = qs.exclude(name4__in=negList)
					elif i == 's5':
						qs = qs.exclude(name5__in=negList)
		else:
			if len(negVals)>0:
				logger.debug('filtering on negVals '+negVals)
				qs = qs.exclude(name__iregex=r''+negVals+'')
				negList = negVals.split('||')

		#filter using positive search terms
		posVals = request.POST.get('filt_results_p', None)
		if posVals:
			posVals = json.loads(posVals)
			posVals = HTMLParser.HTMLParser().unescape(posVals)

		# logger.debug('pVals = '+str(posVals))
		if type == 'st':
			for i in posVals:
				if len(posVals[i]) > 0:
					# p = posVals[i]
					posList = posVals[i].split('||')
					# logger.debug(i+":"+p)
					if i == 's1':
						qs = qs.filter(name1__in=posList)
					elif i == 's2':
						qs = qs.filter(name2__in=posList)
					elif i == 's3':
						qs = qs.filter(name3__in=posList)
					elif i == 's4':
						qs = qs.filter(name4__in=posList)
					elif i == 's5':
						qs = qs.filter(name5__in=posList)
					# reg = r'^'+r1+'\|\|'+r2+'\|\|'+r3+'\|\|'+r4+'\|\|'+r5
					# logger.debug(reg)
					# qs = qs.filter(name__iregex=r''+reg+'')
		else:
			if len(posVals) > 0:
				posList = posVals.split('||')
				logger.debug('filtering on posVals')
				# qs = qs.filter(name__iregex=r''+posVals+'')
				qs = qs.filter(name__in=posList)

		# filter using sliders
		pval = request.POST.get('filt_results_pval', None)
		odds = request.POST.get('filt_results_odds', None)
		pfr = request.POST.get('filt_results_pfr', None)
		logger.debug('pval:'+pval+' odds:'+odds+' pfr:'+pfr)
		if pval and pval != 'NaN':
			qs = qs.filter(mean_cp__lte=pval)
		if odds and odds != 'NaN':
			qs = qs.filter(mean_odds__gte=odds)
		if pfr and pfr != 'NaN':
			qs = qs.filter(treeLevel__gte=pfr)

	logger.debug('len(qs)=' + str(len(qs)))

	#remove ids names
	if type == 'st':
		return export_to_csv(request, qs, fields = ('name1', 'name2', 'name3', 'name4', 'name5', 'mean_cp', 'mean_odds', 'uniq_a', 'uniq_b', 'shared', 'score', 'treeLevel'), resID=resID)
	elif type == 'mesh':
		for c in qs:
			c.name = c.name.rsplit(":",1)[0]
		return export_to_csv(request, qs, fields = ('name', 'mean_cp', 'mean_odds', 'uniq_a', 'uniq_b', 'shared', 'score', 'treeLevel'), resID=resID)
	elif type == 'sc':
		for c in qs:
			c.name = c.name.rsplit(":",1)[0]
		return export_to_csv(request, qs, fields = ('name', 'mean_cp', 'mean_odds', 'uniq_a', 'uniq_b', 'shared', 'score'), resID=resID)

def download_filter(request):
	fList = request.POST.get('fList')
	resID = request.POST.get('resID')
	fType = request.POST.get('fType')
	if fList != type(None) and len(fList)>0:
		response = HttpResponse(fList, content_type='application/force-download')
		response['Content-Disposition'] = 'attachment; filename="%s"' % resID+fType+'-filter.txt'
	return response

def upload_filter(request):
	logger.debug('uploading filter file')
	context={}
	return HttpResponse(json.dumps(context), 'application/json')

def save_filter(request):
	logger.debug('saving filters')
	resID = request.GET.get('resID')
	com = Compare.objects.get(pk=resID)
	type = request.GET.get('type')
	negVals = json.loads(request.GET.get('nsTerm'))
	posVals = json.loads(request.GET.get('psTerm'))
	logger.debug('resID : ' +resID+" type : "+type)
	logger.debug('nsTerm ' +str(negVals))
	logger.debug('psTerm ' +str(posVals))
	fCount=0
	if type == 'st':
		for i in negVals:
			if len(negVals[i])>0:
				neg = negVals[i]
				logger.debug(i+":"+neg)
				loc = int(i[1])
				f=Filters(com_id=com.id,version=1,type=type,num=fCount,value=neg,location=loc,ftype='neg')
				f.save()
				fCount+=1
	context={}
	return HttpResponse()

def ajax_delete(request):
	logger.debug('user_id = '+str(request.user.id))
	if str(request.user.id) == 'None':
		logger.debug('Someone is trying to delete the demo data!')
	else:
		session = driver.session()
		id = request.GET['id']
		type = request.GET['type']
		logger.debug('Deleting id '+id+' for type '+type)
		if type == 'AS':
			s = SearchSet.objects.get(pk=id)
			user_id = s.user_id
			name = s.job_name
			#check user ids match
			if str(user_id) != str(request.user.id):
				logger.debug('wrong user access - user id = '+str(request.user.id)+' data id = '+user_id)
				#return HttpResponseRedirect('/')
			else:
				#delete from mysql
				s.delete()
				Compare.objects.filter(job_name__contains=id+'_').delete()
				Compare.objects.filter(job_name=id).delete()
				#delete from neo4j
				com="match (s:SearchSet)-[r]-(p:Pubmed) where s.name = '"+name+"_"+user_id+"' delete s,r;"
				logger.debug(com)
				session.run(com)
				session.close()
				#delete FET data
				com = 'rm -r '+tmpDir+'saved_data/fet/'+id+'_*'
				logger.debug(com)
				subprocess.call(com, shell=True)
	return HttpResponse()

def temmpo(request):
	if str(request.user.id) == 'None':
		return HttpResponseRedirect('/')
	else:
		s=SearchSet.objects.filter(user_id=str(request.user.id),job_status='Complete')
		context = {'s': s}
		return render_to_response('temmpo.html', context, context_instance=RequestContext(request))

def temmpo_res(request):
	if str(request.user.id) == 'None':
		return HttpResponseRedirect('/')
	else:
		user = str(request.user.id)
		logger.debug('user = '+user)
		as1 = request.POST.get('as1')
		as2 = request.POST.get('as2')
		s1=SearchSet.objects.get(job_name=as1,user_id=str(request.user.id))
		s2=SearchSet.objects.get(job_name=as2,user_id=str(request.user.id))

		int_file = request.FILES['intFile']
		intData = int_file.read().replace("\n","','")[:-2]
		#save to file
		#fileStore = '/tmp/'+str(int_file)
		logger.debug("Running temmpo style analysis on "+str(as1)+" and "+str(as2))
		jobDesc = as1+" : "+as2
		jobName = str(s1.id)+"_"+str(s2.id)+"_2017"
		try:
			jCheck = Compare.objects.get(job_name=jobName, job_desc=jobDesc+" : "+str(int_file), user_id=str(request.user.id),job_type='Temmpo')
			# delete entry if not complete and resubmitted
			if jCheck.job_progress != 100:
				jCheck.delete()
				jCheck = False
		except ObjectDoesNotExist:
			jCheck = False
		if jCheck == False:
			q = Compare(user_id=str(request.user.id), job_desc=jobDesc+" : "+str(int_file), year_range='1950 - 2017', job_name=jobName, job_start=time.strftime("%Y-%m-%d %H:%M:%S"), job_status='Pending',job_type='Temmpo',job_progress=0)
			q.save()
			j=temmpo_task.delay(q.id,intData)
		return HttpResponseRedirect(reverse('jobs'))
