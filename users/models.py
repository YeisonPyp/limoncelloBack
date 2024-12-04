from django.db import models

# Create your models here.
class People(models.Model):
    person_id = models.AutoField(primary_key=True, db_column='person_id')
    identification = models.CharField(max_length=20, db_column='identification')
    first_name = models.CharField(max_length=100, db_column='first_name')
    second_name = models.CharField(max_length=100, blank=True, null=True, db_column='second_name')
    first_last_name = models.CharField(max_length=100, db_column='first_last_name')
    second_last_name = models.CharField(max_length=100, blank=True, null=True, db_column='second_last_name')
    date_of_birth = models.DateField(db_column='date_of_birth')
    phone_number = models.CharField(max_length=100, blank=True, null=True, db_column='phone_number')
    email = models.EmailField(db_column='email')
    send_email = models.BooleanField(default=False, db_column='send_email')
    creation_date = models.DateTimeField(auto_now_add=True, db_column='creation_date')
    modification_date = models.DateTimeField(auto_now=True, db_column='modification_date')

    def __str__(self):
        return self.first_name + ' ' + self.first_last_name
    
    class Meta:
        db_table = 'People'
        verbose_name = 'Person'
        verbose_name_plural = 'People'
        unique_together = ('identification', 'email')


class Users(models.Model):
    user_id = models.AutoField(primary_key=True, db_column='user_id')
    username = models.CharField(max_length=100, db_column='username')
    password_hash = models.CharField(max_length=255, db_column='password_hash')
    is_locked = models.BooleanField(default=False, db_column='is_locked')
    is_active = models.BooleanField(default=False, db_column='is_active')
    person_id = models.ForeignKey(People, on_delete=models.CASCADE, db_column='person_id')
    creation_date = models.DateTimeField(auto_now_add=True, db_column='creation_date')
    modification_date = models.DateTimeField(auto_now=True, db_column='modification_date')

    def __str__(self):
        return self.username
    
    class Meta:
        db_table = 'Users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'