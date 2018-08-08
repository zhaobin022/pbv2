# Generated by Django 2.1 on 2018-08-02 08:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dpinfo', '0003_hostenvironmentrelation_priority'),
    ]

    operations = [
        migrations.CreateModel(
            name='JenkinsJob',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_name', models.CharField(max_length=128, verbose_name='job名称')),
                ('job_type', models.PositiveIntegerField(choices=[(0, '功能测试部署(FUN)'), (1, '用户验收测试部署(UAT)'), (2, '构建'), (3, '通过测试'), (4, '生产准备'), (5, '可选类型'), (6, '生产部署'), (7, '生产起停')], default=2)),
                ('auto_build', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='JenkinsServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('server_name', models.CharField(max_length=128)),
                ('ip', models.GenericIPAddressField()),
                ('username', models.CharField(max_length=64)),
                ('password', models.CharField(blank=True, max_length=256, null=True)),
                ('token', models.CharField(max_length=256)),
                ('api_url', models.URLField()),
                ('workspace', models.CharField(blank=True, max_length=256, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operation_name', models.CharField(max_length=128)),
                ('operation_value', models.CharField(max_length=64)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='operation',
            unique_together={('operation_name', 'operation_value')},
        ),
        migrations.AddField(
            model_name='jenkinsjob',
            name='action_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='jkmgr.Operation'),
        ),
        migrations.AddField(
            model_name='jenkinsjob',
            name='emails',
            field=models.ManyToManyField(blank=True, to='dpinfo.EmailList'),
        ),
        migrations.AddField(
            model_name='jenkinsjob',
            name='environment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='dpinfo.Environment'),
        ),
        migrations.AddField(
            model_name='jenkinsjob',
            name='jenkins_server',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jkmgr.JenkinsServer'),
        ),
        migrations.AddField(
            model_name='jenkinsjob',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_jobs', to='dpinfo.Project', verbose_name='项目名'),
        ),
        migrations.AlterUniqueTogether(
            name='jenkinsjob',
            unique_together={('job_name', 'project')},
        ),
    ]