# Generated by Django 2.1 on 2018-08-09 01:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jkmgr', '0008_auto_20180809_0013'),
    ]

    operations = [
        migrations.AddField(
            model_name='jenkinsserver',
            name='svn_credentials_id',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='jenkinsserver',
            name='svn_xml_template',
            field=models.TextField(blank=True, null=True),
        ),
    ]
