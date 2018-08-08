from rest_framework import serializers
from rest_framework import filters
from dpinfo import models
from jkmgr.models import JenkinsJob


class AppVariablesSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.AppVariables
        fields = "__all__"

class DbVariablesSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.DbVariables
        fields = "__all__"

class EnvironmentSerializer(serializers.ModelSerializer):
    app_var = AppVariablesSerializer(many=True)
    db_var = DbVariablesSerializer(many=True)
    class Meta:
        model = models.Environment
        fields = "__all__"

class AnsibleGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Group
        fields = "__all__"



class TomcatSerializer(serializers.ModelSerializer):
    http_type = serializers.SerializerMethodField()

    def get_http_type(self, obj):

        return obj.get_http_type_display()

    class Meta:
        model = models.Tomcat
        fields = "__all__"


class HostSerializer(serializers.ModelSerializer):
    host_type = serializers.SerializerMethodField()
    def get_host_type(self,obj):

        return obj.get_host_type_display()



    class Meta:
        model = models.Hosts
        fields = "__all__"


class VersionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Version
        fields = "__all__"


class ProjectSerializer(serializers.ModelSerializer):
    version = VersionSerializer(many=False)

    class Meta:
        model = models.Project
        fields = "__all__"


# class TemplatesSerializer(serializers.ModelSerializer):
#     name = serializers.SerializerMethodField()
#
#     def get_name(self, obj):
#
#         return obj.name

    class Meta:
        model = models.Templates
        fields = ("name",)




class HostEnvironmentRelationSerializer(serializers.ModelSerializer):

    """
    部署详解信息
    """

    environment  = EnvironmentSerializer(many=False)
    group = AnsibleGroupSerializer(many=False)
    tomcat = TomcatSerializer(many=False)
    hosts = HostSerializer(many=True)
    group_type = serializers.SerializerMethodField()
    templates = serializers.SerializerMethodField()
    app_variables = AppVariablesSerializer(many=True)
    db_variables = DbVariablesSerializer(many=True)

    def get_group_type(self, obj):

        return obj.get_group_type_display()

    def get_templates(self,obj):
        templates = obj.templates.all()
        return [x.name  for x in templates]

    class Meta:
        model = models.HostEnvironmentRelation
        # fields = ("environment","group","app_foot","group_type","tomcat","hosts","project","priority",)
        fields = "__all__"
