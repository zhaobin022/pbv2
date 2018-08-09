# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import Group
from dpinfo import models as dp_models
from django.db.models.signals import post_delete,post_save,pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from utils.jenkins_api import JenkinsApi
import copy

MyUser = get_user_model()

# Create your models here.



class JenkinsServer(models.Model):
    server_name = models.CharField(max_length=128)
    ip = models.GenericIPAddressField()
    username = models.CharField(max_length=64)
    password = models.CharField(max_length=256,blank=True,null=True)
    token = models.CharField(max_length=256)
    api_url = models.URLField()
    workspace = models.CharField(max_length=256,blank=True,null=True)
    mavne_job_xml_template = models.TextField(null=True,blank=True)
    svn_xml_template = models.TextField(null=True,blank=True)
    svn_credentials_id = models.CharField(max_length=128,null=True,blank=True)

    def __str__(self):
        return self.api_url


class Operation(models.Model):
    operation_name = models.CharField(max_length=128)
    operation_value = models.CharField(max_length=64)

    def __str__(self):
        return "%s(%s)" % (self.operation_name,self.operation_value)



    class Meta:
        unique_together = ("operation_name", "operation_value")




class JenkinsJob(models.Model):
    job_name = models.CharField(max_length=128,verbose_name="job名称")
    # notify_group = models.ManyToManyField(Group)
    project = models.ForeignKey(dp_models.Project,verbose_name="项目名",related_name='project_jobs',on_delete=models.CASCADE)
    # action_type=models.ForeignKey(Operation,blank=True,null=True,on_delete=models.CASCADE)
    default_action_type = models.ForeignKey(Operation,blank=True,null=True,on_delete=models.DO_NOTHING)
    action_list=models.ManyToManyField(Operation,blank=True,related_name="jks_job")

    jenkins_server = models.ForeignKey(JenkinsServer,on_delete=models.CASCADE)
    # environment = models.ForeignKey(dp_models.Environment,blank=True,null=True,on_delete=models.CASCADE)

    emails = models.ManyToManyField(dp_models.EmailList,blank=True)
    job_type_choice = (
        (0, u'功能测试部署(FUN)'),
        (1, u'用户验收测试部署(UAT)'),
        (2, u'构建'),
        (3, u'通过测试'),
        (4, u'生产准备'),
        (5, u'可选类型'),
        (6, u'生产部署'),
        (7, u'生产起停')
    )
    job_type = models.PositiveIntegerField(choices=job_type_choice,default=2)
    auto_build = models.BooleanField(default=False)
    svn_url = models.URLField(null=True,blank=True)

    # current_svn_version = models.PositiveIntegerField(blank=True,null=True)
    # fun_svn_version = models.PositiveIntegerField(blank=True,null=True)
    # uat_svn_version = models.PositiveIntegerField(blank=True,null=True)


    def __str__(self):
        if self.jenkins_server:
            return "%s(%s)" % (self.job_name,self.jenkins_server.server_name)
        else:
            return "%s()" % (self.job_name)


    class Meta:
        unique_together = (("job_name", "jenkins_server"),)

Group.add_to_class('jenkins_job',models.ManyToManyField(JenkinsJob,blank=True))
MyUser.add_to_class('jenkins_job',models.ManyToManyField(JenkinsJob,blank=True))

# dp_models.Project.add_to_class('fun_job',models.ForeignKey(JenkinsJob,blank=True))

@receiver(post_delete, sender=JenkinsJob)
def delete_job_after(sender, instance, **kwargs):

    js_obj = JenkinsApi(instance.jenkins_server)
    if js_obj.jk_ping():
        js_obj.delete_job(instance.job_name)


@receiver(pre_save , sender=JenkinsJob)
def save_job_before(sender, instance,raw,update_fields, **kwargs):

    old = JenkinsJob.objects.filter(pk=instance.pk).first()
    if old:
        js_obj = JenkinsApi(instance.jenkins_server)

        if old and old.job_name != instance.job_name:
            js_obj.rename_job(old.job_name,instance.job_name)

        if old.svn_url != instance.svn_url:
            old_svn_url = js_obj.get_job_svn_url(instance.job_name)
            if old_svn_url != instance.svn_url:
                js_obj.set_svn_url(instance)




@receiver(post_save , sender=JenkinsJob)
def save_job_after(sender, instance,created,raw,update_fields, **kwargs):

    if created:
        jk_server = instance.jenkins_server
        jk_handler = JenkinsApi(jk_server)
        jk_handler.create_job(instance)

