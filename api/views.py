from django.shortcuts import render,reverse
from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.authentication import SessionAuthentication, BasicAuthentication,TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from dpinfo.filters import CustomFilterBackend
from jkmgr.models import JenkinsJob
from dpinfo.models import HostEnvironmentRelation
from dpinfo.serializers import HostEnvironmentRelationSerializer
from jkmgr.serializers import JenkinsJobSerializer
from jkmgr.filters import JenkinsJobCustomFilterBackend

# Create your views here.


class HostEnvironmentRelationViewset(viewsets.GenericViewSet,mixins.ListModelMixin):
    queryset = HostEnvironmentRelation.objects.all()
    serializer_class = HostEnvironmentRelationSerializer
    authentication_classes  = (SessionAuthentication,TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,CustomFilterBackend,OrderingFilter)
    filter_fields = ('environment__environment_name', )
    ordering_fields = ('priority',)
    ordering = ('-priority',)


class JenkinsJobViewset(viewsets.GenericViewSet,mixins.ListModelMixin):
    queryset = JenkinsJob.objects.all()
    serializer_class = JenkinsJobSerializer
    authentication_classes  = (SessionAuthentication,TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    filter_backends = (JenkinsJobCustomFilterBackend,)



