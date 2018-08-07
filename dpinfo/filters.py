from rest_framework import filters
from jkmgr.models import JenkinsJob


class CustomFilterBackend(filters.BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """
    def filter_queryset(self, request, queryset, view):
        job_name = request.query_params.get('job_name', None)
        jenkins_server_id = request.query_params.get('jenkins_server_id', None)

        jjob = JenkinsJob.objects.filter(job_name=job_name,jenkins_server_id=jenkins_server_id).first()
        if jjob:
            project_obj = jjob.project
            return queryset.filter(project=project_obj)
        else:
            return None