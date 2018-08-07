from rest_framework import serializers
from dpinfo import models
from jkmgr.models import JenkinsJob,JenkinsServer






class VersionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Version
        fields = "__all__"


class ProjectSerializer(serializers.ModelSerializer):
    version = VersionSerializer(many=False)

    class Meta:
        model = models.Project
        fields = "__all__"


class JenkinsServerSerializer(serializers.ModelSerializer):

    class Meta:
        model = JenkinsServer
        fields = "__all__"


class JenkinsJobSerializer(serializers.ModelSerializer):
    """
    jenkins job 详细信息
    """

    project = ProjectSerializer(many=False)
    jenkins_server = JenkinsServerSerializer(many=False)
    class Meta:
        model = JenkinsJob
        fields = "__all__"
