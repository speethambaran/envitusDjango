from ast import operator
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    class Role(models.TextChoices):
        OPERATOR = "OPERATOR", "Operator"
        ADMINISTRATOR = "ADMINISTRATOR", "Administrator"
        SUPERVISOR = "SUPERVISOR", "Supervisor"
        SUPERADMIN = "SUPERADMIN", "Superadmin"

    base_role = Role.OPERATOR

    role = models.CharField(max_length=50, choices=Role.choices)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.role = self.base_role
            return super().save(*args, **kwargs)


class AdministratorManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=User.Role.ADMINISTRATOR)


class Administrator(User):
    base_role = User.Role.ADMINISTRATOR

    administrator = AdministratorManager()

    class Meta:
        proxy = True

    def welcome(self):
        return "Only for administrator"


@receiver(post_save, sender=Administrator)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role == "ADMINISTRATOR":
        AdministratorProfile.objects.create(user=instance)


class AdministratorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class SupervisorManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=User.Role.SUPERVISOR)


class Supervisor(User):
    base_role = User.Role.SUPERVISOR

    supervisor = SupervisorManager()

    class Meta:
        proxy = True

    def welcome(self):
        return "Only for supervisor"


class SupervisorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


@receiver(post_save, sender=Supervisor)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role == "SUPERVISOR":
        SupervisorProfile.objects.create(user=instance)


class SuperadminManger(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=User.Role.SUPERADMIN)


class Superadmin(User):
    base_role = User.Role.SUPERADMIN

    Superadmin = SuperadminManger()

    class Meta:
        proxy = True

    def welcome(self):
        return "Only for operator"


@receiver(post_save, sender=Superadmin)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role == "SUPERADMIN":
        SuperadminProfile.objects.create(user=instance)
    else:
        return ("error")


class SuperadminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
