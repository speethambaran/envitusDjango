from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super_Admin"
        ADMINISTRATOR = "ADMINISTRATOR", "Administrator"
        SUPERVISOR = "SUPERVISOR", "Supervisor"
        OPERATOR = "OPERATOR", "Operator"

    base_role = Role.SUPER_ADMIN

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

    student = AdministratorManager()

    class Meta:
        proxy = True

    def welcome(self):
        return "Only for administrators"



@receiver(post_save, sender=Administrator)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role == "ADMINISTRATOR":
        AdministratorProfile.objects.create(user=instance)


class AdministratorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    administrator_id = models.IntegerField(null=True, blank=True)


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
        return "Only for supervisors"


@receiver(post_save, sender=Supervisor)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role == "SUPERVISOR":
        SupervisorProfile.objects.create(user=instance)


class SupervisorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    Supervisor_id = models.IntegerField(null=True, blank=True)


class OperatorManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=User.Role.OPERATOR)


class Operator(User):
    base_role = User.Role.OPERATOR

    operator = OperatorManager()

    class Meta:
        proxy = True

    def welcome(self):
        return "Only for operators"


@receiver(post_save, sender=Operator)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role == "OPERATOR":
        OperatorProfile.objects.create(user=instance)


class OperatorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    operator_id = models.IntegerField(null=True, blank=True)


class SuperAdminManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=User.Role.SUPER_ADMIN)


class Super_Admin(User):
    base_role = User.Role.SUPER_ADMIN

    super_admin = SuperAdminManager()

    class Meta:
        proxy = True

    def welcome(self):
        return "Only for super admin"


class Super_Admin_Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    super_admin_id = models.IntegerField(null=True, blank=True)


@receiver(post_save, sender=Super_Admin)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role == "SUPER_ADMIN":
        Super_Admin_Profile.objects.create(user=instance)
