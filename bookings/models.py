from django.db import models

class Campus(models.Model):
    campus_id = models.AutoField(primary_key=True, db_column='campus_id')
    name = models.CharField(max_length=100, db_column='name')
    address = models.CharField(max_length=150, db_column='address')
    phone = models.CharField(max_length=15, db_column='phone')
    email = models.EmailField(db_column='email')

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'Campus'
        verbose_name = 'Campus'
        verbose_name_plural = 'Campus'


class Booking(models.Model):
    booking_id = models.AutoField(primary_key=True, db_column='booking_id')
    person_id = models.ForeignKey('users.People', on_delete=models.CASCADE, db_column='person_id')
    campus_id = models.ForeignKey(Campus, on_delete=models.CASCADE, db_column='campus_id')
    people_amount = models.IntegerField(db_column='people_amount')
    booking_date = models.DateField(db_column='booking_date')
    booking_hour = models.TimeField(db_column='booking_hour')
    observations = models.TextField(blank=True, null=True, db_column='observations')
    active = models.BooleanField(default=True, db_column='active')
    approved = models.BooleanField(default=False, db_column='approved')
    creation_date = models.DateTimeField(auto_now_add=True, db_column='creation_date')
    
    class Meta:
        db_table = 'Booking'
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'

