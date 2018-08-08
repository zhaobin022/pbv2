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
if __name__ == '__main__':
    # jenkins_handler = JenkinsApi("http://10.12.208.89:8080", "admin", "e0f51bfdafb9bcccec1ab1e59aac0e41","a")
    # jenkins_handler.build_job({})

    # server = jenkins.Jenkins("http://10.12.208.89:8080", username="admin", password="6879e44b3dce17ae2df63d898a6ec318")
    # try:
    server = jenkins.Jenkins("http://10.12.12.157:8080", username="admin", password="fe8640ce0a98f56b75fb3e68ba08f536")
    # ret = server.get_job_config('job22')
    # with open('ret1.xml','w') as f:
    #     f.write(ret)
    svn_xml = '''
<scm class="hudson.scm.SubversionSCM" plugin="subversion@2.11.1">
<locations>
  <hudson.scm.SubversionSCM_-ModuleLocation>
    <remote>http://abc.com</remote>
    <credentialsId></credentialsId>
    <local>.</local>
    <depthOption>infinity</depthOption>
    <ignoreExternalsOption>true</ignoreExternalsOption>
    <cancelProcessOnExternalsFail>true</cancelProcessOnExternalsFail>
  </hudson.scm.SubversionSCM_-ModuleLocation>
</locations>
<excludedRegions></excludedRegions>
<includedRegions></includedRegions>
<excludedUsers></excludedUsers>
<excludedRevprop></excludedRevprop>
<excludedCommitMessages></excludedCommitMessages>
<workspaceUpdater class="hudson.scm.subversion.UpdateWithCleanUpdater"/>
<ignoreDirPropChanges>false</ignoreDirPropChanges>
<filterChangelog>false</filterChangelog>
<quietOperation>true</quietOperation>
</scm>
'''
    job1_config_xml = server.get_job_config('job1')

    import xml.etree.ElementTree as ET

    svn_root = ET.fromstring(svn_xml)

    job_root = ET.fromstring(job1_config_xml)
    for scm in job_root.iter("scm"):
        job_root.remove(scm)
        break



    for project in job_root.iter('project'):
        project.append(svn_root)
        break

    msg = ET.tostring(job_root,encoding='utf8')
    print(type(msg))
    server.reconfig_job('job1',msg.decode('utf-8'))
    pass

    # server.reconfig_job('job1',create_job_xml)
    # pass
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

