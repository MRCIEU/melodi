import requests
import time
import json
import requests

api_url='http://localhost:8000/api/'
#api_url='http://snp.mrbase.org/api/'


def get_set():
	url = api_url+'set/1/'
	print(url)
	start = time.time()
	r = requests.get(url)
	j = json.loads(r.text)
	#print(j)
	print("Time taken for API call:", round(time.time() - start, 3), "seconds")
	if len(j)>0:
		print(j)

def get_sets():
	url = api_url+'sets/'
	print(url)
	start = time.time()
	r = requests.get(url)
	j = json.loads(r.text)
	#print(j)
	print("Time taken for API call:", round(time.time() - start, 3), "seconds")
	if len(j)>0:
		print(j)

def create_new_set():
	headers = {'content-type': 'application/x-www-form-urlencoded'}
	params = {
		'user_id':'None',
		'job_name':'test1',
		'job_id':'test1',
		'job_progress':100,
		'ss_desc':'test1',
		'job_status':'Complete',
		'job_start':'never',
		'pTotal':1000
		}
	r = requests.post(api_url+'sets/', data=params, headers=headers)
	print(r.text)

get_set()
get_sets()
create_new_set()
