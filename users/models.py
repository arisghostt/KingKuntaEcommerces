from django.contrib.auth.models import AbstractUser, Group
from django.db import models


class CustomUser(AbstractUser):
    tenant = models.ForeignKey('core.Tenant', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=120, blank=True, default='')
    bio = models.TextField(blank=True, default='')

    @property
    def domain_user_id(self):
        return self.tenant_id

    @property
    def role(self):
        group = self.groups.order_by('id').first()
        return group.name if group else ''

    @property
    def role_obj(self):
        return self.groups.order_by('id').first()

    @property
    def is_superadmin(self):
        if self.is_superuser:
            return True
        group = self.role_obj
        return group.name in ['superadmin', 'administrator'] if group else False



class RoleProfile(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='profile')
    description = models.TextField(blank=True)
    color = models.CharField(max_length=30, default='bg-gray-500')

    def __str__(self):
        return f'RoleProfile<{self.group.name}>'


class Module(models.Model):
    module_name = models.CharField(max_length=100)
    module_url = models.CharField(max_length=200, unique=True)
    is_menu = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.module_name


class RolePermission(models.Model):
    role = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='module_permissions')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    is_view = models.BooleanField(default=False)
    is_add = models.BooleanField(default=False)
    is_edit = models.BooleanField(default=False)
    is_delete = models.BooleanField(default=False)

    class Meta:
        unique_together = ['role', 'module']

    def __str__(self):
        return f'{self.role.name} → {self.module.module_name}'


class UserPermission(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='module_permissions')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    is_view = models.BooleanField(default=False)
    is_add = models.BooleanField(default=False)
    is_edit = models.BooleanField(default=False)
    is_delete = models.BooleanField(default=False)
    domain_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='domain_permissions')

    class Meta:
        unique_together = ['user', 'module']

    def __str__(self):
        return f'{self.user.username} - {self.module.module_name}'
