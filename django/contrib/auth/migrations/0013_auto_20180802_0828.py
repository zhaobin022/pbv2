# Generated by Django 2.1 on 2018-08-02 08:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jkmgr', '0001_initial'),
        ('auth', '0012_auto_20180802_0533'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='jenkins_job',
            field=models.ManyToManyField(blank=True, to='jkmgr.JenkinsJob'),
        ),
        migrations.AddField(
            model_name='user',
            name='jenkins_job',
            field=models.ManyToManyField(blank=True, to='jkmgr.JenkinsJob'),
        ),
    ]
