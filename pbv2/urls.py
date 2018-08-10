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
from django.contrib import admin
from django.urls import path
from django.conf.urls import url,include
from rest_framework.authtoken import views

from .views import IndexView,LoginView,GetValidImgView



urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^api-auth/', include('rest_framework.urls')),
    url(r'^api/', include('api.urls')),
    url(r'^api-token-auth/', views.obtain_auth_token),
    url(r'^$', IndexView.as_view(),name='index'),
    url(r'^login$', LoginView.as_view(),name='user_login'),
    url(r'^get_valid_img',GetValidImgView.as_view(),name='get_valid_img'),
]
