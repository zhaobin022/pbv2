from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.db.models import Q
import json
from django.core.paginator import Paginator
from copy import deepcopy


from .models import JenkinsServer,JenkinsJob
from dpinfo.models import Project,Group,HostEnvironmentRelation,Environment
from pbv2.utils import CustomPaginator
from .forms import BuildJenkinsJobForm
from utils.jenkins_api import JenkinsApi


# Create your views here.

class CustomView(View):


    constant_dict = {}

    global_choices_dict = {}

    @property
    def queryset(self):

        qs = self.model.objects.all()

        return qs


    def quseryset_filter(self,request):
        search = request.GET.get("search", "")
        search_dict = json.loads(search)
        values = []

        qs = self.queryset
        for i in self.table_config:
            if i['q']:
                values.append(i['q'])
        conn = Q()

        data_list = []
        if not qs:
            return data_list
        if search_dict['q']:

            for i in values:
                conn.add(Q(**{'{}__icontains'.format(i): search_dict['q']}), Q.OR)

            data_list = list(qs.filter(conn).values(*values))
        else:
            data_list = list(qs.values(*values))
        return data_list

    def ajax(self,request):
        data_list = self.quseryset_filter(request)

        p = CustomPaginator(data_list, request, page_size=2)
        page_content = p.gen_page_html()

        ret = {
            'table_config': self.table_config,
            'data_list': p.get_current_page_object_list(),
            'page_content': page_content,
            'search_config' : self.search_config,
            'global_choices_dict': self.global_choices_dict,
            'constant_dict':self.constant_dict,
        }

        return ret

    def get(self,request):

        self._request = request


        if request.is_ajax():
            return JsonResponse(self.ajax(request))
        return render(request,self.url)


class JobListView(View):
    url = 'jkmgr/job_list.html'
    model = JenkinsJob
    constant_dict = {}
    search_config = [
        {

            'id': 'q',
            'bind': 'change',
            'mode':'global',
            'type':'input',
        },
    ]

    global_choices_dict = {
        'job_type_choice': model.job_type_choice
    },

    table_config = [
        {
            'q': 'id',
            "display": True,
            'title': 'ID',
        },
        {
            'q': 'job_name',
            "display": True,
            'title': 'job名',
        },
        {
            'q': 'job_type',
            "display": True,
            'title': 'job类型',
            'text': {'tpl': '{a1}', 'kwargs': {'a1': '@@job_type_choice'}},
        },
        {
            'q': None,
            "display": True,
            'title': '操作',
            'text': {
                'tpl': '''<a class="btn btn-primary btn-sm" href="/jkmgr/job_detail/{pid}/{sid}/{id}/">详情</a>''',
                'kwargs': {'id': '@id','pid':'@@@pid','sid':'@@@sid'}
            },
        },
    ]

    @property
    def queryset(self):

        qs = self.model.objects.all()

        return qs

    def quseryset_filter(self,request,table_name):
        search = request.GET.get("{}_search".format(table_name), "")
        if search:
            search_dict = json.loads(search)
        values = []

        qs = self.queryset
        if table_name == 't1':
            qs = qs.filter(job_type=2)
        elif table_name == 't2':
            qs = qs.exclude(job_type=2)
        for i in self.table_config:
            if i['q']:
                values.append(i['q'])
        conn = Q()
        if search:
            if  search_dict[table_name+'_q']:

                for i in values:
                    conn.add(Q(**{'{}__icontains'.format(i): search_dict[table_name+'_q']}), Q.OR)

                data_list = list(qs.filter(conn).values(*values))
            else:
                data_list = list(qs.values(*values))
        else:
            data_list = list(qs.values(*values))
        return data_list

    def ajax(self, request):
        t1_data_list = self.quseryset_filter(request,'t1')

        p1 = CustomPaginator(t1_data_list, request, page_key='t1_page',page_size=2)
        p1_page_content = p1.gen_page_html()


        t2_data_list = self.quseryset_filter(request,'t2')

        p2 = CustomPaginator(t2_data_list,request,page_key='t2_page' , page_size=2)
        p2_page_content = p2.gen_page_html()

        ret = {
            't1': {
                'data_list': p1.get_current_page_object_list(),
                'page_content': p1_page_content,
            },
            't2':{
                'data_list': p2.get_current_page_object_list(),
                'page_content': p2_page_content,
            },
            'table_config': self.table_config,
            'search_config': self.search_config,
            'global_choices_dict': self.global_choices_dict,
            'constant_dict': self.constant_dict,
        }

        return ret

    def get(self,request,pid,sid):
        self.constant_dict['pid'] = pid
        self.constant_dict['sid'] = sid

        if request.is_ajax():
            return JsonResponse(self.ajax(request))
        return render(request,'jkmgr/job_list.html',{'pid':pid,'sid':sid})


class JenkinsResultView(View):


    def get(self,request,jid):

        if request.is_ajax():
            ret = {
                'status':False,
                'msg':''
            }
            job_obj = JenkinsJob.objects.filter(id=jid).first()
            bid = request.GET.get('bid','')
            if job_obj and bid:
                jk_handler = JenkinsApi(jsever_obj=job_obj.jenkins_server)
                ret = jk_handler.get_build_console_output(job_obj.job_name,bid)
            else:
                ret['msg'] = 'get job failed !'
            return JsonResponse(ret)


