import pytest
import sys
import os

sys.path.append(os.path.abspath('../scripts'))

from run import pub_sem,compare

#py.test -s

test_set_1 = ['TMEM163','GPNMB','STX4','HSD3B7','CRHR1','GRN','LINC02210']
test_set_2 = ["parkinson's disease"]

def test_create_sets():
	#test_query = ['TMEM163','GPNMB','STX4','HSD3B7','CRHR1','GRN','LINC02210',"parkinson's disease"]
	test_query = test_set_1+test_set_2
	for q in test_query:
		print('Creating',q)
		pub_sem(q,{})

def test_compare():
	print('aaaa')
