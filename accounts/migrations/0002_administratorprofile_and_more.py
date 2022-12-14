# Generated by Django 4.1.1 on 2022-10-13 05:35

from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdministratorProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('administrator_id', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.RenameModel(
            old_name='StudentProfile',
            new_name='SupervisorProfile',
        ),
        migrations.RemoveField(
            model_name='teacherprofile',
            name='user',
        ),
        migrations.DeleteModel(
            name='Student',
        ),
        migrations.DeleteModel(
            name='Teacher',
        ),
        migrations.CreateModel(
            name='Administrator',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('accounts.user',),
            managers=[
                ('administrator', django.db.models.manager.Manager()),
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Supervisor',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('accounts.user',),
            managers=[
                ('supervisor', django.db.models.manager.Manager()),
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.RenameField(
            model_name='supervisorprofile',
            old_name='student_id',
            new_name='teacher_id',
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('ADMIN', 'Admin'), ('ADMINISTRATOR', 'Administrator'), ('SUPERVISOR', 'Supervisor')], max_length=50),
        ),
        migrations.DeleteModel(
            name='TeacherProfile',
        ),
        migrations.AddField(
            model_name='administratorprofile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
