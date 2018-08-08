#!/home/zb/.virtualenvs/pbv2/bin/python -W ignore
# -- coding: UTF-8 --
import sys
import argparse
from collections import namedtuple
import os
import yaml
import traceback
import shutil
import subprocess
import time
import json
from prettytable import PrettyTable
import re
import shutil
import jenkins
import chardet
import datetime
import email
import mimetypes
import smtplib
import hashlib
import datetime
import glob
from jinja2 import Template
import zipfile
import fcntl
import requests
import redis
from urllib.parse import urljoin
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor

from ansible.plugins.callback import CallbackBase
import ansible.constants as C
from ansible.inventory.group import Group
from ansible.inventory.host import Host

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET




class AnsibleApi2(object):
    def __init__(self,inventory_dict,tag,hostname=None):
        self.tags_str = tag

        Options = namedtuple('Options',
                             ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection', 'module_path', 'forks',
                              'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
                              'scp_extra_args', 'become', 'become_method', 'become_user', 'remote_user', 'verbosity',
                              'check', 'diff','tags'])
        self.options = Options(listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh',
                          module_path=None, forks=100, private_key_file=None, ssh_common_args=None, ssh_extra_args=None,
                          sftp_extra_args=None, scp_extra_args=None, become=False, become_method=None, become_user=None,
                          remote_user=None, verbosity=None, check=False, diff=None,tags=[self.tags_str,])

        self.loader = DataLoader()

        # self.variable_manager.add_group_vars_file()

        self.passwords = {}
        # self.host_list = ['server02',]
        # self.group_var_file_path = group_var_file
        # self.group_var_file_path = 'group_vars/all_84'
        # self.group_var_file_path = group_var_path
        # self.variable_manager.add_group_vars_file(self.group_var_file_path,self.loader)
        # self.variable_manager.
        # print self.variable_manager._group_vars_files,11111111111111111

        self.inventory = InventoryManager(loader=self.loader, )
        self.inventory_data = self.inventory._inventory
        all_group = self.inventory_data.groups['all']
        if inventory_dict['group_type'] == 'webapps':
            self.inventory_data.add_group(inventory_dict['group']['name'])
            all_group.add_child_group(self.inventory_data.groups[inventory_dict['group']['name']])
            for h in inventory_dict['hosts']:
                self.inventory_data.add_host(h['ipaddr'], group=inventory_dict['group']['name'])
        elif inventory_dict['group_type']  == 'javaapps':
            if hostname:
                java_group_name = hostname
                self.inventory_data.add_group(java_group_name)
                all_group.add_child_group(self.inventory_data.groups[java_group_name])
                for h in inventory_dict['hosts']:
                    self.inventory_data.add_host(h['ipaddr'], group=java_group_name)

        if inventory_dict['environment']['app_var']:
            for i in inventory_dict['environment']['app_var']:
                all_group.set_variable(i['key'],i['value'])

        if inventory_dict['environment']['db_var']:
            for i in inventory_dict['environment']['db_var']:
                all_group.set_variable(i['key'],i['value'])

        if inventory_dict['app_variables']:
            for i in inventory_dict['app_variables']:
                all_group.set_variable(i['key'],i['value'])


        if inventory_dict['db_variables']:
            for i in inventory_dict['db_variables']:
                all_group.set_variable(i['key'],i['value'])

        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)


    def run_model(self,command_args,hosts):
        print('host list: ',self.inventory.get_hosts())
        play_source = dict(
            name="Ansible Play",
            hosts=hosts,
            gather_facts='no',
            tasks=[
                dict(action=dict(module='shell', args=command_args), register='shell_out'),
                # dict(action=dict(module='shell', args=command_args)),
                dict(action=dict(module='debug', args='var=shell_out.stdout_lines'))
            ]
        )
        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)
        qm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
                # stdout_callback='default',
            )
            result = tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()


    def run_playbook(self,play_book,extra_vars):
        try:
            playbook_path = play_book # modify here, change playbook
            self.inventory
            path = os.getcwd()

            self.variable_manager.extra_vars=extra_vars
            if not os.path.exists(os.path.join(path,playbook_path)):
                sys.exit('[INFO] The playbook does not exist')

            passwords = {}
            executor = PlaybookExecutor(
               playbooks=[playbook_path],
             #    playbooks=['deploy/test.yml'],
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=passwords,
            )
            pass
            # executor._tqm._stdout_callback = self.results_callback
            # code = executor.run()
            # stats = executor._tqm._stats
            # hosts = sorted(stats)
            code = executor.run()
            stats = executor._tqm._stats
            hosts = sorted(stats.processed.keys())
            result = [{h: stats.summarize(h)} for h in hosts]
            results = {'code': code, 'result': result, 'playbook': playbook_path}
            return results

        except Exception as e:
            msg = traceback.format_exc()
            sys.exit(msg)

class Utils(object):
    @staticmethod
    def rsync_command(src,dest,x,delete=False):
        Utils.check_legal_path(src)
        Utils.check_legal_path(dest)
        if not src.endswith('/'):
            src += '/'
        if delete:
            cmd = "rsync -a --delete %s %s" % (src,dest)
        else:
            cmd = "rsync -a %s %s" % (src,dest)
        x.add_row( [cmd])
        return_code = subprocess.call(cmd, shell=True)
        if return_code != 0:
            print(x)
            sys.exit("rsync %s to %s failed !!!" % (src,dest))


    @staticmethod
    def rsync_command_for_config(src,dest,x,delete=False):
        Utils.check_legal_path(src)
        Utils.check_legal_path(dest)
        if not src.endswith('/'):
            src += '/'
        if delete:
            cmd = """rsync -a --delete --exclude ".svn" %s %s""" % (src,dest)
        else:
            cmd = """rsync -a --exclude ".svn" %s %s""" % (src,dest)
        x.add_row( [cmd])
        return_code = subprocess.call(cmd, shell=True)
        if return_code != 0:
            print(x)
            sys.exit("rsync %s to %s failed !!!" % (src,dest))


    @staticmethod
    def check_legal_path(path):
        if re.match(r'.*\s+.*', path) and len(path.strip()<27):
            sys.exit("illegal character: %s" % path)

    @staticmethod
    def unzip_file(file_path,dest):
        cmd = "unzip %s -d %s" % (file_path,dest)
        return_code = subprocess.call(cmd, shell=True)
        if return_code != 0:
            sys.exit("unzip  %s  failed !!!" % (file_path, dest))

    @staticmethod
    def add_version_file(file_path,version):
        try:
            cmd = '''echo %s >  %s/.version''' % (version,file_path)
            print(cmd)
            return_code = subprocess.call(cmd, shell=True)
            if return_code != 0:
                sys.exit("gen version file (%s) failed !!!" % os.path.join(file_path,".version"))


        except Exception as e:
            msg = traceback.format_exc()
            sys.exit(msg)


    @staticmethod
    def md5check(file_path):
        try:
            cmd = '''find %s -type f  ! -path "%s/md5check.txt" -exec md5sum '{}' \;|sort | sed "s#  %s#  .#" >  %s/md5check.txt''' % tuple([file_path for i in range(4)])
            print(cmd)
            return_code = subprocess.call(cmd, shell=True)
            if return_code != 0:
                sys.exit("find  %s  failed !!!" % (file_path))


#            cmd = '''md5sum %s/md5check.txt >  %s/.hmd5c.txt''' % (file_path,file_path)
#            print cmd
#            return_code = subprocess.call(cmd, shell=True)
#            if return_code != 0:
#                sys.exit("gen hiden md5file (%s) failed !!!" % os.path.join(file_path,".hmd5c.txt"))

        except Exception as e:
            msg = traceback.format_exc()
            sys.exit(msg)

        # try:
        #     md5file_path = os.path.join(file_path,'md5check.txt')
        #
        #     cmd = '''find %s -type f   ! -path "%s/md5check.txt"  -exec md5sum '{}' \;|sort | sed "s#  %s#  .#"''' % (file_path,file_path,file_path)
        #     print cmd
        #     p = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE,shell=True)
        #
        #     with open(md5file_path , 'w') as f:
        #         while True:
        #             line = p.stdout.readline()
        #             if line:
        #                 f.write(line)
        #             else:
        #                 break
        #
        #
        #     return_code = p.wait()
        #
        #     if return_code != 0:
        #         sys.exit("find  %s  failed !!!" % (file_path))

        except Exception as e:
            msg = traceback.format_exc()
            sys.exit(msg)

    @staticmethod
    def md5check_for_config(file_path):
        try:
            # cmd = '''find %s -type f -exec md5sum '{}' \;|grep -v '\.svn' | sort | sed "s#  %s#  .#" > %s ''' % (file_path,file_path,md5file_path)
            cmd = '''find %s -type f ! -path '*.svn*' ! -path "%s/md5check.txt" -exec md5sum '{}' \; | sort | sed "s#  %s#  .#" > %s/md5check.txt''' % tuple([file_path for i in range(4)])
            print(cmd)
            return_code = subprocess.call(cmd, shell=True)
            if return_code != 0:
                sys.exit("find  %s  failed !!!" % (file_path))




#            cmd = '''md5sum %s/md5check.txt >  %s/.hmd5c.txt''' % (file_path,file_path)
#            print cmd
#            return_code = subprocess.call(cmd, shell=True)
#            if return_code != 0:
#                sys.exit("gen hiden config md5file (%s) failed !!!" % os.path.join(file_path,".hmd5c.txt"))

        except Exception as e:
            msg = traceback.format_exc()
            sys.exit(msg)


        # try:
        #     # cmd = '''find %s -type f -exec md5sum '{}' \;|grep -v '\.svn' | sort | sed "s#  %s#  .#"''' % (file_path,file_path)
        #     cmd = '''find %s -type f ! -path '*.svn*' -exec md5sum '{}' \; | sort | sed "s#  %s#  .#"''' % (file_path,file_path)
        #     print cmd
        #     p = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE,shell=True)
        #     return_code = p.wait()
        #     if return_code != 0:
        #         sys.exit("find  %s  failed !!!" % (file_path))
        #
        #
        #     md5file_path = os.path.join(file_path,'md5check.txt')
        #     with open(md5file_path , 'w') as f:
        #         f.write(p.stdout.read())
        #
        # except Exception as e:
        #     msg = traceback.format_exc()
        #     sys.exit(msg)


    @staticmethod
    def gen_prod_md5check(file_path):
        try:
            app = os.path.basename(file_path)
            md5file_path = os.path.join(os.path.dirname(file_path),'%s_md5file' % app)
            cmd = '''find %s -type f -exec md5sum '{}' \;|sort | sed "s#  %s#  .#" > %s ''' % (file_path,file_path,md5file_path)
            print(cmd)
            return_code = subprocess.call(cmd, shell=True)
            if return_code != 0:
                sys.exit("find  %s  failed !!!" % (file_path))


            return md5file_path

        except Exception as e:
            msg = traceback.format_exc()
            sys.exit(msg)

    @staticmethod
    def gen_prod_md5check_for_config(file_path):
        try:
            md5file_path = os.path.join(os.path.dirname(file_path),'temp_md5file')
            cmd = '''find %s -type f -exec md5sum '{}' \;|grep -v '\.svn' | sort | sed "s#  %s#  .#" > %s ''' % (file_path,file_path,md5file_path)
            print(cmd)
            return_code = subprocess.call(cmd, shell=True)
            if return_code != 0:
                sys.exit("find  %s  failed !!!" % (file_path))


        except Exception as e:
            msg = traceback.format_exc()
            sys.exit(msg)



    @staticmethod
    def remove_svn_dir(path):
        Utils.check_legal_path(path)
        cmd = 'find %s -type d -name ".svn" | xargs rm -rf' % path
        print(cmd)
        return_code = subprocess.call(cmd, shell=True)
        if return_code != 0:
            sys.exit("remove   %s  .svn directory failed !!!" % (path))

    @staticmethod
    def send_mail(subject,context,sender,receivers):
        # !/usr/bin/python
        # -*- coding: UTF-8 -*-

        import smtplib
        from email.mime.text import MIMEText
        from email.header import Header

        # sender = 'from@runoob.com'
        # receivers = ['429240967@qq.com']  # �����ʼ���������Ϊ���QQ���������������
        # mail_msg = """
        # <p>Python �ʼ����Ͳ���...</p>
        # <p><a href="http://www.runoob.com">����һ������</a></p>
        # """
        # message = MIMEText(context, 'html', 'utf-8')
        # message['From'] = Header(sender, 'utf-8')
        # message['To'] = Header(','.join(receivers), 'utf-8')
        #
        # # subject = 'Python SMTP �ʼ�����'
        # message['Subject'] = Header(subject, 'utf-8')

        # try:
        #     smtpObj = smtplib.SMTP('10.11.0.65')
        #     smtpObj.sendmail(sender, receivers, message.as_string())
        #     print "send successfull"
        # except smtplib.SMTPException as e:
        #     print str(e)
        #     print "Error: send failed"


        msgRoot = MIMEMultipart('related')
        msgRoot['Subject'] = subject
        msgRoot['From'] = sender
        msgRoot['To'] = ','.join(receivers)
        msgRoot.preamble = 'This is a multi-part message in MIME format.'
        # Encapsulate the plain and HTML versions of the message body in an
        # 'alternative' part, so message agents can decide which they want to display.
        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)
        # 设�~Z纯�~V~G�~\�信�~A
        # msgText = MIMEText(plainText, 'plain', 'utf-8')
        # msgAlternative.attach(msgText)
        # 设�~ZHTML信�~A
        msgText = MIMEText(context, 'html', 'utf-8')
        msgAlternative.attach(msgText)
        # 设�~Z�~F~E置�~[��~I~G信�~A
        # fp = open('test.jpg', 'rb')
        # msgImage = MIMEImage(fp.read())
        # fp.close()
        # msgImage.add_header('Content-ID', '<image1>')
        # msgRoot.attach(msgImage)
        # �~O~Q�~@~A�~B�件
        smtp = smtplib.SMTP()
        # 设�~Z�~C�~U级�~H��~L�~]�~C~E�~F��~@~L�~Z
        # smtp.set_debuglevel(1)
        smtp.connect("10.11.0.65")
        # smtp.login(user, passwd)
        smtp.sendmail(sender, receivers, msgRoot.as_string())
        smtp.quit()

    @staticmethod
    def add_change_recorder(app_name,chang_file_path):
        cmd = "echo %s >> %s " % (app_name,chang_file_path)
        print(cmd)
        return_code = subprocess.call(cmd, shell=True)
        if return_code != 0:
            sys.exit("change   %s  failed !!!" % (chang_file_path))

    @staticmethod
    def empty_change_file(chang_file_path):
        Utils.check_legal_path(chang_file_path)
        cmd = "> %s " % (chang_file_path)
        print(cmd)
        return_code = subprocess.call(cmd, shell=True)
        if return_code != 0:
            sys.exit("change   %s  failed !!!" % (chang_file_path))


