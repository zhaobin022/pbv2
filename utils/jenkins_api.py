import jenkins
import time
import datetime
import traceback
import svn.remote




# class JenkinsServer(models.Model):
#     server_name = models.CharField(max_length=128)
#     ip = models.GenericIPAddressField()
#     username = models.CharField(max_length=64)
#     password = models.CharField(max_length=256,blank=True,null=True)
#     token = models.CharField(max_length=256)
#     api_url = models.URLField()
#     workspace = models.CharField(max_length=256,blank=True,null=True)

class JenkinsApi(object):
    def __init__(self,jsever_obj):
        # self.url = jsever_obj.api_url
        # self.user_name = jsever_obj.username
        # self.token = jsever_obj.token
        # # self.job_obj = job_obj
        # self.job_name = job_obj.job_name
        # print self.url, self.user_name, self.token

        self.server = jenkins.Jenkins(jsever_obj.api_url, username=jsever_obj.username, password=jsever_obj.token)
        pass
        # print self.server.get_version()


    def copy_job(self,old_name,new_name):

        self.server.copy_job(old_name, new_name)

    def delete_job(self,job_name):
        self.server.delete_job(job_name)
    def rename_job(self,old_name,new_name):
        self.server.rename_job(old_name,new_name)
# if __name__ == '__main__':
    # jenkins_handler = JenkinsApi("http://10.12.208.89:8080", "admin", "e0f51bfdafb9bcccec1ab1e59aac0e41","a")
    # jenkins_handler.build_job({})

    # server = jenkins.Jenkins("http://10.12.208.89:8080", username="admin", password="6879e44b3dce17ae2df63d898a6ec318")
    # try:
    #     # server = jenkins.Jenkins("http://10.12.12.157:8080", username="admin", password="fe8640ce0a98f56b75fb3e68ba08f536")
    #     # msg = server.build_job(name='job1')
    #     # server.copy_job('job1','job1_copy')
    #     # pass
    #     from jkmgr.models import JenkinsJob
    #     obj = JenkinsJob.objects.get(pi=1)
    #     jobj = JenkinsApi(obj.jenkins_server)
    #     jobj.copy_job('job1')
    # except Exception as e:
    #     pass
    # print server.get_job_info("BUILD-exchange")
    # build_info_dict = server.get_build_info("BUILD-moneyweb",28)

