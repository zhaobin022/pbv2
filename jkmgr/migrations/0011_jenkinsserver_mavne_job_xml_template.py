# Generated by Django 2.1 on 2018-08-09 02:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jkmgr', '0010_jenkinsserver_job_xml_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='jenkinsserver',
            name='mavne_job_xml_template',
            field=models.TextField(blank=True, null=True),
        ),
    ]