class ParsePomXml(object):
    def __init__(self, base_dir):
        self.base_dir = base_dir

        self.pom_ns = "{http://maven.apache.org/POM/4.0.0}"
        self.root_pom_path = os.path.join(self.base_dir, 'pom.xml')
        self.tree = ET.parse(self.root_pom_path)
        self.root = self.tree.getroot()
        self.ret_dict= {}

    def parse_child_pom_file(self, module_name):
        module_pom_file_path = os.path.join(
            self.base_dir,
            module_name,
            'pom.xml'
        )

        if os.path.exists(module_pom_file_path):

            module_tree = ET.parse(module_pom_file_path)
            module_root = module_tree.getroot()
            artifact_id_obj = module_root.find("%sartifactId" % self.pom_ns)
            packaging = module_root.find("%spackaging" % self.pom_ns)
            parent = module_root.find("%sparent" % self.pom_ns)
            package_version_obj = parent.find("%sversion" % self.pom_ns)

            descriptor_obj = module_root.find(
                "./%sbuild/%splugins/%splugin/%sexecutions/%sexecution/%sconfiguration/%sdescriptors/%sdescriptor[0]" % (
                    self.pom_ns,
                    self.pom_ns,
                    self.pom_ns,
                    self.pom_ns,
                    self.pom_ns,
                    self.pom_ns,
                    self.pom_ns,
                    self.pom_ns,
                ))
            print(module_pom_file_path)

            if descriptor_obj is not None:
                self.parse_plugin(module_pom_file_path, descriptor_obj.text)
            else:

                artifact_id = artifact_id_obj.text
                package_type = packaging.text
                package_version = package_version_obj.text
                package_name = "%s-%s.%s" % (artifact_id, package_version, package_type)
                print(package_name)

    def check_file_list(self, module_name):
        module_target_file = os.path.join(
            self.base_dir,
            module_name,
            "target"
        )
        war_file_path = glob.glob(r"%s/*.war" % module_target_file)
        zip_file_path = glob.glob(r"%s/*.zip" % module_target_file)

        if zip_file_path:
            # "-".join(s.split('-')[:-1])

            zip_file_path = zip_file_path[0]
            zip_file_name = os.path.basename(zip_file_path)
            dir_name = "-".join(zip_file_name.split('-')[:-1])

            unzip_module_path = os.path.join(
                os.path.dirname(zip_file_path),
                dir_name
            )

            if os.path.exists(unzip_module_path):
                Utils.check_legal_path(unzip_module_path)
                shutil.rmtree(unzip_module_path)
                print('remove %s' % unzip_module_path)

            f = zipfile.ZipFile(zip_file_path)
            f.extractall(path=os.path.dirname(zip_file_path))
            f.close()
            print("unzip %s to\n%s" % (zip_file_path,os.path.dirname(zip_file_path)))

            self.ret_dict[module_name]= unzip_module_path
        if  war_file_path:
            war_file_path = war_file_path[0]
            unzip_module_path = os.path.splitext(war_file_path)[0]
            if  os.path.exists(unzip_module_path):
                Utils.check_legal_path(unzip_module_path)
                shutil.rmtree(unzip_module_path)
                print('remove %s' % unzip_module_path)


            os.mkdir(unzip_module_path)

            f = zipfile.ZipFile(war_file_path)
            f.extractall(path=unzip_module_path)
            f.close()
            print("unzip %s to\n%s" % (war_file_path,unzip_module_path))
            self.ret_dict[module_name]= unzip_module_path

    def get_all_file_list(self):

        for child in self.root.getiterator('%smodule' % (self.pom_ns)):
            # self.ret_dict[child.text] = []
            self.check_file_list(child.text)


        return self.ret_dict

