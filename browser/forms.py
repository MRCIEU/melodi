from django import forms
from .models import SearchSet
from django.forms import ModelForm, Textarea, HiddenInput

COMTYPES=(
	('meshMain','Main Mesh'),
	#('notMeshMain', 'Not Main Mesh'),
	('semmed_c','SemMedDB Concept'),
	('semmed_t','SemMedDB Triple')

)

class ComSearchSets(forms.Form): #Note that it is not inheriting from forms.ModelForm
	a = forms.CharField(max_length=200,widget=forms.HiddenInput(),required=True,error_messages={'required': 'Please select two article sets from the table'})
	b = forms.CharField(max_length=200,widget=forms.HiddenInput(),required=False,error_messages={'required': 'Please select two article sets from the table'})
	comType = forms.MultipleChoiceField(required=True,widget=forms.CheckboxSelectMultiple(attrs={'checked' : 'checked'}), choices=COMTYPES, error_messages={'required': 'Please select at least one search option'})

class CreateSearchSet(forms.ModelForm):
	class Meta:
		model = SearchSet
		fields = ['job_name','user_id','ss_file','ss_desc']
		widgets = {
			'job_name': Textarea(attrs={'cols': 25, 'rows': 1, 'placeholder':'e.g. bmi_medline'}),
            'ss_desc': Textarea(attrs={'cols': 45, 'rows': 1,'placeholder':'e.g. BMI Pubmed search'}),
			'user_id': HiddenInput()
        }

class CreateSemSet(forms.ModelForm):
	class Meta:
		model = SearchSet
		fields = ['job_name','ss_desc','user_id']
		widgets = {
			'job_name': Textarea(attrs={'cols': 25, 'rows': 1, 'placeholder':'e.g. bmi_semmed'}),
            'ss_desc': Textarea(attrs={'cols': 35, 'rows': 1, 'class': 'ui-widget','id':'tags','placeholder':'e.g. body mass index'}),
			'user_id': HiddenInput()
        }

class CreatePubSet(forms.ModelForm):
	class Meta:
		model = SearchSet
		fields = ['job_name','ss_desc','user_id']
		widgets = {
			'job_name': Textarea(attrs={'cols': 25, 'rows': 1, 'placeholder':'e.g. bmi_pubmed'}),
            'ss_desc': Textarea(attrs={'cols': 85, 'rows': 1,'placeholder':'e.g. body mass index'}),
			'user_id': HiddenInput()
        }