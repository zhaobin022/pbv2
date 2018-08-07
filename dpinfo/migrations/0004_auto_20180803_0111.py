# Generated by Django 2.1 on 2018-08-03 01:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dpinfo', '0003_hostenvironmentrelation_priority'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appvariables',
            name='envirment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='app_var', to='dpinfo.Environment'),
        ),
        migrations.AlterField(
            model_name='dbvariables',
            name='envirment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='db_var', to='dpinfo.Environment'),
        ),
        migrations.AlterField(
            model_name='dbvariables',
            name='key',
            field=models.CharField(max_length=255, unique=True, verbose_name='数据库key'),
        ),
    ]
