# Generated by Django 4.1.2 on 2022-11-01 10:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_alter_user_role'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='administratorprofile',
            name='administrator_id',
        ),
        migrations.RemoveField(
            model_name='operatorprofile',
            name='operator_id',
        ),
        migrations.RemoveField(
            model_name='supervisorprofile',
            name='Supervisor_id',
        ),
    ]