class JobDetailView(View):

    def change_email(self,request):
        ret = {
            'status': False,
            'msg': ''
        }
        try:
            emails = request.GET.getlist('emails', '')
            job_obj = JenkinsJob.objects.filter(id=id).first()
            job_obj.emails.set(emails)
            ret['status'] = True
            ret['msg'] = '修改成功'
        except Exception as e:
            ret['msg'] = '修改失败'
        return ret

    def get(self,request,pid,sid,id):
        if request.is_ajax():
            ret = self.change_email(request)
            return JsonResponse(ret)


        j_obj = JenkinsJob.objects.filter(id=id).first()
        email_list = j_obj.emails.all().values_list('email')
        email_list = [ i[0] for i in email_list ]
        email_str = ','.join(email_list)

        her = HostEnvironmentRelation.objects.filter(environment__hostenvironmentrelation__project_id=pid).distinct().values_list('group__id','group__name')
        a = j_obj.action_list.all()

        if j_obj:
            j_form = BuildJenkinsJobForm(instance=j_obj)



        return render(request,'jkmgr/job_detail.html',locals())


    def post(self,request,pid,sid,id):

        if request.is_ajax():
            group_list = request.POST.getlist('group_list','')
            operation = request.POST.get('operation','')
            environment = request.POST.get('environment','')
            ret = {
                'status':False,
                'msg':''
            }
            group_list = [ i[0] for i in Group.objects.filter(id__in=group_list).values_list('name') ]
            environment =  Environment.objects.filter(pk=environment).first().environment_name
            if group_list and operation and environment:
                j_obj = JenkinsJob.objects.filter(pk=id).first()
                if j_obj:
                    parameters = {'group_list':','.join(group_list),'operation':operation,'environment':environment}
                    jkh = JenkinsApi(j_obj.jenkins_server)
                    build_number,building = jkh.build_job(j_obj.job_name,parameters)
                    ret['status'] = True
                    ret['build_number'] = build_number
                    ret['building'] = building
                else:
                    ret['msg'] = 'no job find'

            else:
                ret['msg'] = '参数不全'


            return JsonResponse(ret)



class ServerListView(CustomView):
    url = 'jkmgr/jk_server_list.html'
    model = JenkinsServer
    search_config = [
        {

            'id': 'q',
            'bind': 'change',
            'mode':'global',
            'type':'input',
        },
    ]


    table_config = [
        {
            'q': 'id',
            "display": True,
            'title': 'ID',
        },
        {
            'q': 'server_name',
            "display": True,
            'title': '服务器名',
        },
        {
            'q': 'ip',
            "display": True,
            'title': 'IP地址',
        },
        {
            'q': 'api_url',
            "display": True,
            'title': '接口地址',
            'text': {
                'tpl': '''<a  href="{href}" target="_blank">{href}</a>''',
                'kwargs':{'href':'@api_url'},
            },
        },
        {
            'q': 'workspace',
            "display": True,
            'title': '工作目录',
        },
        {
            'q': None,
            "display": True,
            'title': '操作',
            'text': {
                'tpl': '''<a class="btn btn-primary btn-sm" href="/jkmgr/project_list/{id}/">详情</a>''',
                'kwargs': {'id': '@id'}
            },
        },
    ]


class ProjectListView(CustomView):
    constant_dict = {}
    url = 'jkmgr/project_list.html'
    model = Project


    search_config = [
        {

            'id': 'q',
            'bind': 'change',
            'mode':'global',
            'type':'input',
        },
    ]


    table_config = [
        {
            'q': 'id',
            "display": True,
            'title': 'ID',
        },
        {
            'q': 'name',
            "display": True,
            'title': '项目名',
        },
        {
            'q': 'version__name',
            "display": True,
            'title': '版本',
            'text': {
                'tpl': '''{version}''',
                'kwargs': {'version': '@version__name'}
            },
        },
        {
            'q': None,
            "display": True,
            'title': '操作',
            'text': {
                'tpl': '''<a class="btn btn-primary btn-sm" href="/jkmgr/job_list/{pid}/{sid}/">详情</a>''',
                'kwargs': {'pid': '@id','sid':'@@@sid'}
            },
        },
    ]

    @property
    def queryset(self):

        jb_qs = JenkinsJob.objects.filter(jenkins_server__id = self.sid)
        if jb_qs:
            ids = jb_qs.values_list('project_id').distinct()
            project_qs = Project.objects.filter(id__in=ids)
        else:
            project_qs= []
        return project_qs


    def get(self,request,sid):
        self.sid = sid
        self.constant_dict['sid'] = sid
        if request.is_ajax():
            return JsonResponse(self.ajax(request))
        return render(request,self.url,{'sid':sid})



class BuildListView(View):

    table_config = [
        {
            'q': 'number',
            "display": True,
            'title': 'BID',
        },
        {
            'q': 'url',
            "display": True,
            'title': 'BUILD URL',
        },
        {
            'q': None,
            "display": True,
            'title': '操作',
            'text': {
                'tpl': '''<a class="btn btn-primary btn-sm" number="{id}">详情</a>''',
                'kwargs': {'id': '@number'}
            },
        }
    ]

    def get(self,request,id):

        j_obj = JenkinsJob.objects.filter(pk=id).first()

        id = j_obj.pk
        pid = j_obj.project.pk
        sid = j_obj.jenkins_server.pk
        if request.is_ajax():


            jk_handler = JenkinsApi(j_obj.jenkins_server)
            job_info_dict = jk_handler.server.get_job_info(j_obj.job_name)
            buid_info_list = job_info_dict['builds']


            p = CustomPaginator(buid_info_list, request, page_size=4)
            page_content = p.gen_page_html()

            ret = {
                'table_config': self.table_config,
                'data_list': p.get_current_page_object_list(),
                'page_content': page_content,
            }

            return JsonResponse(ret)

        return render(request,'jkmgr/build_list.html',locals())