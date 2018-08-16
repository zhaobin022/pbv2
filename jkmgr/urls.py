"""pbv2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.urls import path

from .views import ServerListView,JobListView,ProjectListView,JobDetailView


app_name='jkmgr'

urlpatterns = [
    url(r'server_list/', ServerListView.as_view(),name='server_list'),
    path('job_list/<int:pid>/<int:sid>/', JobListView.as_view(), name='job_list'),
    path('job_detail/<int:pid>/<int:sid>/<int:id>/', JobDetailView.as_view(), name='job_detail'),
    path('project_list/<int:sid>/', ProjectListView.as_view(), name='project_list'),
]
