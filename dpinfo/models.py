from __future__ import unicode_literals
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model


MyUser = get_user_model()

class Environment(models.Model):

    environment_name = models.CharField(max_length=50,unique=True,verbose_name="环境名")

    def __str__(self):
        return self.environment_name

    class Meta:
        verbose_name="部署环境"
        verbose_name_plural="部署环境"

def varildate_var(obj):
    env_list = Environment.objects.all().values_list("environment_name")
    key_list = []
    flag = True
    for e_name in env_list:
        if obj.startswith(e_name):
            flag=False
            break

    if flag:
        raise ValidationError(
            _("variables must belong to one envirment"),
        )
class AppVariables(models.Model):
    environment = models.ForeignKey(Environment,on_delete=models.CASCADE,null=True,blank=True,related_name="app_var")
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=255)


    def __str__(self):
        if self.environment:
            return '%s  %s : %s' % (self.environment.environment_name,self.key,self.value)
        else:
            return '%s  %s : %s' % ("public",self.key,self.value)

    class Meta:
        verbose_name = "应用变量表"
        verbose_name_plural = "应用变量表"



class DbVariables(models.Model):
    environment = models.ForeignKey(Environment,on_delete=models.CASCADE,null=True,related_name='db_var')

    key = models.CharField(max_length=255,verbose_name="数据库key")
    value = models.CharField(max_length=255,verbose_name="数据库value")


    def __str__(self):
        if self.environment:
            return '%s  %s : %s' % (self.environment.environment_name,self.key,self.value)
        else:
            return '%s  %s : %s' % ("public",self.key,self.value)
    class Meta:
        verbose_name = "数据库变量表"
        verbose_name_plural = "数据库变量表"



class JavaAppFoot(models.Model):
    foot_name = models.CharField(max_length=50)

    def __str__(self):
        return self.foot_name
    class Meta:
        verbose_name="Java应用服务名"
        verbose_name_plural="Java应用服务名"


class Hosts(models.Model):
    ipaddr =  models.GenericIPAddressField(unique=True)
    host_type_choice = (
        (0, 'app'),
        (1, 'db'),
    )
    host_type = models.IntegerField(choices=host_type_choice)

    def __str__(self):
        return self.ipaddr

    class Meta:
        verbose_name="主机"
        verbose_name_plural="主机"


class Group(models.Model):
    name = models.CharField(max_length=50,unique=True)

    def __str__(self):
        return  self.name

    class Meta:
        verbose_name="Ansible组"
        verbose_name_plural="Ansible组"

class Project(models.Model):
    name = models.CharField(max_length=50)
    version = models.ForeignKey("Version",null=True,blank=True,related_name="version",on_delete=models.CASCADE)
    lastversion = models.CharField(max_length=255,null=True,blank=True)
    pass_uat_test = models.BooleanField()
    production_tag = models.BooleanField(default=False)
    fun_job_name = models.CharField(max_length=255,null=True,blank=True)
    uat_job_name = models.CharField(max_length=255,null=True,blank=True)
    mn_prod_deploy_job = models.CharField(max_length=255,null=True,blank=True)
    sp_prod_deploy_job = models.CharField(max_length=255,null=True,blank=True)
    last_fun_successful_dir = models.CharField(max_length=255,null=True,blank=True)
    admin_email = models.ManyToManyField("EmailList",blank=True,related_name="admin_email")
    develop_email = models.ManyToManyField("EmailList",blank=True,related_name="develop_email")
    test_email = models.ManyToManyField("EmailList",blank=True,related_name="test_email")

    def __str__(self):
        return "%s_%s" % (self.name,self.version.name)


    class Meta:
        unique_together = (("name", "version"),)
        verbose_name="项目"
        verbose_name_plural="项目"

class Version(models.Model):
    name = models.CharField(max_length=255)


    def __str__(self):
        return self.name

    class Meta:
        verbose_name="版本"
        verbose_name_plural="版本"




