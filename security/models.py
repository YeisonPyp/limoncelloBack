from django.db import models
from users.models import Users
from bookings.models import Campus


class Roles(models.Model):
    role_id = models.AutoField(primary_key=True, db_column='role_id')
    role_name = models.CharField(max_length=100, db_column='role_name')
    role_description = models.CharField(max_length=255, db_column='role_description')
    campus_id = models.ForeignKey(Campus, on_delete=models.CASCADE, db_column='campus_id')

    def __str__(self):
        return self.role_name
    
    class Meta:
        db_table = 'Roles'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'


class UserRoles(models.Model):
    user_role_id = models.AutoField(primary_key=True, db_column='user_role_id')
    user_id = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='user_id')
    role_id = models.ForeignKey(Roles, on_delete=models.CASCADE, db_column='role_id')

    class Meta:
        db_table = 'UserRoles'
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'
        unique_together = ('user_id', 'role_id')


class Permissions(models.Model):
    permission_cod = models.CharField(max_length=3, primary_key=True, db_column='permission_cod')
    permission_name = models.CharField(max_length=100, db_column='permission_name', unique=True)

    def __str__(self):
        return self.permission_name
    
    class Meta:
        db_table = 'Permissions'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'


class RolePermissions(models.Model):
    role_permission_id = models.AutoField(primary_key=True, db_column='role_permission_id')
    role_id = models.ForeignKey(Roles, on_delete=models.CASCADE, db_column='role_id')
    permission_cod = models.ForeignKey(Permissions, on_delete=models.CASCADE, db_column='permission_cod')

    class Meta:
        db_table = 'RolePermissions'
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'
        unique_together = ('role_id', 'permission_cod')