class DeployHandler(object):
    # def __init__(self,envid,job_type,depapps,job_name,deploy_type,config):
    def __init__(self,**kwargs):
        self.envid = kwargs['envid']
    #    self.job_id = kwargs['job_id']
        self.job_type = kwargs['job_type']
        self.depapps = kwargs['depapps']
        # self.project = kwargs['project']
        # self.version = kwargs['version']
        # self.job_name = kwargs['job_name']
        # self.job_name = os.path.basename(os.path.abspath('.'))
        self.job_name = 'job22'
        # self.deploy_type = kwargs['deploy_type']
        self.package_file = kwargs['package_file']
        self.build_number = kwargs['build_number']
        self.command_args = kwargs['command_args']
        self.mavenbase = kwargs['mavenbase']
        self.is_jar = kwargs['is_jar']
        self.ant = kwargs['ant']
        # self.config_file_dir = os.path.join("../deploy",kwargs['config'])
        # self.config_file_dir = os.path.abspath(self.config_file_dir)
        self.DEBUG = kwargs['debug']
        self.production = kwargs['production']
        self.api_server = 'http://10.12.12.157:8000'
        self.ansible_inventory_api = urljoin(self.api_server,"/api/hostrel/?format=json")
        self.job_detail_api = urljoin(self.api_server,"/api/jkjob/?job_name=job22&jenkins_server_id=1")
        self.headers = {"Authorization":"Token b5b4451ed9f917c6c09ea6bbbe3d65f931bb2a0e"}
        self.redis_host = "127.0.0.1"
        self.redis_port = 6379
        self.mailtype = kwargs['mailtype']
        self.src_job_dir = kwargs['src_job_dir']
        self.admin_mail = "ITappdatamanagement@tjpme.com"
        self.jenkins_server_id = '1'
        self.last_fun_successful_dir = 'fun_s'
        self.last_uat_successful_dir = 'uat_s'

        self.config_dic = {
            'java_app_template_path':'roles/javaapps/templates',
            'web_app_template_path':'roles/webapps/templates',
            'java_app_file_path':'roles/javaapps/files',
            'web_app_file_path':'roles/webapps/files'
        }




        self.r = redis.Redis(host=self.redis_host, port=self.redis_port)

        # payload = {
        #     "envid" : self.envid,
        #     # "project" : self.project,
        #     # "version" : self.version,
        #     "apps" : self.depapps,
        #     "job_type" : self.job_type,
        #     "job_name":self.job_name,
        #     "jenkins_server_id":self.jenkins_server_id
        #     # "job_name"
        # }
        inventory_payload = {
                'environment__environment_name': self.envid,
                'job_name':'job22',
                'jenkins_server_id':self.jenkins_server_id
            }
        job_detail_payload = {
                'job_name':'job22',
                'jenkins_server_id':self.jenkins_server_id
            }
        try:
            r = requests.get(self.ansible_inventory_api,params=inventory_payload,headers=self.headers)
            if self.job_type != "getmail":
                print(r.url)
            self.inventory_list = r.json()

            r = requests.get(self.job_detail_api,params=job_detail_payload,headers=self.headers)
            job_detail_list = r.json()

            if self.DEBUG:
                print(self.inventory_list)
                print(job_detail_list)

            if not self.inventory_list or not job_detail_list :
                sys.exit()
            self.job_detail_dict = job_detail_list.pop()
            self.project = self.job_detail_dict['project']['name']
            self.version = self.job_detail_dict['project']['version']['name']
            if self.job_detail_dict['job_type'] == 0:
                self.deploy_type = 'fun'
            elif self.job_detail_dict['job_type'] == 1:
                self.deploy_type = 'uat'
            else:
                self.deploy_type = None


            self.app_full_name = '%s_%s' % (self.project,self.version)
            self.app_full_config_name = '%s_config' % self.app_full_name

            self.change_redis_key = "%s_change" % self.app_full_name
            self.changeall_redis_key = "%s_changeall" % self.app_full_name

            self.base_dir = self.job_detail_dict['jenkins_server']['workspace']
            os.chdir(self.base_dir)
        except Exception as e:
            print(traceback.format_exc())
            sys.exit(1)


        self.javaapps = [i['group']['name'] for i in self.inventory_list if i['group_type'] == 'javaapps']
        self.webapps = [i['group']['name'] for i in self.inventory_list if i['group_type'] == 'webapps']
        self.allapp_list = [ i['group']['name'] for i in self.inventory_list ]

        self.job_workspace = os.path.join(self.base_dir, self.job_name)

        # file_list = ['javaapps.yml','roles','tomcat.yml','webapps.yml']
        #
        # ret_list = list(map(lambda x: os.path.exists(os.path.join(self.job_workspace, x)), file_list))
        #
        # if not any(ret_list):
        #     ansible_role_tempate = os.path.join(self.base_dir,'ansible_role_template')
        #     x = PrettyTable(["init job workspace "])
        #     Utils.rsync_command(ansible_role_tempate,self.job_workspace,x)

        self.html = '''
    <HTML>
    <HEAD>
        <META content="text/html; charset=utf-8" http-equiv=Content-Type>
        <META name=GENERATOR content="MSHTML 8.00.7601.17514">
    </HEAD>
    <BODY>
    <HR>
    (本邮件是程序自动下发的，请勿回复！)
    <HR>
    项目名称：{{ job_name }}
    <HR>
    变更集:
    <STYLE>BODY {
        FONT-FAMILY: Verdana, Helvetica, sans serif;
        COLOR: black;
        FONT-SIZE: 11px
    }

    TABLE {
        FONT-FAMILY: Verdana, Helvetica, sans serif;
        COLOR: black;
        FONT-SIZE: 11px
    }

    TD {
        FONT-FAMILY: Verdana, Helvetica, sans serif;
        COLOR: black;
        FONT-SIZE: 11px
    }

    TH {
        FONT-FAMILY: Verdana, Helvetica, sans serif;
        COLOR: black;
        FONT-SIZE: 11px
    }

    P {
        FONT-FAMILY: Verdana, Helvetica, sans serif;
        COLOR: black;
        FONT-SIZE: 11px
    }

    H1 {
        COLOR: black
    }

    H2 {
        COLOR: black
    }

    H3 {
        COLOR: black
    }

    TD.bg1 {
        BACKGROUND-COLOR: #0000c0;
        COLOR: white;
        FONT-SIZE: 120%
    }

    TD.bg2 {
        BACKGROUND-COLOR: #4040ff;
        COLOR: white;
        FONT-SIZE: 110%
    }

    TD.bg3 {
        BACKGROUND-COLOR: #8080ff;
        COLOR: white
    }

    TD.test_passed {
        COLOR: blue
    }

    TD.test_failed {
        COLOR: red
    }

    TD.console {
        FONT-FAMILY: Courier New
    }
    </STYLE>


    <BR>
    <TABLE width="100%">
        <TBODY>
            <TR>
                <TD class=bg1 colSpan=2><B>&nbsp;envid : ({{ envid }})</B></TD>
            </TR>

        {% for module_info in ret_list %}
            <TR>
                <TD class=bg1 colSpan=2><B>&nbsp;模块名:({{ module_info.module_name }})</B></TD>
            </TR>

            {% for comment in module_info.comments %}
            <TR>
                <TD class=bg2 colSpan=2>&nbsp;&nbsp;version : <B>{{ comment.revision }}</B>
                    </TD>
            </TR>
            <TR>
                <TD width="10%">&nbsp;&nbsp;comments :   </TD>
                <TD>{{ comment.msg }}</TD>
            </TR>
            {% endfor %}
        {% endfor %}
        </TBODY>
    </TABLE>
    <BR>
    <HR>
    </BODY>
    </HTML>
    '''


        self.job_mail_html = u"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title>{{ job_name }}-第{{build_number}}次构建日志</title>
        </head>

        <body leftmargin="8" marginwidth="0" topmargin="8" marginheight="4"
            offset="0">
            <table width="95%" cellpadding="0" cellspacing="0"
                style="font-size: 11pt; font-family: Tahoma, Arial, Helvetica, sans-serif">
                <tr>
                    <td>(本邮件是程序自动下发的，请勿回复！)</td>
                </tr>
                <tr>
                    <td><h2>
                            <font color="#0000FF">构建结果 - {{ build_status }}</font>
                        </h2></td>
                </tr>
                <tr>
                    <td><br />
                    <b><font color="#0B610B">构建信息</font></b>
                    <hr size="2" width="100%" align="center" /></td>
                </tr>
                <tr>
                    <td>
                        <ul>
                            <li>项目名称 ： {{ job_name }}</li>
                            {% if action != "build" %}
        					    <li>部署的应用 : {{deployapps}} </li>
                            {% endif %}
                            <li>构建编号 ： 第{{ build_number }}次构建</li>
                            <li>触发原因： {{ cause }}</li>
                            <li>构建日志： <a href="{{ build_url }}console">{{ build_url }}console</a></li>
                            {% if action == "build" %}

                                <li>SVN  URL ： <a href="{{svn_url}}">{{svn_url}}</a></li>
                                <li>SVN  号 ： <a href="{{svn_version}}">{{svn_version}}</a></li>
                            {% endif %}

                        </ul>
                    </td>
                </tr>



            </table>
        </body>
        </html>
        """

    def get_jenkins_server(self):
        url = self.job_detail_dict['jenkins_server']['api_url']
        username = self.job_detail_dict['jenkins_server']['username']
        password = self.job_detail_dict['jenkins_server']['token']
        server = jenkins.Jenkins(url, username=username, password=password)


        return server


    def check_all_dirs(self):

        # if not os.path.exists(self.host_file_path):
        #     sys.exit("hosts file %s not exist !" % self.host_file_path)
        #
        # if not os.path.exists(self.group_var_path):
        #     sys.exit("group vars file %s not exist !" % self.group_var_path)

        if not self.production:

            self.full_last_fun_successful_dir = os.path.join(
                    self.base_dir,
                    self.last_fun_successful_dir,
                    self.app_full_name
                )

            if not os.path.exists(self.full_last_fun_successful_dir):
                try:
                    print('mkdirs %s' % self.full_last_fun_successful_dir)
                    os.makedirs(self.full_last_fun_successful_dir)
                except Exception as e:
                    msg = traceback.format_exc()
                    sys.exit(msg)



            self.full_last_fun_config_successful_dir = os.path.join(
                self.base_dir,
                self.last_fun_successful_dir,
                self.app_full_config_name
            )

            if not os.path.exists(self.full_last_fun_config_successful_dir):
                try:
                    print('mkdirs %s' % self.full_last_fun_config_successful_dir)

                    os.makedirs(self.full_last_fun_config_successful_dir)
                except Exception as e:
                    msg = traceback.format_exc()
                    sys.exit(msg)


            self.full_last_uat_successful_dir = os.path.join(
                self.base_dir,
                self.last_uat_successful_dir,
                self.app_full_name
            )


            if not os.path.exists(self.full_last_uat_successful_dir):
                try:
                    print('mkdirs %s' % self.full_last_uat_successful_dir)

                    os.makedirs(self.full_last_uat_successful_dir)
                except Exception as e:
                    msg = traceback.format_exc()
                    sys.exit(msg)



            self.full_last_uat_config_successful_dir = os.path.join(
                self.base_dir,
                self.last_uat_successful_dir,
                self.app_full_config_name
            )


            if not os.path.exists(self.full_last_uat_config_successful_dir):
                try:
                    print('mkdirs %s' % self.full_last_uat_config_successful_dir)

                    os.makedirs(self.full_last_uat_config_successful_dir)
                except Exception as e:
                    msg = traceback.format_exc()
                    sys.exit(msg)



        self.builds_dir = os.path.join(self.base_dir,"builds")
        if not os.path.exists(self.builds_dir):
            try:
                os.makedirs(self.builds_dir)
                print('create builds dir %s' % self.builds_dir)
            except Exception as e:
                msg = traceback.format_exc()
                sys.exit(msg)


        self.project_dir = os.path.join(self.builds_dir,self.app_full_name)
        if not os.path.exists(self.project_dir):
            try:
                os.makedirs(self.project_dir)
                print('create project dir %s' % self.project_dir)
            except Exception as e:
                msg = traceback.format_exc()
                sys.exit(msg)

        self.project_config_dir = os.path.join(self.builds_dir, self.app_full_config_name)
        if not os.path.exists(self.project_config_dir):
            try:
                os.makedirs(self.project_config_dir)
                print('create project config dir %s' % self.project_config_dir)
            except Exception as e:
                msg = traceback.format_exc()
                sys.exit(msg)


    def check_app(self):
        if not self.envid:
            sys.exit(" --envid can't empty")
        if not self.depapps == 'all':
            if not self.depapps:
                sys.exit(" --depapps can't empty")


            app_list = self.depapps.split(",")

            for app in app_list:
                if not app in self.allapp_list:
                    sys.exit("illegal app : %s" % app)

    def sync_javaapps(self,app_name):
        #sync the javaapp file to
        if self.deploy_type=='fun':
            #backup code to last fun successfuall
            role_file_path = os.path.join(self.job_name, self.config_dic['java_app_file_path'], app_name)
            if not role_file_path.endswith('/'):
                role_file_path += '/'

            last_fun_successful_dir_path = os.path.join(self.full_last_fun_successful_dir, app_name)
            x = PrettyTable([app_name+"(BACKUP JAVAAPPS FUNCTION TEST)"])

            msg = 'BACKUP LAST SUCCESSFUL JAVAAPPS (FUNCTION TEST)\n FROM (%s) TO (%s)' % (role_file_path, last_fun_successful_dir_path)
            x.add_row([msg])
            if os.path.exists(role_file_path):
                Utils.rsync_command(role_file_path, last_fun_successful_dir_path,x,delete=True)


            print

            #backup config file to last fun successfuall
            role_config_path = os.path.join(self.job_name, os.path.join(self.config_dic['java_app_template_path'], app_name))

            if not role_config_path.endswith('/'):
                role_config_path += '/'
            last_fun_config_successful_dir_path = os.path.join(self.full_last_fun_config_successful_dir, app_name)

            msg = 'BACKUP LAST SUCCESSFUL JAVAAPPS (FUNCTION TEST) CONFIG \nFROM (%s) TO (%s)' % (role_config_path, last_fun_config_successful_dir_path)
            x.add_row([msg])

            if os.path.exists(role_config_path):
                Utils.rsync_command(role_config_path, last_fun_config_successful_dir_path,x,delete=True)
            print(x)





        elif self.deploy_type=='uat':
            #backup code to uat last successfull
            role_file_path = os.path.join(self.job_name, self.config_dic['java_app_file_path'], app_name)
            if not role_file_path.endswith('/'):
                role_file_path += '/'
            last_uat_successful_dir_path = os.path.join(self.full_last_uat_successful_dir, app_name)
            x = PrettyTable([app_name+"(BACKUP JAVAAPPS UAT TEST)"])

            msg = 'BACKUP LAST SUCCESSFUL JAVAAPPS (UAT TEST)\n FROM (%s) TO (%s)' % (role_file_path, last_uat_successful_dir_path)
            x.add_row([msg])
            if os.path.exists(role_file_path):
                Utils.rsync_command(role_file_path, last_uat_successful_dir_path,x,delete=True)
            # backup config file to last uat successfuall
            role_config_path = os.path.join(self.job_name,
                                            os.path.join(self.config_dic['java_app_template_path'], app_name))

            if not role_config_path.endswith('/'):
                role_config_path += '/'
            last_uat_config_successful_dir_path = os.path.join(self.full_last_uat_config_successful_dir, app_name)

            msg = 'BACKUP LAST SUCCESSFUL JAVAAPPS (UAT TEST) CONFIG \nFROM (%s) TO (%s)' % (
            role_config_path, last_uat_config_successful_dir_path)
            x.add_row([msg])
            if os.path.exists(role_config_path):
                Utils.rsync_command(role_config_path, last_uat_config_successful_dir_path, x,delete=True)
            print(x)





            # fun_role_path = os.path.join(self.builds_dir, self.app_full_name, app_name)
            fun_role_path = os.path.join(self.config_dic['fun_job_name'], self.config_dic['java_app_file_path'], app_name)
            if not fun_role_path.endswith('/'):
                fun_role_path += '/'

            app_role_file_path = os.path.join(self.job_name, os.path.join(self.config_dic['java_app_file_path'], app_name))
            x = PrettyTable([app_name + "(COPY JAVAAPPS CODE TO ANSIBLE ROLE)"])

            msg = 'FROM FUN TEST JAVAAPPS (%s) TO (%s)' % (fun_role_path, app_role_file_path)
            x.add_row([msg])
            Utils.rsync_command(fun_role_path, app_role_file_path, x,delete=True)


            # app_config_builds_path = os.path.join(os.path.join(self.builds_dir, self.app_full_config_name), app_name)
            fun_role_config__path = os.path.join(self.config_dic['fun_job_name'], self.config_dic['java_app_template_path'], app_name)
            if not fun_role_config__path.endswith('/'):
                fun_role_config__path += '/'
            app_role_config_path = os.path.join(self.job_name, self.config_dic['java_app_template_path'], app_name)
            msg = 'FROM FUN TEST CONFIG JAVAAPPS (%s) TO (%s)' % (fun_role_config__path, app_role_config_path)
            x.add_row([msg])

            Utils.rsync_command(fun_role_config__path, app_role_config_path,x, delete=True)
            print(x)

        if self.deploy_type!='uat':

            if self.src_job_dir and os.path.exists(self.src_job_dir):
                # backup code to uat last successfull

                # fun_role_path = os.path.join(self.builds_dir, self.app_full_name, app_name)
                src_role_path = os.path.join(self.src_job_dir, self.config_dic['java_app_file_path'],
                                             app_name)
                if not src_role_path.endswith('/'):
                    src_role_path += '/'

                app_role_file_path = os.path.join(self.job_name,
                                                  os.path.join(self.config_dic['java_app_file_path'], app_name))
                x = PrettyTable([app_name + "(COPY JAVAAPPS CODE TO ANSIBLE ROLE)"])

                msg = 'FROM JAVA APP JOB %s (%s) TO (%s)' % (self.src_job_dir, src_role_path, app_role_file_path)
                x.add_row([msg])
                Utils.rsync_command(src_role_path, app_role_file_path, x, delete=True)

                # app_config_builds_path = os.path.join(os.path.join(self.builds_dir, self.app_full_config_name), app_name)
                src_role_config_path = os.path.join(self.src_job_dir, self.config_dic['java_app_template_path'], app_name)
                if not src_role_config_path.endswith('/'):
                    src_role_config_path += '/'
                app_role_config_path = os.path.join(self.job_name, self.config_dic['java_app_template_path'], app_name)
                msg = 'FROM  JAVA APP CONFIG %s JAVAAPPS (%s) TO (%s)' % (
                self.src_job_dir, src_role_config_path, app_role_config_path)
                x.add_row([msg])

                Utils.rsync_command(src_role_config_path, app_role_config_path, x, delete=True)
                print(x)

            else:
                app_builds_path = os.path.join(os.path.join(self.builds_dir, self.app_full_name), app_name)
                if not app_builds_path.endswith('/'):
                    app_builds_path += '/'
    
                app_role_file_path = os.path.join(self.job_name, os.path.join(self.config_dic['java_app_file_path'], app_name))
                x = PrettyTable([app_name + "(COPY JAVAAPPS CODE TO ANSIBLE ROLE)"])
    
                msg = 'FROM BUILDS JAVAAPPS (%s) TO (%s)' % (app_builds_path, app_role_file_path)
                x.add_row([msg])
                Utils.rsync_command(app_builds_path, app_role_file_path, x,delete=True)
    
                app_config_builds_path = os.path.join(os.path.join(self.builds_dir, self.app_full_config_name), app_name)
                if not app_config_builds_path.endswith('/'):
                    app_config_builds_path += '/'
                app_role_config_path = os.path.join(self.job_name, os.path.join(self.config_dic['java_app_template_path'], app_name))
                msg = 'FROM BUILDS JAVAAPPS (%s) TO (%s)' % (app_config_builds_path, app_role_config_path)
                x.add_row([msg])
    
                Utils.rsync_command(app_config_builds_path, app_role_config_path,x, delete=True)
                print(x)
    

    def sync_webapps(self,web_name):
        #sync the javaapp file to
        if self.deploy_type=='fun':
            #backup code to last fun successfuall
            role_file_path = os.path.join(self.job_name, os.path.join(self.config_dic['web_app_file_path'], web_name))
            if not role_file_path.endswith('/'):
                role_file_path += '/'

            last_fun_successful_dir_path = os.path.join(self.full_last_fun_successful_dir, web_name)
            x = PrettyTable([web_name+"(BACKUP WEBAPPS FUNCTION TEST)"])

            msg = 'BACKUP LAST SUCCESSFUL WEBAPPS (FUNCTION TEST)\n FROM (%s) TO (%s)' % (role_file_path, last_fun_successful_dir_path)
            x.add_row([msg])
            # print x
            if os.path.exists(role_file_path):
                Utils.rsync_command(role_file_path, last_fun_successful_dir_path,x,delete=True)

            #backup config file to last fun successfuall
            role_config_path = os.path.join(self.job_name, self.config_dic['web_app_template_path'], web_name)

            if not role_config_path.endswith('/'):
                role_config_path += '/'
            last_fun_config_successful_dir_path = os.path.join(self.full_last_fun_config_successful_dir, web_name)
            # x = PrettyTable([web_name])
            msg = 'BACKUP LAST SUCCESSFUL WEBAPPS (FUNCTION TEST) CONF\n FROM (%s) TO (%s)' % (role_config_path, last_fun_config_successful_dir_path)
            x.add_row([msg])
            if os.path.exists(role_config_path):
                Utils.rsync_command(role_config_path, last_fun_config_successful_dir_path,x,delete=True)
            print(x)


        elif self.deploy_type=='uat':
            #backup code to uat last successfull
            role_file_path = os.path.join(self.job_name, os.path.join(self.config_dic['web_app_file_path'], web_name))
            if not role_file_path.endswith('/'):
                role_file_path += '/'
            last_uat_successful_dir_path = os.path.join(self.full_last_uat_successful_dir, web_name)
            x = PrettyTable([web_name+"(BACKUP WEBAPPS UAT TEST)"])

            msg = 'BACKUP LAST SUCCESSFUL WEBAPPS (UAT TEST)\n FROM (%s) TO (%s)' % (role_file_path, last_uat_successful_dir_path)
            x.add_row([msg])
            if os.path.exists(role_file_path):
                Utils.rsync_command(role_file_path, last_uat_successful_dir_path,x,delete=True)
            # backup config file to last uat successfuall
            role_config_path = os.path.join(self.job_name,
                                           self.config_dic['web_app_template_path'], web_name)

            if not role_config_path.endswith('/'):
                role_config_path += '/'
            last_uat_config_successful_dir_path = os.path.join(self.full_last_uat_config_successful_dir, web_name)

            msg = 'BACKUP LAST SUCCESSFUL WEBAPPS (UAT TEST) CONFIG \nFROM (%s) TO (%s)' % (
            role_config_path, last_uat_config_successful_dir_path)
            x.add_row([msg])
            if os.path.exists(role_config_path):
                Utils.rsync_command(role_config_path, last_uat_config_successful_dir_path, x,delete=True)
            print(x)




            print

            # app_builds_path = os.path.join(os.path.join(self.builds_dir, self.app_full_name), web_name)


            fun_role_file_path = os.path.join(self.config_dic['fun_job_name'], self.config_dic['web_app_file_path'], web_name)



            if not fun_role_file_path.endswith('/'):
                fun_role_file_path += '/'
            app_role_file_path = os.path.join(self.job_name, self.config_dic['web_app_file_path'], web_name)
            x = PrettyTable([web_name + "(COPY FUN TEST CODE TO ANSIBLE ROLE)"])

            msg = 'FROM FUN TEST DIR (%s) TO (%s)' % (fun_role_file_path, app_role_file_path)
            x.add_row([msg])

            Utils.rsync_command(fun_role_file_path, app_role_file_path,x, delete=True)

            # print

            # app_config_builds_path = os.path.join(os.path.join(self.builds_dir, self.app_full_config_name), web_name)
            fun_config_builds_path = os.path.join(self.job_detail_dict['project']['fun_job_name'], self.config_dic['web_app_template_path'], web_name)
            if not fun_config_builds_path.endswith('/'):
                fun_config_builds_path += '/'
            app_role_config_path = os.path.join(self.job_name, os.path.join(self.config_dic['web_app_template_path'], web_name))
            msg = 'FROM FUN TEST CONFIG (%s) TO (%s)' % (fun_config_builds_path, app_role_config_path)
            x.add_row([msg])

            Utils.rsync_command(fun_config_builds_path, app_role_config_path,x, delete=True)
            print(x)


        if self.deploy_type != 'uat':

            if self.src_job_dir and os.path.exists(self.src_job_dir):

                src_role_file_path = os.path.join(
                    self.src_job_dir,
                    self.config_dic['web_app_file_path'],
                    web_name
                )

                if not src_role_file_path.endswith('/'):
                    src_role_file_path += '/'
                app_role_file_path = os.path.join(self.job_name,
                                                  self.config_dic['web_app_file_path'], web_name)
                x = PrettyTable([web_name + "(COPY  WEBAPP JOB %s CODE TO ANSIBLE ROLE)" % self.src_job_dir])

                msg = 'FROM WEBAPP JOB (%s) DIR (%s) TO (%s)' % (self.src_job_dir, src_role_file_path, app_role_file_path)
                x.add_row([msg])

                Utils.rsync_command(src_role_file_path, app_role_file_path, x, delete=True)

                # print

                # app_config_builds_path = os.path.join(os.path.join(self.builds_dir, self.app_full_config_name), web_name)
                src_config_builds_path = os.path.join(
                    self.src_job_dir,
                    self.config_dic['web_app_template_path'],
                    web_name
                )
                if not src_config_builds_path.endswith('/'):
                    src_config_builds_path += '/'
                app_role_config_path = os.path.join(self.job_name,
                                                   self.config_dic['web_app_template_path'], web_name)
                msg = 'FROM  WEBAPP JOB (%s) CONFIG (%s) TO (%s)' % (self.src_job_dir, src_config_builds_path, app_role_config_path)
                x.add_row([msg])

                Utils.rsync_command(src_config_builds_path, app_role_config_path, x, delete=True)
                print(x)


    #-----------------------------
            else:

                app_builds_path = os.path.join(self.builds_dir, self.app_full_name, web_name)
                if not app_builds_path.endswith('/'):
                    app_builds_path += '/'
                app_role_file_path = os.path.join(self.job_name,
                                                  self.config_dic['web_app_file_path'], web_name)
                x = PrettyTable([web_name + "(COPY WEBAPPS CODE TO ANSIBLE ROLE)"])
    
                msg = 'FROM BUILDS (%s) TO (%s)' % (app_builds_path, app_role_file_path)
                x.add_row([msg])
    
                Utils.rsync_command(app_builds_path, app_role_file_path, x, delete=True)
    
                # print
    
                app_config_builds_path = os.path.join(self.builds_dir, self.app_full_config_name, web_name)
                if not app_config_builds_path.endswith('/'):
                    app_config_builds_path += '/'
                app_role_config_path = os.path.join(self.job_name,
                                                    self.config_dic['web_app_template_path'], web_name)
                msg = 'FROM BUILDS (%s) TO (%s)' % (app_config_builds_path, app_role_config_path)
                x.add_row([msg])
    
                Utils.rsync_command(app_config_builds_path, app_role_config_path, x, delete=True)
                print(x)
    

    def sync_file_and_config(self):
        if self.job_type not in ['mnmd5check','promd5check']:

            change_apps = self.r.smembers(self.change_redis_key)
            # self.changelog_file_path = os.path.join(self.changelog_dir,'change')
            # if os.path.isfile(self.changelog_file_path):
            #     try:
            #         print 'copy %s to %s' % (self.changelog_file_path,self.last_fun_successful_dir)
            #         shutil.copy(self.changelog_file_path,self.last_fun_successful_dir)
            #     except Exception as e:
            #         msg = traceback.format_exc()
            #         sys.exit(msg)
            with open(os.path.join(self.full_last_fun_successful_dir,'change'),'w') as f:
                for l in change_apps:
                    f.write("%s\n" % l)


            # javaapps = self.config_dic['javaapps']
            # webapps = self.config_dic['webapps']
        changeall_list = list(self.r.smembers(self.changeall_redis_key))
        change_list = self.r.smembers(self.change_redis_key)
        if self.depapps == 'all':
            for app_name in self.javaapps:
                print
                # print app_name.upper()
                if self.deploy_type=='uat':
                    if app_name not in changeall_list:
                        sys.exit("app (%s) not in changeall list , if you want to deploy UAT please check !" % app_name)
                elif self.deploy_type == 'fun':
                    if app_name not in change_list:
                        sys.exit("app (%s) not in change list , if you want to deploy FUN please check !" % app_name)
                self.sync_javaapps(app_name)
            for web_name in self.webapps:
                print
                # print app_name.upper()
                if self.deploy_type=='uat':
                    if app_name not in changeall_list:
                        sys.exit("app (%s) not in changeall list , if you want to deploy UAT please check !" % app_name)
                elif self.deploy_type == 'fun':
                    if app_name not in change_list:
                        sys.exit("app (%s) not in change list , if you want to deploy FUN please check !" % app_name)

                self.sync_webapps(web_name)


        else:
            depapps_list = self.depapps.split(',')
            for app in depapps_list:
                if app in self.javaapps:
                    '''
                    if self.deploy_type=='uat':
                        if app not in changeall_list:
                            sys.exit("app (%s) not in changeall list , if you want to deploy UAT please check !" % app)
                    elif self.deploy_type == 'fun':
                        if app not in change_list:
                            sys.exit("app (%s) not in change list , if you want to deploy FUN please check !" % app)
                    '''

                    self.sync_javaapps(app)
                elif app in self.webapps:
                    if self.deploy_type=='uat':
                        if app not in changeall_list:
                            sys.exit("app (%s) not in changeall list , if you want to deploy UAT please check !" % app)
                    elif self.deploy_type == 'fun':
                        if app not in change_list:
                            sys.exit("app (%s) not in change list , if you want to deploy FUN please check !" % app)
                    self.sync_webapps(app)

        #if self.deploy_type == 'fun':


            # change_redis_key = "%s_change" % self.app_full_name
            # changeall_redis_key = "%s_changeall" % self.app_full_name
            # print "add change reocder(%s) into redis" % app_name
         #   self.r.delete(self.change_redis_key)
    def run_playbook(self,playbook,tag,extra_vars,msg,inventory,hostname=None):

        # if not os.path.exists(self.host_file_path):
        #     msg = "don't exist file (%s)" % self.host_file_path
        #     sys.exit(msg)
        # if not os.path.exists(self.group_var_path):
        #     msg = "don't exist file (%s)" % self.group_var_path
        #     sys.exit(msg)
        print
        print(msg)
        ansible_handler = AnsibleApi2(inventory, tag,hostname=hostname)
        ret = ansible_handler.run_playbook(playbook, extra_vars)
        # print ret
        if self.DEBUG:
            print(playbook)
            print(tag)
            print(extra_vars)
            print(ret)
        if ret['code'] != 0:
            sys.exit(1)


    def run_module(self,msg):

        if not os.path.exists(self.host_file_path):
            msg = "don't exist file (%s)" % self.host_file_path
            sys.exit(msg)
        if not os.path.exists(self.group_var_path):
            msg = "don't exist file (%s)" % self.group_var_path
            sys.exit(msg)
        print
        print(msg)
        ansible_handler = AnsibleApi2(self.host_file_path, self.group_var_path, None)
        if self.depapps == 'all':
            for app in self.webapps.keys():
                    # print 'deploy tomcat'
                ansible_handler.run_model(self.command_args,app)


        else:
            depapps_list = self.depapps.split(',')
            for app in depapps_list:
                ansible_handler.run_model(self.command_args,app)

        # ansible_handler.run_model(self.command_args,self.depapps)
        # print ret
        # if self.DEBUG:
        #     print playbook
        #     print tag
        #     print extra_vars
        #     print ret
        # if ret['code'] != 0:
        #     sys.exit(1)



    def deploy_tomcat(self,app):
        play_book = '%s/%s' % (self.job_name, 'tomcat.yml')
        extra_vars = {
            'rolename': app,
            'deploypath': self.config_dic['webapps'][app]['tomcatname']
        }
        msg = "install the tomcat service on %s !" % app
        tag = 'deploy'
        print('install tomcat ,extra  var',extra_vars)
        self.run_playbook(play_book, tag, extra_vars, msg)

    def config_tomcat(self,app):
        play_book = '%s/%s' % (self.job_name, 'tomcat.yml')

        extra_vars = {
            'rolename': app,
            'deploypath': self.config_dic['webapps'][app]['tomcatname'],
            'jvmsize': self.config_dic['webapps'][app]['jvm_size'],
            'shutport': self.config_dic['webapps'][app]['shut_port'],
            'httpport': self.config_dic['webapps'][app]['http_port'],
            'httpsport': self.config_dic['webapps'][app]['https_port'],
        }
        if self.webapps[app]['http_type'] == 'http':
            tag = 'httpconfig'
        elif self.webapps[app]['http_type'] == 'https':
            tag = 'httpsconfig'

        msg = "configration the tomcat service on %s !" % app
        print(extra_vars,'config tomcate template')

        self.run_playbook(play_book, tag, extra_vars, msg)




    def deploy_and_config_tomcat(self,app):
        for r in self.inventory_list:
            if r['group']['name'] == app:
                tomcat_info = r['tomcat']
                play_book = '%s/%s' % (self.job_name, 'tomcat.yml')

                extra_vars = {
                    'rolename': app,
                    'deploypath': tomcat_info['name'],
                    'jvmsize': tomcat_info['jvm_size'],
                    'shutport': tomcat_info['shutdown_port'],
                    'httpport': tomcat_info['http_port'],
                    'httpsport': tomcat_info['https_port'],
                }
                if tomcat_info['http_type'] == 'http':
                    tag = 'deploy_and_config_http'
                elif tomcat_info['http_type']  == 'https':
                    tag = 'deploy_and_config_https'

                msg = "configration the tomcat service on %s !" % app
                print(extra_vars, 'config tomcate template')
                self.run_playbook(play_book, tag, extra_vars, msg,r)
    def tomcat(self):
        if self.depapps == 'all':
            for app in self.webapps:
                if app in self.webapps:
                    # print 'deploy tomcat'
                    self.deploy_and_config_tomcat(app)

        else:
            depapps_list = self.depapps.split(',')
            for app in depapps_list:
                if app in self.webapps:
                    self.deploy_and_config_tomcat(app)



    def stop_web_app(self,app):
        for r in self.inventory_list:
            if r['group']['name'] == app:
                play_book = '%s/%s' % (self.job_name, 'webapps.yml')

                extra_vars = {
                    'rolename': app,
                    'deploypath': r['tomcat']['name'],
                }

                tag='stop'
                msg = "stop tomcat service on %s(%s) !" % (app,extra_vars['deploypath'])

                self.run_playbook(play_book,tag,extra_vars,msg,r)

    def stop_java_app(self,app):
        for r in self.inventory_list:
            play_book = '%s/%s' % (self.job_name, 'javaapps.yml')
            for appfoot in r['app_foot']:
                extra_vars = {
                    'hostname': "%s_%s" % (app,str(appfoot)),
                    'rolename': app,
                }

                tag='stop'

                msg = "stop java service on %s !" % extra_vars['hostname']

                self.run_playbook(play_book, tag, extra_vars, msg,r,hostname= extra_vars['hostname'])

    def stop(self):
        if self.depapps == 'all':
            for app in self.allapp_list:
                if app in self.webapps:
                    self.stop_web_app(app)
                elif app in self.javaapps:
                    self.stop_java_app(app)
        else:
            depapps_list = self.depapps.split(',')
            for app in self.allapp_list:
                if app in depapps_list:
                    if app in self.webapps.keys():
                        self.stop_web_app(app)
                    if app in self.javaapps.keys():
                        self.stop_java_app(app)

    def start_web_app(self,app):
        for r in self.inventory_list:
            if r['group']['name'] == app:
                play_book = '%s/%s' % (self.job_name, 'webapps.yml')

                extra_vars = {
                    'rolename': app,
                    'deploypath': r['tomcat']['name'],
                }

                tag='start'
                msg = "start tomcat service on %s(%s) !" % (app,extra_vars['deploypath'])

                self.run_playbook(play_book, tag, extra_vars, msg,r)

    def start_java_app(self,app):
        for r in self.inventory_list:
            if r['group']['name'] == app:
                play_book = '%s/%s' % (self.job_name, 'javaapps.yml')
                for appfoot in r['app_foot']:
                    extra_vars = {
                        'hostname': "%s_%s" % (app,str(appfoot)),
                        'rolename': app,
                    }

                    tag='start'
                    msg = "start java service on %s !" % extra_vars['hostname']
                    self.run_playbook(play_book, tag, extra_vars, msg,r,hostname=extra_vars['hostname'])

    def start(self):
        if self.depapps == 'all':
            for app in self.allapp_list:
                if app in self.webapps:
                    self.start_web_app(app)
                elif app in self.javaapps:
                    self.start_java_app(app)
        else:
            depapps_list = self.depapps.split(',')
            for app in self.allapp_list:
                if app in depapps_list:
                    if app in self.webapps:
                        self.start_web_app(app)
                    if app in self.javaapps:
                        self.start_java_app(app)

    def restart_web_app(self,app):
        for r in self.inventory_list:
            if r['group']['name'] == app:
                play_book = '%s/%s' % (self.job_name, 'webapps.yml')

                extra_vars = {
                    'rolename': app,
                    'deploypath': r['tomcat']['name'],
                }

                tag='restart'
                msg = "restart tomcat service on %s(%s) !" % (app,extra_vars['deploypath'])

                self.run_playbook(play_book, tag, extra_vars, msg,r)

    def restart_java_app(self,app):
        for r in self.inventory_list:
            if r['group']['name'] == app:
                play_book = '%s/%s' % (self.job_name, 'javaapps.yml')
                for appfoot in r['app_foot']:
                    extra_vars = {
                        'hostname': "%s_%s" % (app,str(appfoot)),
                        'rolename': app,
                    }

                    tag='restart'
                    msg = "restart java service on %s !" % extra_vars['hostname']

                    self.run_playbook(play_book, tag, extra_vars, msg,r,hostname=extra_vars['hostname'])

    def restart(self):
        if self.depapps == 'all':
            for app in self.allapp_list:
                if app in self.webapps:
                    self.restart_web_app(app)
                #
                if app in self.javaapps:
                    self.restart_java_app(app)
        else:
            depapps_list = self.depapps.split(',')
            for app in self.allapp_list:
                if app in depapps_list:
                    if app in self.webapps:
                        self.restart_web_app(app)
                    if app in self.javaapps:
                        self.restart_java_app(app)

    def checkport_web_app(self,app):
        for r in self.inventory_list:
            if r['group']['name'] == app:
                play_book = '%s/%s' % (self.job_name, 'webapps.yml')

                extra_vars = {
                    'rolename': app,
                    'deploypath': r['tomcat']['name'],
                }

                tag='checkport'
                msg = "checkport tomcat service on %s(%s) !" % (app,extra_vars['deploypath'])

                self.run_playbook(play_book, tag, extra_vars, msg,r)

    def checkport_java_app(self,app):
        for r in self.inventory_list:
            if r['group']['name'] == app:
                play_book = '%s/%s' % (self.job_name, 'javaapps.yml')
                for appfoot in r['app_foot']:
                    extra_vars = {
                        'hostname': "%s_%s" % (app,str(appfoot)),
                        'rolename': app,
                    }

                    tag='checkport'
                    msg = "checkport java service on %s !" % extra_vars['hostname']

                    self.run_playbook(play_book, tag, extra_vars, msg,r,hostname=extra_vars['hostname'])

    def checkport(self):
        if self.depapps == 'all':
            for app in self.allapp_list:
                if app in self.webapps:
                    self.checkport_web_app(app)
                #
                if app in self.javaapps:
                    self.checkport_java_app(app)
        else:
            depapps_list = self.depapps.split(',')
            for app in self.allapp_list:
                if app in depapps_list:
                    if app in self.webapps:
                        self.checkport_web_app(app)
                    if app in self.javaapps:
                        self.checkport_java_app(app)

    def deploy_web_app(self,app):
        for r in self.inventory_list:
            if r['group']['name'] == app:
                play_book = '%s/%s' % (self.job_name, 'webapps.yml')

                extra_vars = {
                    'rolename': app,
                    'deploypath': r['tomcat']['name'],
                }

                tag='deploy'
                msg = "deploy web code on %s(%s) !" % (app,extra_vars['deploypath'])

                self.run_playbook(play_book, tag, extra_vars, msg,r)

    def deploy_java_app(self,app):
        for r in self.inventory_list:
            if r['group']['name'] == app:
                play_book = '%s/%s' % (self.job_name, 'javaapps.yml')
                for appfoot in r['app_foot']:
                    extra_vars = {
                        'hostname': "%s_%s" % (app,str(appfoot)),
                        'rolename': app,
                    }

                    tag='deploy'
                    msg = "deploy java code on %s !" % extra_vars['hostname']

                    self.run_playbook(play_book, tag, extra_vars, msg,r,hostname=extra_vars['hostname'])

    def deploy(self):

        if self.depapps == 'all':
            for app in self.allapp_list:
                if app in self.webapps:
                    self.deploy_web_app(app)
                        #
                if app in self.javaapps:
                    self.deploy_java_app(app)
        else:
            depapps_list = self.depapps.split(',')
            for app in self.allapp_list:
                if app in depapps_list:
                    if app in self.webapps:
                        self.deploy_web_app(app)
                    if app in self.javaapps:
                        self.deploy_java_app(app)

    def config_web_app(self,app):
        for r in self.inventory_list:
            if r['group']['name'] == app:
                play_book = '%s/%s' % (self.job_name, 'webapps.yml')

                extra_vars = {
                    'rolename': app,
                    'deploypath': r['tomcat']['name'],
                }


                templates = r.get('templates')
                if templates:
                    extra_vars['templates'] = templates

                tag='config'
                msg = "config web code on %s(%s) !" % (app,extra_vars['deploypath'])

                self.run_playbook(play_book, tag, extra_vars, msg,r)

    def config_java_app(self,app):
        for r in self.inventory_list:
            if r['group']['name'] == app:
                play_book = '%s/%s' % (self.job_name, 'javaapps.yml')
                for appfoot in r['app_foot']:
                    extra_vars = {
                        'hostname': "%s_%s" % (app,str(appfoot)),
                        'rolename': app,
                        'app_foot':str(appfoot),
                    }

                    templates = r['templates']
                    if templates:
                        extra_vars['templates'] = templates

                    tag='config'
                    msg = "config java code on %s !" % extra_vars['hostname']

                    self.run_playbook(play_book, tag, extra_vars, msg,r,hostname=extra_vars['hostname'])

    def config(self):

        if self.depapps == 'all':
            for app in self.allapp_list:
                if app in self.webapps:
                    self.config_web_app(app)
                        #
                if app in self.javaapps:
                    self.config_java_app(app)
        else:
            depapps_list = self.depapps.split(',')
            for app in self.allapp_list:
                if app in depapps_list:
                    if app in self.webapps:
                        self.config_web_app(app)
                    if app in self.javaapps:
                        self.config_java_app(app)

    def deploy_and_config_web_app(self,app):
        for r in self.inventory_list:
            if app == r['group']['name']:
                play_book = '%s/%s' % (self.job_name, 'webapps.yml')

                extra_vars = {
                    'rolename': app,
                    'deploypath': r['tomcat']['name'],
                }

                templates = r.get('templates')
                if templates:
                    extra_vars['templates'] = templates

                tag='all_job'
                msg = "(stop -> deploy -> config -> start) web code on %s(%s) !" % (app,extra_vars['deploypath'])

                self.run_playbook(play_book, tag, extra_vars, msg,r)
                if self.deploy_type == 'fun':
                    self.r.srem(self.change_redis_key,app)



    def deploy_and_config_java_app(self,app):
        for r in self.inventory_list:
            if app == r['group']['name']:
                for appfoot in r['app_foot']:
                    play_book = '%s/%s' % (self.job_name, 'javaapps.yml')
                    extra_vars = {
                        'hostname': "%s_%s" % (app,str(appfoot)),
                        'rolename': app,
                        'app_foot':str(appfoot),
                    }

                    templates = r.get('templates')
                    if templates:
                        extra_vars['templates'] = templates

                    tag='all_job'
                    msg = "(stop -> deploy -> config -> start) java code on (%s) !" % extra_vars['hostname']

                    self.run_playbook(play_book, tag, extra_vars, msg,r,hostname=extra_vars.get('hostname'))
                if self.deploy_type == 'fun':
                    self.r.srem(self.change_redis_key,app)

    def get_job_info(self,job_name):

        ret_list = []
        # url = 'http://10.12.208.72:8080'
        # username = "admin"
        # password = "3c986b051327f5b28f9f8647c1c5f4c1"
        server = self.get_jenkins_server()
        # jenkins.CREATE_NODE
        # print server.get_all_jobs()
        # print server.get_build_info("")
        # print server.get_version()
        last_build_number = server.get_job_info(job_name)['lastCompletedBuild']['number']
        # user = server.get_whoami()
        # print user
        build_info = server.get_build_info(job_name, last_build_number)
        change_items = build_info['changeSet']['items']
        for i in change_items:
            temp_dict = {}

            temp_dict['revision'] = i['revision']
            temp_dict['msg'] = i['msg']

            ret_list.append(temp_dict)

        return ret_list

    def sendEmail(self,authInfo, fromAdd, toAdd, subject, htmlText):
        strFrom = fromAdd
        strTo = ', '.join(toAdd)
        server = authInfo.get('server')
        # user = authInfo.get('user')
        # passwd = authInfo.get('password')
        # if not (server and user and passwd) :
        #         print 'incomplete login info, exit now'
        #         return
        # �趨root��Ϣ
        msgRoot = MIMEMultipart('related')
        msgRoot['Subject'] = subject
        msgRoot['From'] = strFrom
        msgRoot['To'] = strTo
        msgRoot.preamble = 'This is a multi-part message in MIME format.'
        # Encapsulate the plain and HTML versions of the message body in an
        # 'alternative' part, so message agents can decide which they want to display.
        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)
        # �趨���ı����/
        # msgText = MIMEText(plainText, 'plain', 'utf-8')
        # msgAlternative.attach(msgText)
        # �趨HTML��Ϣ
        msgText = MIMEText(htmlText, 'html', 'utf-8')
        msgAlternative.attach(msgText)
        # �趨����ͼƬ��Ϣ
        # fp = open('test.jpg', 'rb')
        # msgImage = MIMEImage(fp.read())
        # fp.close()
        # msgImage.add_header('Content-ID', '<image1>')
        # msgRoot.attach(msgImage)
        # �����ʼ�
        smtp = smtplib.SMTP()
        # �趨���Լ������������
        # smtp.set_debuglevel(1)
        smtp.connect(server)
        # smtp.login(user, passwd)
        smtp.sendmail(strFrom, toAdd, msgRoot.as_string())
        smtp.quit()

    def email_after_fun(self):


        app_list = []

        if self.depapps == 'all':
            app_list+=self.webapps.keys()
            app_list+=self.javaapps.keys()
        else:
            app_list = self.depapps.split(',')


        module_list = []
        for module_name in app_list:
            module_list.append("BUILD-" + module_name)
        # print get_job_info('BUILD-selfmember',35)
        ret_list = []
        for job_name in module_list:
            ret_dic = {}
            commint_info = self.get_job_info(job_name)
            ret_dic['module_name'] = job_name.split('-')[1]
            ret_dic['comments'] = commint_info
            ret_list.append(ret_dic)

        template = Template(self.html)
        htmlText = template.render(ret_list=ret_list, job_name=self.job_name, envid=self.envid)

        authInfo = {}
        authInfo['server'] = self.config_dic['smtp_info']['server']
        # # authInfo['user'] = 'username'
        # # authInfo['password'] = 'password'
        fromAdd = self.config_dic['smtp_info']['from_addr']

        toAdd = self.config_dic['email_list']['test'].split(',')
    #    toAdd += self.config_dic['email_list']['develop'].split(',')
        toAdd += self.config_dic['email_list']['admin'].split(',')

        subject = self.job_name
        # plainText = '��������ͨ�ı�'
        # with open("email.html") as f:
        #     htmlText = f.read()
        self.sendEmail(authInfo, fromAdd, toAdd, subject, htmlText)



    def all(self):
        # if not self.production:
        #     if not self.deploy_type:
        #         sys.exit("must input --deploy_type like fun or uat")

        if self.depapps == 'all':
            for app in self.allapp_list:
                if app in self.javaapps:
                    self.deploy_and_config_java_app(app)
                elif app in self.webapps:
                    self.deploy_and_config_web_app(app)

        else:
            depapps_list = self.depapps.split(',')

            for app in self.allapp_list:
                if app in depapps_list:
                    if app in self.webapps:
                        self.deploy_and_config_web_app(app)
                    elif app in self.javaapps:
                        self.deploy_and_config_java_app(app)


        if self.deploy_type == 'fun':
            if not self.mavenbase:
                self.email_after_fun()
        # self.stop()
        # time.sleep(2)
        # self.deploy()
        # time.sleep(2)
        # self.config()
        # time.sleep(2)
        # self.start()
        # if self.deploy_type == 'fun':
        #     pass

       # self.post_action()

    def check_build_status(self):
        if not  self.build_number:
            sys.exit("Please input the build number (--build_number) !! ")
        server = self.get_jenkins_server()
        #BUILD-test
        build_info = server.get_build_info(self.job_name, self.build_number)
        # build_info = server.get_build_info('BUILD-test', self.build_number)
        # print build_info
        build_info['result'] = 'SUCCESS'
        if  build_info['result'] != 'SUCCESS':
            msg = "%s - Build # %d - Failure!" % (self.job_name,self.build_number)

            sys.exit(msg)
        else:
            return True
        #     log_file_path = os.path.join(
        #         os.path.join(
        #             os.path.join(
        #                 os.path.join(
        #                     os.path.join(
        #                         os.path.dirname(
        #                             self.config_dic['base_dir']),
        #                         'jobs'
        #                     ),
        #                     self.job_name
        #                 ),
        #                 'builds'
        #             ),
        #             str(self.build_number)
        #         ),
        #         'log'
        #     )
        #     # with open(log_file_path) as f:
        #     #     charset = chardet.detect(f.read())
        #     #     print charset, type(charset)
        #     with open(log_file_path) as f:
        #         s = f.read()
        #         s = s.decode('gbk').encode('utf8')
        #     temp = ''
        #     for l in s:
        #         try:
        #             if l.index("8mha"):
        #                 print 'index'
        #                 continue
        #         except Exception as e:
        #             # print 'exception'
        #             temp += l
        #     subject = "%s - Build # %d - Failure!" % (self.job_name,self.build_number)
        #     html_content ="<h2>%s</h2>" % subject
        #     html_content += '<table>'
        #     html_content+='<tr><td>%s</td><td>%s</td></tr>' % ("fullDisplayName",build_info['fullDisplayName'])
        #     html_content += '</table>'
        #     html_content += "<pre>%s</pre>" % temp.decode(encoding='utf8')
        #
        #
        #     sender='itbushu@tjpme.com'
        #     receivers=self.config_dic['email_list']['admin'].split(',')
        #     Utils.send_mail(subject,html_content,sender,receivers)
        #
        #
        #
        #
        #     # s.encode(encoding='utf-8')
        #     # print s
        #     # sys.exit("job_failed")
        # else:
        #     subject = "%s - Build # %d - Successful!" % (self.job_name, self.build_number)
        #     html_content = "<h2>%s</h2>" % subject
        #     html_content += '<table>'
        #     html_content += '<tr><td>%s</td><td>%s</td></tr>' % ("fullDisplayName", build_info['fullDisplayName'])
        #     html_content += '</table>'
        #     # html_content += "<pre>%s</pre>" % temp.decode(encoding='utf8')
        #
        #     sender = 'itbushu@tjpme.com'
        #     receivers = self.config_dic['email_list']['admin'].split(',')
        #     Utils.send_mail(subject, html_content, sender, receivers)
        #
        # sys.exit()

    def gen_svn_number_file(self,file_path):
        try:

            server = self.get_jenkins_server()
            build_info_dict = server.get_build_info(self.job_name,self.build_number)
            print(build_info_dict)
            svn_url_list = build_info_dict['changeSet']['revisions']

            if len(svn_url_list) == 1:
                sn = svn_url_list[0]['revision']
                print("gen svn number file (%s) ! " % os.path.join(file_path,".sn"))
                with open(os.path.join(file_path,".sn"),'w') as f:
                    fcntl.flock(f, fcntl.LOCK_EX)
                    f.write(str(sn))
        except Exception as e:
            traceback.print_exc()



    def gen_build_number(self,file_path):
        try:
            print("gen build number file (%s) ! " % os.path.join(file_path,".bn"))
            with open(os.path.join(file_path,".bn"),'w') as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                f.write(str(self.build_number))
        except Exception as e:
            traceback.print_exc()

    def build(self):

        if self.depapps:
            try:
                app_name = self.depapps.split(',')[0]

                if len(self.depapps.split(',')) > 1:
                    self.app_list = self.depapps.split(',')
            except Exception as e:
                traceback.print_exc()
                sys.exit(1)
        else:
            try:
                app_name = self.job_name.split('-')[1]
            except Exception as e:
                print('jenkins job name not right format')

        server = self.get_jenkins_server()
        #BUILD-test
        try:
            self.build_info_dict = server.get_build_info(self.job_name, self.build_number)


            build_status =  self.build_info_dict["result"]
            if build_status != "SUCCESS":
                self.post_action()
                sys.exit("build error !")

            elif self.is_jar:
                self.post_action()
                sys.exit(0)

            else:
                try:
                    last_build = int(self.build_number)-1
                    if last_build==0:
                        self.add_change_recoder(app_name)
                        print(" is first build ")
                    else:
                        last_build_info_dict = server.get_build_info(self.job_name, int(self.build_number-1))
                        last_build_status = last_build_info_dict["result"]
                        if last_build_status != "SUCCESS":
                            self.add_change_recoder(app_name)

                except Exception as e:
                    traceback.print_exc()

        except Exception as e:
            traceback.print_exc()
            sys.exit("get build info error !")

        if self.mavenbase:
            pom_handler = ParsePomXml(self.job_workspace)
            ret_dict = pom_handler.get_all_file_list()

            for module_name,src_path in ret_dict.items():
                x = PrettyTable(["(RSYNC %s to BUILDS)" % module_name])

                Utils.rsync_command(src_path,os.path.join(self.project_dir,module_name),x,delete=True)

                print(x)

                Utils.add_version_file(os.path.join(self.project_dir,app_name),self.app_full_name)

                Utils.md5check(os.path.join(self.project_dir,module_name))

                x = PrettyTable(["(RSYNC %s config to BUILDS)" % module_name])

                config_file_path = os.path.join(
                    self.job_workspace,
                    module_name,
                    "config"
                )
                Utils.rsync_command_for_config(config_file_path,os.path.join(self.project_config_dir,module_name),x,delete=True)
                print(x)

#                Utils.add_version_file(os.path.join(self.project_config_dir,app_name),self.app_full_name)
                Utils.md5check_for_config(os.path.join(self.project_config_dir,module_name))

                self.add_change_recoder(module_name)
        elif self.ant:

            try:


                job_build_dir = os.path.join(self.job_workspace, 'build/%s' % app_name)

                config_path = os.path.join(self.job_workspace, 'config')
                #  if os.path.exists(config_path):
                #      print "remove config dir (%s)" % config_path
                #      shutil.rmtree(self.config_path)
                # Utils.remove_svn_dir(config_path)
                x = PrettyTable([app_name + "(RSYNC THEN CODE  TO BUILS DIRECTORY)"])
                Utils.rsync_command(job_build_dir, os.path.join(self.project_dir, app_name), x, delete=True)
                print(x)

                Utils.add_version_file(os.path.join(self.project_dir,app_name),self.app_full_name)
                Utils.md5check(os.path.join(self.project_dir, app_name))

                x = PrettyTable([app_name + "(RSYNC THEN  CONFIG TO BUILS DIRECTORY)"])
                if os.path.exists(os.path.join(self.project_config_dir, app_name)):
                    print("rmove builds config  (%s)" % os.path.join(self.project_config_dir, app_name))
                    shutil.rmtree(os.path.join(self.project_config_dir, app_name))
                Utils.rsync_command_for_config(config_path, os.path.join(self.project_config_dir, app_name), x,
                                               delete=True)
                print(x)
                Utils.add_version_file(os.path.join(self.project_config_dir,app_name),self.app_full_name)
                Utils.md5check_for_config(os.path.join(self.project_config_dir, app_name))


            except IndexError as e:

                msg = traceback.format_exc()
                print(msg)
                sys.exit("the job name '%s is not the right format . must be like this (BUILD-appname) " % app_name)
            except Exception as e:
                msg = traceback.format_exc()
                sys.exit(msg)
                # sys.exit("remove dir (%s) error!!" % self.job_build_dir)
            self.add_change_recoder(app_name)

        else:
            try:



                self.job_build_dir = os.path.join(self.job_workspace,'build/%s' % app_name)
                Utils.check_legal_path(self.job_build_dir)
                print("remove dir (%s)" % self.job_build_dir)
                if os.path.exists(self.job_build_dir):
                    shutil.rmtree(self.job_build_dir)
                os.makedirs(self.job_build_dir)

                if not self.package_file:

                    target_path = os.path.join(self.job_workspace,"target/*.zip")
                    import glob
                    file_list = glob.glob(target_path)
                    if len(file_list) == 1:

                        file_path = file_list[0]
                    else:
                        target_path = os.path.join(self.job_workspace, "target/*.war")
                        file_path = glob.glob(target_path)[0]

                else:
                    file_path = os.path.join(self.job_workspace,'target/%s' % self.package_file)

                if not os.path.exists(file_path):
                    sys.exit("the target file (%s) not exist !\nmust input the package_file like : --package_file=test.war" % file_path)
                Utils.unzip_file(file_path,self.job_build_dir)

                config_path = os.path.join(self.job_workspace,'config')
              #  if os.path.exists(config_path):
              #      print "remove config dir (%s)" % config_path
              #      shutil.rmtree(self.config_path)
               # Utils.remove_svn_dir(config_path)
                x = PrettyTable([app_name+"(RSYNC THEN CODE  TO BUILS DIRECTORY)"])
                Utils.rsync_command(self.job_build_dir,os.path.join(self.project_dir,app_name),x,delete=True)
                print(x)

                Utils.add_version_file(os.path.join(self.project_dir,app_name),self.app_full_name)
                if self.build_number:
                    self.gen_svn_number_file(os.path.join(self.project_dir,app_name))
                    self.gen_build_number(os.path.join(self.project_dir,app_name))
                Utils.md5check(os.path.join(self.project_dir,app_name))

                x = PrettyTable([app_name + "(RSYNC THEN  CONFIG TO BUILS DIRECTORY)"])
                if os.path.exists(os.path.join(self.project_config_dir, app_name)):
                    print("rmove builds config  (%s)" % os.path.join(self.project_config_dir, app_name))
                    shutil.rmtree(os.path.join(self.project_config_dir, app_name))
                Utils.rsync_command_for_config(config_path, os.path.join(self.project_config_dir, app_name),x,delete=True)
                print(x)
                Utils.add_version_file(os.path.join(self.project_config_dir,app_name),self.app_full_name)
                if self.build_number:
                    self.gen_svn_number_file(os.path.join(self.project_config_dir,app_name))
                    self.gen_build_number(os.path.join(self.project_config_dir,app_name))
                Utils.md5check_for_config(os.path.join(self.project_config_dir, app_name))


                if hasattr(self,"app_list") and len(self.app_list) > 1:
                    src = os.path.join(self.project_dir, app_name)
                    src_config = os.path.join(self.project_config_dir, app_name)
                    for i in self.app_list[1:]:
                        dst = os.path.join(
                            self.project_dir,
                            i,
                        )

                        dst_config = os.path.join(
                            self.project_config_dir,
                            i,
                        )

                        try:
                            print("ln -s %s %s" % (src,dst))
                            os.symlink(src, dst)
                            print("ln -s %s %s" % (src_config,dst_config))
                            os.symlink(src_config, dst_config)
                        except OSError as e:
                            pass

            except IndexError as e:
               
                msg = traceback.format_exc()
                print(msg)
                sys.exit("the job name '%s is not the right format . must be like this (BUILD-appname) " % app_name )
            except Exception as e:
                msg = traceback.format_exc()
                sys.exit(msg)
                # sys.exit("remove dir (%s) error!!" % self.job_build_dir)
            self.add_change_recoder(app_name)

        self.post_action()

    def add_change_recoder(self,app_name):
        # change_redis_key = "%s_change" % self.app_full_name
        # changeall_redis_key = "%s_changeall" % self.app_full_name

        try:
            server  = self.get_jenkins_server()
            build_info_dict = server.get_build_info(self.job_name,self.build_number)
            if len(build_info_dict["changeSet"]["items"]) != 0 or len(build_info_dict["changeSet"]["revisions"]) > 1:
                print("add change reocder(%s) into redis for svn change" % app_name)
                self.r.sadd(self.change_redis_key,app_name)
                self.r.sadd(self.changeall_redis_key,app_name)
                if  hasattr(self,"app_list") and len(self.app_list) > 1:
                    for i in self.app_list[1:]:
                        print("add change reocder(%s) into redis" % i)
                        self.r.sadd(self.change_redis_key, i)
                        self.r.sadd(self.changeall_redis_key, i)
            else:
                cause_dict = build_info_dict['actions'][0]['causes'][0]
                if cause_dict.has_key('upstreamBuild'):
                    print("add change reocder(%s) into redis for upstream jar change" % app_name)
                    self.r.sadd(self.change_redis_key, app_name)
                    self.r.sadd(self.changeall_redis_key, app_name)
        except Exception as e:
            traceback.print_exc()

    # def backup_config_dict(self):
    #     try:
    #         backup_suffix = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    #
    #         file_name,suffix = os.path.splitext(self.config_file_dir)
    #         backup_config_path = "%s_%s%s" % (file_name,backup_suffix,suffix)
    #
    #         with open(backup_config_path, 'w') as f:
    #             yaml.dump(self.config_dic, f, default_flow_style=False)
    #     except Exception as e:
    #         print 'backup config_fict faile !!!'
    #         msg = traceback.format_exc()
    #         sys.exit(msg)
    #
    # def update_config_dict(self):
    #     try:
    #         with open(self.config_file_dir, 'w') as f:
    #             fcntl.flock(f, fcntl.LOCK_EX)
    #             yaml.dump(self.config_dic, f, default_flow_style=False)
    #     except Exception as e:
    #         print 'update config_fict faile !!!'
    #         msg = traceback.format_exc()
    #         sys.exit(msg)

    def get_md5_number(self,md5_file_path):
        if os.path.exists(md5_file_path):
            with open(md5_file_path) as f:
                md5sum = hashlib.md5()
                md5sum.update(f.read())
                md5sum_digest = md5sum.hexdigest()
                return md5sum_digest
        else:
            sys.exit("%s not exist!" % md5_file_path)

    def md5check(self):
        if not self.config_dic['uat_job_name']:
            sys.exit("Please config the uat_job_name in  config")
        print("MD5 VERIFY:")
        # app_list = []
        diff_app_list = []
        # changeall_file_path = os.path.join(self.changelog_dir,'changeall')
        # with open(changeall_file_path) as f:
        #     for l in f:
        #         app_list.append(l)

        app_list = list(self.r.smembers(self.changeall_redis_key))

        self.uat_job_workspace = os.path.join(
            self.config_dic['base_dir'],
            self.config_dic['uat_job_name']
        )
        for app_name in app_list:
            app_name = app_name.strip()
            #check code md5
            builds_md5_file_path = os.path.join(
                os.path.join(
                    os.path.join(
                        self.builds_dir,
                        self.app_full_name
                    ),
                    app_name
                ),
                'md5check.txt'
            )
            builds_md5 = self.get_md5_number(builds_md5_file_path)
            if app_name in self.javaapps.keys():
                role_md5_file_path = os.path.join(
                    os.path.join(
                        os.path.join(
                            self.uat_job_workspace,
                            self.config_dic['java_app_file_path']
                        ),
                        app_name
                        ),
                    'md5check.txt'
                )
            elif app_name in self.webapps.keys():
                role_md5_file_path = os.path.join(
                    os.path.join(
                        os.path.join(
                            self.uat_job_workspace,
                            self.config_dic['web_app_file_path']
                        ),
                        app_name
                        ),
                    'md5check.txt'
                )
            else:
                print(self.webapps.keys())
                print(self.javaapps.keys())
                sys.exit("app(%s) must belong to webapps or javaapps !" % app_name)
            role_md5 = self.get_md5_number(role_md5_file_path)
            print(builds_md5_file_path,role_md5_file_path)
            print(builds_md5,role_md5)
            if builds_md5 != role_md5:
                diff_app_list.append(app_name)




            #check config md5
            builds_md5_config_path = os.path.join(
                os.path.join(
                    os.path.join(
                        self.builds_dir,
                        self.app_full_config_name
                    ),
                    app_name
                ),
                'md5check.txt'
            )
            builds_config_md5 = self.get_md5_number(builds_md5_config_path)
            if app_name in self.javaapps.keys():
                role_md5_config_path = os.path.join(
                    os.path.join(
                        os.path.join(
                            self.uat_job_workspace,
                            self.config_dic['java_app_template_path']
                        ),
                        app_name
                    ),
                    'md5check.txt'
                )
            else:
                role_md5_config_path = os.path.join(
                    os.path.join(
                        os.path.join(
                            self.uat_job_workspace,
                            self.config_dic['web_app_template_path']
                        ),
                        app_name
                    ),
                    'md5check.txt'
                )
            print(builds_md5_config_path,role_md5_config_path)
            role_config_md5 = self.get_md5_number(role_md5_config_path)
            print(builds_config_md5,role_config_md5)
            if builds_config_md5 != role_config_md5:
                diff_app_list.append("%s_config" % app_name)
        # diff_file_path = os.path.join(self.job_workspace,'diff_app.yml')
        # with open(diff_file_path, 'w') as f:
        #     fcntl.flock(f, fcntl.LOCK_EX)
        #
        #     yaml.dump(diff_app_list, f, default_flow_style=False)
        if diff_app_list:
            print(diff_app_list)
            sys.exit("file change alter dingban")
        else:
            try:


                print('md5check passed !!!')
                # new_change_all_path = os.path.join(
                #     self.builds_dir,
                #     self.app_full_name,
                #     'changeall'
                # )
                # # print 'copy %s to %s ' % (changeall_file_path,new_change_all_path)
                # # shutil.copy(changeall_file_path,new_change_all_path)
                # # print "change config file (%s)" % self.config_file_dir
                #
                #
                # # app_list
                # print 'backup change all recoder to %s' % new_change_all_path
                #
                # with open(new_change_all_path,'w') as f:
                #     for app_name in app_list:
                #         f.write("%s\n" % app_name)


                payload = {
                    # "envid": self.envid,
                    "project": self.project,
                    "version": self.version,
                    # "apps": self.depapps,
                    "job_type": self.job_type
                }
                r = requests.post(self.api_url, data=payload,headers=self.headers)
                print(r.url)
                ret = r.json()
                print(ret)
                # self.backup_config_dict()
                # print current_version
                # self.config_dic['lastversion'] =  self.config_dic['version']

                # self.config_dic['version'] = '%s_temp' % self.config_dic['version']
                # self.update_config_dict()
            except Exception as e:
                msg = traceback.format_exc()
                sys.exit(msg)

    def sync2pro(self):

        if not self.config_dic.has_key("production_mount_point"):
            sys.exit("don't have production_mount_point configuration!")

        if not os.path.exists( self.config_dic.get("production_mount_point")):
            sys.exit("production_mount_point don't exist  !")


        try:
            # version_file_path = os.path.join(
            #     self.config_dic['base_dir'],
            #     self.config_dic['uat_job_name'],
            #     'version'
            # )
            # with open(version_file_path) as f:


            app_full_onlinename = "%s_%s" % (self.config_dic['app_prefix'],"online")
            app_full_config_onlinename = "%s_config" % app_full_onlinename


            product_app_dir = os.path.join(self.config_dic['production_mount_point'],self.app_full_name)
            if not os.path.exists(product_app_dir):
                os.mkdir(product_app_dir)

            product_app_config_dir = os.path.join(self.config_dic['production_mount_point'],self.app_full_config_name)
            if not os.path.exists(product_app_config_dir):
                os.mkdir(product_app_config_dir)

            product_app_online_dir = os.path.join(self.config_dic['production_mount_point'], app_full_onlinename)
            if not os.path.exists(product_app_online_dir):
                os.mkdir(product_app_online_dir)

            product_app_config_online_dir = os.path.join(self.config_dic['production_mount_point'], app_full_config_onlinename)
            if not os.path.exists(product_app_config_online_dir):
                os.mkdir(product_app_config_online_dir)

            # changeall_file_path = os.path.join(
            #     self.config_dic['base_dir'],
            #     self.config_dic['builds_dir'],
            #     app_full_name,
            #     'changeall'
            # )
            app_list = self.r.smembers(self.changeall_redis_key)

            # with open(changeall_file_path) as f:
            #     print 'open',changeall_file_path
            #     for app_name in f:
            #         app_list.append(app_name.strip())

            x = PrettyTable(["(BACKUP CURRENT ONLINE VERSION)"])
            time_stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            Utils.rsync_command(product_app_online_dir,"%s_%s" % (product_app_online_dir,time_stamp),x,delete=True)
            Utils.rsync_command(product_app_config_online_dir,"%s_%s" % (product_app_config_online_dir,time_stamp),x,delete=True)
            print(x)

            for app in app_list:
                x = PrettyTable([app.strip() + "(SYNC APP TO PRODUCTION MOUNT)"])

                if app in self.javaapps.keys():

                    src = os.path.join(
                        self.config_dic['base_dir'],
                        self.config_dic['uat_job_name'],
                        self.config_dic['java_app_file_path'],
                        app
                    )
                elif app in self.webapps.keys():
                    src = os.path.join(
                        self.config_dic['base_dir'],
                        self.config_dic['uat_job_name'],
                        self.config_dic['web_app_file_path'],
                        app
                    )
                # dest = os.path.join(product_app_dir,app)
                online_dest = os.path.join(product_app_online_dir,app)
                # Utils.rsync_command(src,dest,x,delete=True)
                Utils.rsync_command(src,online_dest,x,delete=True)



                if app in self.javaapps.keys():
                    src_config = os.path.join(
                        self.config_dic['base_dir'],
                        self.config_dic['uat_job_name'],
                        self.config_dic['java_app_template_path'],
                        app
                    )
                elif app in self.webapps.keys():
                    src_config = os.path.join(
                        self.config_dic['base_dir'],
                        self.config_dic['uat_job_name'],
                        self.config_dic['web_app_template_path'],
                        app
                    )
                # dest_config = os.path.join(product_app_config_dir,app)
                online_dest_config = os.path.join(product_app_config_online_dir,app)
                # Utils.rsync_command(src_config,dest_config,x,delete=True)
                Utils.rsync_command(src_config,online_dest_config,x,delete=True)
                # Utils.rsync_command(src,dest,x,delete=True)
                print(x)
            # print 'copy %s to %s' % (changeall_file_path, os.path.join(product_app_dir,"changeall"))
            # shutil.copy(changeall_file_path, os.path.join(product_app_dir,"changeall"))


            with open(os.path.join(product_app_online_dir, "changeall"), 'w') as f1:
                with open(os.path.join(product_app_config_online_dir, "changeall"), 'w') as f2:
                    for app in app_list:
                        f1.write("%s%s" % (app, os.linesep))
                        f2.write("%s%s" % (app, os.linesep))


            with open(os.path.join(product_app_online_dir, ".current_version"), 'w') as f1:
                with open(os.path.join(product_app_config_online_dir, ".current_version"), 'w') as f2:
                    f1.write(self.app_full_name)
                    f2.write(self.app_full_name)

            x = PrettyTable(["(GEN APP TO VERSION LINE)"])

            Utils.rsync_command(product_app_online_dir,product_app_dir,x,delete=True)
            Utils.rsync_command(product_app_config_online_dir,product_app_config_dir,x,delete=True)

            print(x)




            x = PrettyTable(["id","UPDATE APP LIST VERSION(%s)" % self.app_full_name])
            for index,app in enumerate(app_list):
                x.add_row([index+1,app])
            print(x)



        except Exception as e:

            msg = traceback.format_exc()
            sys.exit(msg)
    def command(self):
        if not self.command_args:
            msg = "please input the command like : --command_args=ls"
            sys.exit(msg)
        msg = 'run command %s' % self.command_args
        self.run_module(msg)




    def deal_prod_md5(self,app):


        if app in self.javaapps.keys():
            source_md5_file = os.path.join(
                    os.path.join(
                        os.path.join(
                        self.job_workspace,
                        self.config_dic['java_app_file_path']
                    ),app
                ),'%s_md5check.txt' % app
            )

            target_md5_file = os.path.join(
                    os.path.join(
                        self.job_workspace,
                        self.config_dic['java_app_file_path']
                    ), '%s_md5check.txt' % app
            )


            config_source_md5_file = os.path.join(
                    os.path.join(
                        os.path.join(
                        self.job_workspace,
                        self.config_dic['java_app_template_path']
                    ),app
                ),'%s_md5check.txt' % app
            )

            config_target_md5_file = os.path.join(
                    os.path.join(
                        self.job_workspace,
                        self.config_dic['java_app_template_path']
                    ), '%s_md5check.txt' % app
            )



        elif app in self.webapps.keys():
            source_md5_file = os.path.join(
                    os.path.join(
                        os.path.join(
                        self.job_workspace,
                        self.config_dic['web_app_file_path']
                    ),app
                ),'md5check.txt'
            )


            target_md5_file = os.path.join(
                    os.path.join(
                        self.job_workspace,
                        self.config_dic['web_app_file_path']
                    ), '%s_md5check.txt' % app
            )

            config_source_md5_file = os.path.join(
                    os.path.join(
                        os.path.join(
                        self.job_workspace,
                        self.config_dic['web_app_template_path']
                    ),app
                ),'md5check.txt'
            )

            config_target_md5_file = os.path.join(
                    os.path.join(
                        self.job_workspace,
                        self.config_dic['web_app_template_path']
                    ), '%s_md5check.txt' % app
            )
        try:
            print('move %s' % source_md5_file)
            print('to %s' % target_md5_file)
            print
            shutil.move(source_md5_file,target_md5_file)
            role_app_dir = os.path.dirname(source_md5_file)
            md5_file_path = Utils.gen_prod_md5check(role_app_dir)

            with open(target_md5_file) as md5_file_hd:
                with open(md5_file_path) as current_md5_file:
                    md5_file_hd_str = md5_file_hd.read()
                    current_md5_file_str = current_md5_file.read()

                    if md5_file_hd_str == current_md5_file_str:
                        msg = '%s check pass !' % app
                    else:
                        msg = '%s check failed !' % app
                        self.pro_md5_diff_list.append(app)
                    x = PrettyTable(["file check result"])
                    x.add_row([msg])
                    print(x)

            print

            print('move %s' % target_md5_file)
            print('to %s' % source_md5_file)
            shutil.move(target_md5_file,source_md5_file)


            print('---------------------- check config file --------------------')

            print('move config %s' % config_source_md5_file)
            print('to config %s' % config_target_md5_file)
            print
            shutil.move(config_source_md5_file,config_target_md5_file)
            config_role_app_dir = os.path.dirname(config_source_md5_file)
            config_md5_file_path = Utils.gen_prod_md5check(config_role_app_dir)

            with open(config_target_md5_file) as config_md5_file_hd:
                with open(config_md5_file_path) as config_current_md5_file:
                    config_md5_file_hd_str = config_md5_file_hd.read()
                    config_current_md5_file_str = config_current_md5_file.read()

                    if config_md5_file_hd_str == config_current_md5_file_str:

                        msg = '%s check config pass !' % app
                    else:
                        msg = '%s check config failed !' % app
                        self.pro_md5_diff_list.append("%s_config" % app)
                    x = PrettyTable(["config file check result"])
                    x.add_row([msg])
                    print(x)

            print

            print('move config %s' % config_target_md5_file)
            print('to config %s' % config_source_md5_file)
            shutil.move(config_target_md5_file,config_source_md5_file)



        except Exception as e:

            msg = traceback.format_exc()
            sys.exit(msg)






    def backup_deploy_dir(self):
        backup_dir = os.path.join(self.config_dic['base_dir'], self.config_dic['backup_dir'])
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        project_backup_dir = os.path.join(backup_dir,"before_%s" % self.app_full_name)
        time_stamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        cur_pro_back_dir = "%s_%s" % (project_backup_dir,time_stamp)
        if not os.path.exists(cur_pro_back_dir):
            os.makedirs(cur_pro_back_dir)

        cur_pro_config_back_dir = "%s_config_%s" % (project_backup_dir,time_stamp)
        if not os.path.exists(cur_pro_config_back_dir):
            os.makedirs(cur_pro_config_back_dir)

        src_list = [
            self.config_dic['java_app_file_path'],
            self.config_dic['web_app_file_path'],
        ]
        x = PrettyTable(['BACKUP BEFORE DEPLOY'])

        deploy_job_name = self.get_deploy_jobname()

        for i in src_list:
            src = os.path.join(
                os.path.join(
                    self.config_dic['base_dir'],
                    deploy_job_name
                )
                ,i
            )

            if os.path.exists(src):
                Utils.rsync_command(src,cur_pro_back_dir,x)
            else:
                print("%s not exist " % src)


        print(x)


        x = PrettyTable(['BACKUP CONFIG BEFORE DEPLOY'])


        src_list = [
            self.config_dic['java_app_template_path'],
            self.config_dic['web_app_template_path'],
        ]



        for i in src_list:
            src = os.path.join(
                os.path.join(
                    self.config_dic['base_dir'],
                    deploy_job_name
                )
                ,i
            )

            if os.path.exists(src):
                Utils.rsync_command(src,cur_pro_config_back_dir,x)
            else:
                print("%s not exist " % src)

        print(x)




    def get_deploy_jobname(self):
        if self.job_type == 'mnmd5check':
            deploy_job_name = self.config_dic['mn_prod_deploy_job']
        elif self.job_type == 'promd5check':
            deploy_job_name = self.config_dic['sp_prod_deploy_job']

        return deploy_job_name
    def push_web_to_deploy_dir(self,app):
        deploy_job_name = self.get_deploy_jobname()
        src = os.path.join(
            os.path.join(
                self.job_workspace,
                self.config_dic['web_app_file_path']
            ), app
        )

        dest = os.path.join(
            os.path.join(
                os.path.join(
                    self.config_dic['base_dir'],
                    deploy_job_name
                ),
                self.config_dic['web_app_file_path']
            ),
            app
        )

        config_src = os.path.join(
            os.path.join(
                self.job_workspace,
                self.config_dic['web_app_template_path']
            ), app
        )

        config_dest = os.path.join(
            os.path.join(
                os.path.join(
                    self.config_dic['base_dir'],
                    deploy_job_name
                ),
                self.config_dic['web_app_template_path']
            ),
            app
        )

        x = PrettyTable(['push %s to deploy dir' % app])

        Utils.rsync_command(src,dest,x,delete=True)

        print(x)
        x = PrettyTable(['push %s config to deploy dir' % app])

        Utils.rsync_command(config_src, config_dest,x,delete=True)
        print(x)


    def push_java_to_deploy_dir(self,app):
        deploy_job_name = self.get_deploy_jobname()
        src = os.path.join(
            os.path.join(
                self.job_workspace,
                self.config_dic['java_app_file_path']
            ), app
        )

        dest = os.path.join(
            os.path.join(
                self.config_dic['base_dir'],
                deploy_job_name
            ),
            self.config_dic['java_app_file_path']
        )

        config_src = os.path.join(
            os.path.join(
                self.job_workspace,
                self.config_dic['java_app_template_path']
            ),
            app
        )

        config_dest = os.path.join(
            os.path.join(
                os.path.join(
                    self.config_dic['base_dir'],
                    deploy_job_name
                ),
                self.config_dic['java_app_template_path']
            ),
            app
        )

        print(src, dest)
        print(config_src, config_dest)

    def push_checked_dir_to_deploy_dir(self):


        if self.depapps == 'all':
            for app in self.webapps.keys():
                self.push_web_to_deploy_dir(app)

            for app in self.javaapps.keys():
                self.push_java_to_deploy_dir(app)
        else:
            depapps_list = self.depapps.split(',')
            for app in depapps_list:
                if app in self.webapps.keys():
                    self.push_web_to_deploy_dir(app)
                elif app in self.javaapps.keys():
                    self.push_java_to_deploy_dir(app)


    def basemd5check(self):
        self.pro_md5_diff_list = []

        try:
            if self.depapps == 'all':
                for app in self.webapps.keys():
                    self.deal_prod_md5(app)
                    #
                for app in self.javaapps.keys():
                    self.deal_prod_md5(app)

            else:
                depapps_list = self.depapps.split(',')
                for app in depapps_list:
                    self.deal_prod_md5(app)

                        # shutil

            print
            print
            if self.pro_md5_diff_list:
                x = PrettyTable([ 'check failed !!!!'])

                for i in self.pro_md5_diff_list:
                    x.add_row([i])

                print(x)
            else:
                self.backup_deploy_dir()
                self.push_checked_dir_to_deploy_dir()


        except Exception as e:

            msg = traceback.format_exc()
            sys.exit(msg)


    def promd5check(self):
        self.basemd5check()

    def mnmd5check(self):
        self.basemd5check()





    def sendmail(self):
        self.post_action()



        # print self.config_dic





    def job_mail(self):
        server = self.get_jenkins_server()
        build_info_dict = server.get_build_info(self.job_name, self.build_number)

        build_url = build_info_dict["url"]
        try:
            cause = build_info_dict["actions"][1]["causes"][0]["shortDescription"]
        except Exception as e:
            # cause = build_info_dict["actions"][0]["causes"][0]["shortDescription"]
            # cause = ""

            try:
                cause = build_info_dict["actions"][0]["causes"][0]["shortDescription"]

            except Exception as e:
                cause = ""
#        try:
#            cause = build_info_dict["actions"][1]["causes"][0]["shortDescription"]
#        except Exception as e:
#            cause = build_info_dict["actions"][0]["causes"][0]["shortDescription"]
        result = build_info_dict["result"]
    #    if self.job_type == "all":
    #        result = 'SUCCESS'
        if self.job_type == "build":
            svn_url = build_info_dict["changeSet"]["revisions"][0]["module"]
            svn_number = build_info_dict["changeSet"]["revisions"][0]["revision"]
        else:
            svn_url = ""
            svn_number = ""
        template = Template(self.job_mail_html)
        htmlText = template.render(
            action=self.job_type,
            job_name=self.job_name,
            build_number=self.build_number,
            svn_url=svn_url,
            svn_version=svn_number,
            cause=cause,
            deployapps=self.depapps,
            build_url= build_url,
            build_status=result
        )

        authInfo = {}
        authInfo['server'] = self.config_dic['smtp_info']['server']
        # authInfo['server'] = self.config_dic['smtp_info']['from_addr']

        mail_list = self.config_dic["job_mail_list"]

        subject = "%s - Build # %s - %s!" % (self.job_name,str(self.build_number),result)
        if mail_list:
            if result != "SUCCESS":
                mail_list.append(self.admin_mail)
            print("sendmail to %s" % ','.join(mail_list))
            self.sendEmail(authInfo, self.config_dic['smtp_info']['from_addr'], mail_list, subject, htmlText)

    def post_action(self):
        pass

    #    self.job_mail()

    def run(self):
        self.check_all_dirs()
        if self.job_type in ['mnmd5check','promd5check']:
            if not self.depapps:
                sys.exit("must input the depapps ! --depapps")
        # if self.job_type in [ 'stop', 'start', 'restart', 'checkport', 'deploy', 'config', 'all', 'tomcat','command' ]:
        if self.job_type in ['stop', 'start', 'restart', 'checkport', 'deploy', 'config', 'all', 'tomcat']:
            # print "host_file: %s" % self.host_file_path
            # print "group_var_file: %s" % self.group_var_path
            self.check_app()

        if self.job_type in ['deploy','all','mnmd5check','promd5check']:
            if not self.production:
                self.sync_file_and_config()
        if hasattr(self,self.job_type):
            fun = getattr(self,self.job_type)
            fun()

if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='Deploy Script')
    # parser.add_argument(
    #     '--job_type',
    #     type=str,
    #     help='input the job type  like "deploy config all"',
    #     required=True,
    #     choices=[
    #         'stop',
    #         'start',
    #         'restart',
    #         'checkport',
    #         'deploy',
    #         'config',
    #         'all',
    #         'tomcat',
    #         'build',
    #         'md5check',
    #         'sync2pro',
    #         'command',
    #         'mnmd5check',
    #         'promd5check',
    #         'sendmail'
    #     ]
    # )
    # parser.add_argument('--envid', type=str,  help='input the envirment id like 147')
    # parser.add_argument('--depapps', type=str,  help='input the project name like all or fmbos,fmcacheserver')
    # parser.add_argument('--mailtype', type=str,  help='input the mailgroup like admin,test,develop')
    # parser.add_argument('--package_file', type=str,  help='input the project name like : fmbos.war')
    # parser.add_argument('--build_number', type=int,  help='input the job build  number')
    # parser.add_argument('--debug', dest='debug', action='store_true')
    # parser.add_argument('--production', dest='production', action='store_true')
    # parser.add_argument('--mavenbase', dest='mavenbase', action='store_true')
    # parser.add_argument('--ant', dest='ant', action='store_true')
    # parser.add_argument('--command_args', type=str,  help='input the command_args like : ls pwd')
    # parser.add_argument('--src_job_dir', type=str, help='get code and configuration from this job in deploy.')
    # parser.add_argument('--is_jar', dest='is_jar', action='store_true')
    #
    #
    #
    #
    #
    # args = parser.parse_args()
    d = {'job_type': 'all', 'envid': '119', 'depapps': 'fcs4exchange', 'mailtype': None, 'package_file': None,
     'build_number': 8, 'debug': False, 'production': False, 'mavenbase': False, 'ant': False, 'command_args': None, 'src_job_dir': None, 'is_jar': False}
    deploy_handler = DeployHandler(**d)

    deploy_handler.run()



