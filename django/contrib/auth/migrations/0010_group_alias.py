# Generated by Django 2.1 on 2018-08-02 04:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='alias',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]