class Tomcat(models.Model):
    name = models.CharField(max_length=255)

    http_type_choice = (
        (0, 'http'),
        (1, 'https'),
    )

    http_type = models.IntegerField(choices=http_type_choice)
    shutdown_port = models.PositiveIntegerField()
    http_port = models.PositiveIntegerField()
    https_port = models.PositiveIntegerField()
    jvm_size = models.PositiveIntegerField(default=2048)

    class Meta:
        unique_together = ("name", "http_type","shutdown_port","http_port","https_port")
        verbose_name="Tomcat配置"
        verbose_name_plural="Tomcat配置"


    def __str__(self):
        return "%s | %s | %d | %d | %d | %d" % (self.name,self.get_http_type_display(),self.shutdown_port,self.http_port,self.https_port,self.jvm_size)


class Templates(models.Model):
    name = models.CharField(max_length=255,unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name="自定义配置模版"
        verbose_name_plural="自定义配置模版"


class HostEnvironmentRelation(models.Model):
    environment = models.ForeignKey(Environment,on_delete=models.CASCADE)
    group = models.ForeignKey(Group,on_delete=models.CASCADE)
    hosts = models.ManyToManyField(Hosts)
    project = models.ForeignKey(Project,on_delete=models.CASCADE)
    app_foot = models.ManyToManyField(JavaAppFoot,blank=True)
    app_variables = models.ManyToManyField(AppVariables,blank=True,related_name="en_r_app_var_set")
    db_variables = models.ManyToManyField(DbVariables,blank=True,related_name="en_r_db_var_set")
    templates = models.ManyToManyField(Templates,blank=True)
    group_type_choice = (
        (0, 'javaapps'),
        (1, 'webapps'),
    )
    group_type = models.IntegerField(choices=group_type_choice)
    tomcat = models.ForeignKey(Tomcat,blank=True,null=True,on_delete=models.CASCADE)
    priority = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = (("environment", "group","project","group_type"),)
        verbose_name = "绑定关系表"
        verbose_name_plural = "绑定关系表"


    def __str__(self):
        return "%s -- %s -- %s" % (self.environment.environment_name,self.group.name,self.project)



class EmailList(models.Model):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "邮件地址"
        verbose_name_plural = "邮件地址"



class DbBaseInfo(models.Model):
    name = models.CharField(max_length=128,unique=True)
    host = models.ForeignKey(DbVariables,related_name="host_set",on_delete=models.CASCADE)
    port = models.ForeignKey(DbVariables,related_name="post_set",on_delete=models.CASCADE)
    sid = models.ForeignKey(DbVariables,related_name="sid_set",on_delete=models.CASCADE)
    db_user = models.ForeignKey(DbVariables,related_name="db_user_set",on_delete=models.CASCADE)
    db_password = models.ForeignKey(DbVariables,related_name="db_password_set",on_delete=models.CASCADE)

    db_charset_choice = (
        (1,"AMERICAN_AMERICA.ZHS16GBK"),
        (2,"AMERICAN_AMERICA.UTF8 ")
    )
    db_charset = models.PositiveIntegerField(choices=db_charset_choice,default=2)

    def __str__(self):
        return self.name


    class Meta:
        verbose_name = "数据库信息"
        verbose_name_plural = "数据库信息"



class SvnPath(models.Model):
    path = models.CharField(max_length=255,unique=True)
    svn_charset_choice = (
        (1,"zh_CN.GB18030"),
        (2,"en_US.UTF-8")
    )
    svn_charset = models.PositiveIntegerField(choices=svn_charset_choice,default=2)

    def __str__(self):
        return "%s : %s" % (self.id,self.path)


    class Meta:
        verbose_name = "svn路径"
        verbose_name_plural = "svn路径"


class ExecuteSqlLog(models.Model):
    db = models.ForeignKey(DbBaseInfo,on_delete=models.CASCADE)
    svn = models.ForeignKey(SvnPath,on_delete=models.CASCADE)
    sql_file_name = models.CharField(max_length=128)
    status_choice = (
        (0, 'successfull'),
        (1, 'failed'),
    )
    status = models.IntegerField(choices=status_choice)
    user = models.ForeignKey(MyUser,blank=True,null=True,on_delete=models.CASCADE)
    create_time = models.DateTimeField(auto_now_add=True)
    contents = models.TextField()


    class Meta:
        verbose_name = "sql执行日志记录"
        verbose_name_plural = "sql执行日志记录"