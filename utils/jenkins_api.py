import jenkins
import time
import datetime
import traceback
import svn.remote
import xml.etree.ElementTree as ET



class JenkinsApi(object):
    def __init__(self,jsever_obj):

        self.server = jenkins.Jenkins(jsever_obj.api_url, username=jsever_obj.username, password=jsever_obj.token)
        self.jsever_obj = jsever_obj


    def jk_ping(self):
        try:
            self.server.jobs_count()
            return True
        except Exception as e:
            return False
    def check_connect(func):

        def wrapper(self,*args,**kwargs):
            if not self.jk_ping():
                return ""
            return func(self,*args,**kwargs)
        return wrapper


    def create_job(self,job_obj):
        if not self.server.job_exists(job_obj.job_name):

            if job_obj.job_type == 2:
                job_config_xml = job_obj.jenkins_server.mavne_job_xml_template

            else:
                job_config_xml = jenkins.EMPTY_CONFIG_XML
            self.server.create_job(job_obj.job_name,job_config_xml)
            job_config_xml = self.server.get_job_config(job_obj.job_name)

            svn_auth = self.jsever_obj.svn_credentials_id or ""

            job_root = ET.fromstring(job_config_xml)
            if job_obj.svn_url:
                for scm in job_root.iter("scm"):
                    for remote in scm.iter("remote"):
                        if remote:
                            remote.text = job_obj.svn_url
                        break
                    if svn_auth:
                        for credentialsId in scm.iter("credentialsId"):
                            credentialsId.text = svn_auth
                            break
                    break

            # for project in job_root.iter('project'):
            #     project.append(svn_root)
            #     break

            new_job_config_xml = ET.tostring(job_root, encoding='utf8')
            self.server.reconfig_job(job_obj.job_name, new_job_config_xml.decode('utf-8'))

    def get_job_svn_url(self,job_name):

        job_config_xml = self.server.get_job_config(job_name)

        import xml.etree.ElementTree as ET


        job_root = ET.fromstring(job_config_xml)
        for scm in job_root.iter("scm"):
            ET.dump(scm)
            for remote in scm.iter("remote"):
                if remote:
                    return remote.text
                else:
                    return ""
                break
            break

    def set_svn_url(self,job_obj):

        job_config_xml = self.server.get_job_config(job_obj.job_name)

        job_root = ET.fromstring(job_config_xml)
        for scm in job_root.iter("scm"):
            for remote in scm.iter("remote"):
                remote.text = job_obj.svn_url
                break
            if self.jsever_obj.svn_credentials_id:
                for credentials_id in scm.iter("credentialsId"):
                    credentials_id.text = self.jsever_obj.svn_credentials_id
                break
            break
        ET.dump(job_root)

        new_xml = ET.tostring(job_root, encoding='utf8')
        self.server.reconfig_job(job_obj.job_name, new_xml.decode('utf-8'))



    def copy_job(self,old_name,new_name):

        self.server.copy_job(old_name, new_name)

    @check_connect
    def delete_job(self,job_name):
        if self.server.job_exists(job_name):
            self.server.delete_job(job_name)

    def rename_job(self,old_name,new_name):
        self.server.rename_job(old_name,new_name)
if __name__ == '__main__':
    # jenkins_handler = JenkinsApi("http://10.12.208.89:8080", "admin", "e0f51bfdafb9bcccec1ab1e59aac0e41","a")
    # jenkins_handler.build_job({})

    # server = jenkins.Jenkins("http://10.12.208.89:8080", username="admin", password="6879e44b3dce17ae2df63d898a6ec318")
    # try:
    server = jenkins.Jenkins("http://10.12.12.157:8080", username="admin", password="fe8640ce0a98f56b75fb3e68ba08f536")
    # print(server.get_version())
    server.jobs_count()
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
    # job1_config_xml = server.get_job_config('j5')
    #
    # import xml.etree.ElementTree as ET
    #
    # svn_root = ET.fromstring(svn_xml)
    #
    # job_root = ET.fromstring(job1_config_xml)
    # ET.dump(job_root)
    # me = server.get_whoami()
    # for scm in job_root.iter("scm"):
    #     ET.dump(scm)
    #     for remote in scm.iter("remote"):
    #
    #
    #         remote.text = 'http://111111111.com'
    #         break
    #     # job_root.remove(scm)
    #     break
    # ET.dump(job_root)
    #
    # msg = ET.tostring(job_root,encoding='utf8')
    # print(msg)
    # server.reconfig_job('j1',msg.decode('utf-8'))


    # for project in job_root.iter('project'):
    #     project.append(svn_root)
    #     break
    #
    # msg = ET.tostring(job_root,encoding='utf8')
    # print(type(msg))
    # server.reconfig_job('job1',msg.decode('utf-8'))
    # jenkins.RECONFIG_XML
    # pass

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

