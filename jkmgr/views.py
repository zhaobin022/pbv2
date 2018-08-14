from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.db.models import Q
from django.core.paginator import Paginator
from copy import deepcopy


from .models import JenkinsServer
from pbv2.utils import CustomPaginator

# Create your views here.

class ServerListView(View):
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
            'text': {'tpl': '''<a class="btn btn-primary btn-sm" href="/jkmgr/job_list/{id}/">详情</a>''',
                     'kwargs': {'id': '@id'}},
        },
    ]

    def get(self,request):

        if request.is_ajax():
            import time


            search = request.GET.get("search", "")

            values = []
            for i in self.table_config:
                if i['q']:
                    values.append(i['q'])
            conn = Q()

            if search:
                for i in values:
                    conn.add(Q(**{'{}__icontains'.format(i): search}), Q.OR)

            data_list = list(JenkinsServer.objects.filter(conn).values(*values))

            p = CustomPaginator(data_list, request,page_size=2)
            page_content = p.gen_page_html()


            ret = {
                'table_config': self.table_config,
                'data_list': p.get_current_page_object_list(),
                'page_content': page_content,
            }
            return JsonResponse(ret)

        return render(request,'jkmgr/jk_server_list.html')


