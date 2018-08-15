from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.db.models import Q
import json
from django.core.paginator import Paginator
from copy import deepcopy


from .models import JenkinsServer,JenkinsJob
from dpinfo.models import Project,Version
from pbv2.utils import CustomPaginator

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
                'tpl': '''<a class="btn btn-primary btn-sm" href="/jkmgr/job_detail/{id}/">详情</a>''',
                'kwargs': {'id': '@id'}
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

        p1 = CustomPaginator(t1_data_list, request, page_size=2)
        p1_page_content = p1.gen_page_html()


        t2_data_list = self.quseryset_filter(request,'t2')

        p2 = CustomPaginator(t2_data_list, request, page_size=2)
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

        if request.is_ajax():
            return JsonResponse(self.ajax(request))
        return render(request,'jkmgr/job_list.html',{'pid':pid,'sid':sid})


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
