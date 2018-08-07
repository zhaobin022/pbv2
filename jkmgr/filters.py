from rest_framework import filters
from jkmgr.models import JenkinsJob


class JenkinsJobCustomFilterBackend(filters.BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """
    def filter_queryset(self, request, queryset, view):
        job_name = request.query_params.get('job_name', None)
        jenkins_server_id = request.query_params.get('jenkins_server_id', None)
        if job_name and jenkins_server_id:
            return queryset.filter(job_name=job_name,jenkins_server_id=jenkins_server_id)
        else:
            return []