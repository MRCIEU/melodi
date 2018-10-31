from browser.models import SearchSet,Compare
from rest_framework import serializers


class SearchSetSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = SearchSet
		fields = ('user_id', 'job_name', 'job_id', 'job_progress','ss_desc','job_status','job_start','pTotal','id')
