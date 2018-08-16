from django import forms
from django.forms import widgets
from .models import JenkinsJob

class BuildJenkinsJobForm(forms.ModelForm):

    class Meta:
        model = JenkinsJob
        fields = ['job_name','project','job_type','svn_url','emails']
        widgets = {
            'job_name': widgets.TextInput(attrs={'class':'form-control',"disabled":""}),
            'project': widgets.Select(attrs={'class': 'form-control', "disabled": ""}),
            'svn_url': widgets.TextInput(attrs={'class': 'form-control', "disabled": ""}),
            'job_type': widgets.Select(attrs={'class': 'form-control', "disabled": ""}),
            'emails': widgets.SelectMultiple(attrs={'class': 'form-control dual_select',}),
        }






