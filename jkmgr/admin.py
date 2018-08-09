# -*-coding:utf-8 -*-
from django.contrib import admin
import traceback
from django.contrib import messages
from django import forms
from django.utils.translation import ugettext_lazy as _


from . import models
from utils.jenkins_api import JenkinsApi


class CheckJkConnForm(forms.ModelForm):

    def ping_jk_server(self):
        jk_handler = JenkinsApi(self.cleaned_data['jenkins_server'])
        if not jk_handler.jk_ping():
            raise forms.ValidationError("Can't connect jenkins server !")

class JenkinsChangeJobForm(CheckJkConnForm):
    def __init__(self, *args, **kwargs):
        super(JenkinsChangeJobForm, self).__init__(*args, **kwargs)

    class Meta:
        model = models.JenkinsJob
        fields = '__all__'

    def clean(self):

        cleaned_data = super().clean()
        self.ping_jk_server()
        if self.instance:
            try:
                default_action_type_obj = cleaned_data["default_action_type"]
                if self.instance.action_list:
                    pks = list(self.instance.action_list.all().values_list("pk"))
                    pks = [i[0] for i in pks]
                else:
                    pks = []

                if default_action_type_obj and default_action_type_obj.id not in pks:
                    self.add_error("default_action_type",forms.ValidationError(_('Default action must in action list !')))
            except Exception as e:
                pass


class JenkinsCreateJobForm(CheckJkConnForm):
    def __init__(self, *args, **kwargs):
        super(JenkinsCreateJobForm, self).__init__(*args, **kwargs)

    class Meta:
        model = models.JenkinsJob
        fields = '__all__'

    def clean(self):
        self.ping_jk_server()
        jenkins_server = self.cleaned_data['jenkins_server']
        jk_handler = JenkinsApi(jenkins_server)
        if jk_handler.server.job_exists(self.cleaned_data['job_name']):
            self.add_error("job_name", forms.ValidationError(_('job exist in jenkins server !')))


class JenkinsJobAdmin(admin.ModelAdmin):
    list_display = ("id","job_name","project","default_action_type","jenkins_server","job_type","auto_build")
    search_fields = ("job_name","project",)
    raw_id_fields = ("project",)
    list_editable = ("job_name","project","default_action_type","jenkins_server","job_type","auto_build",)
    list_filter = ("auto_build",)
    filter_horizontal = ("emails","action_list")
    list_per_page = 20



    def get_form(self, request, obj=None, **kwargs):
        if obj:  # obj is not None, so this is a change page
            return JenkinsChangeJobForm
        else:  # obj is None, so this is an add page
            return JenkinsCreateJobForm
    # form = JenkinsChangeJobForm
    # add_form = JenkinsCreateJobForm

    def duplicate_jenkins_job(modeladmin, request, queryset):
        try:
            object_list = []
            for object in queryset:
                object.id=None
                jenkins_server = object.jenkins_server

                old_name = object.job_name
                new_name ="%s_copy" % object.job_name

                js_obj = JenkinsApi(jenkins_server)
                js_obj.copy_job(old_name,new_name)

                object.job_name=new_name
                object_list.append(object)


            models.JenkinsJob.objects.bulk_create(object_list)

            modeladmin.message_user(request, "copy successfull !", level=messages.INFO)
        except Exception as e:
            msg = traceback.format_exc()
            print(msg)
            modeladmin.message_user(request,"job exist!",level=messages.ERROR)

    duplicate_jenkins_job.short_description = u"复制JENKINS JOB"
    actions = (duplicate_jenkins_job,)


class OperationAdmin(admin.ModelAdmin):
    list_display = ("operation_name","operation_value")

class JenkinsServerAdmin(admin.ModelAdmin):

    '''

        server_name = models.CharField(max_length=128)
    ip = models.GenericIPAddressField()
    username = models.CharField(max_length=64)
    password = models.CharField(max_length=256,blank=True,null=True)
    token = models.CharField(max_length=256)
    api_url = models.URLField()
    workspace = models.CharField(max_length=256,blank=True,null=True)

    '''
    list_display = ("id","server_name","ip","username","token","api_url","workspace")
    list_editable = ("ip","username","token","api_url","workspace")

admin.site.register(models.JenkinsServer,JenkinsServerAdmin)
admin.site.register(models.JenkinsJob,JenkinsJobAdmin)
admin.site.register(models.Operation,OperationAdmin)