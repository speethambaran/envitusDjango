# Generated by Django 4.1.2 on 2022-11-08 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_rename_operatorprofile_superadminprofile_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('Operator', 'Operator'), ('Administrator', 'Administrator'), ('Supervisor', 'Supervisor'), ('Superadmin', 'Superadmin')], max_length=50),
        ),
    ]
