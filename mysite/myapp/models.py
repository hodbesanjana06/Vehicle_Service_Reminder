from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.core.validators import RegexValidator

mobile_validator = RegexValidator(
    regex=r'^[6-9]\d{9}$',
    message="Enter a valid 10-digit mobile number starting with 6-9."

)
# ______________Vehicle____________________________
class Vehicle(models.Model):
    vehicle_type_choices =[
        ('car', 'Car'),
        ('bike', 'Bike'),
        ('scooter', 'Scooter'),
        ('truck', 'Truck'),
        ('bus', 'Bus'),
        ('jeep', 'Jeep'),
        ('auto', 'Auto'),
    ]

    fuel_type_choices = [
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('cng', 'CNG'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=40)
    vehicle_number = models.CharField(max_length=20)
    last_service_date = models.DateField()
    service_interval_days = models.IntegerField()
    vehicle_type = models.CharField(max_length=20, choices=vehicle_type_choices , default='Bike')
    fuel_type = models.CharField(max_length=20, choices=fuel_type_choices , default='Petrol')

    def next_service_date(self):
        return self.last_service_date + timedelta(days=self.service_interval_days)
    
    def __str__(self):
        return f"{self.name} ({self.vehicle_number})"


# _________________Garage___________________________

class Garage(models.Model):
    name = models.CharField(max_length=20)
    city = models.CharField(max_length=10)
    location = models.CharField(max_length=30)
    lat = models.FloatField(default=0.0)
    lng = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.name} - {self.city}"


#____________________________ServiceBooking_______________________ 


class ServiceBooking(models.Model):
    service_choices = [
        ('oil_change', 'Oil Change'),
        ('tire_rotation', 'Tire Rotation'),
        ('battery_check', 'Battery Check'),
        ('brake_check', 'Brake Check'),
        ('engine_check', 'Engine Check'),
        ('wheel_alignment', 'Wheel Alignment'),
        ('air_filter_change', 'Air Filter Change'),
    ]

    timeslot_choices = [
        ('9-1', '9 AM - 1 PM'),
        ('1-5', '1 PM - 5 PM'),
        ('6-10', '6 PM - 10 PM'),
    ]

    pickup_drop_choices = [
        ('no', 'No'),
        ('pickup_only', 'Pickup Only'),
        ('drop_only', 'Drop Only'),
        ('both', 'Both'),
    ]
    garage = models.ForeignKey(Garage, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    service_type = models.CharField(max_length=20, choices=service_choices)
    service_date = models.DateField()
    city = models.CharField(max_length=20, blank=True, null=True)
    timeslot = models.CharField(max_length=10, choices=timeslot_choices ,blank=True, null=True)
    pickup_drop = models.CharField(max_length=20, choices=pickup_drop_choices, default='no')
    pickup_drop_address = models.TextField(blank=True, null=True)
    additional_note = models.TextField(blank=True, null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)

    
    def __str__(self):
        return f"{self.get_service_type_display()} - {self.vehicle.name}"
    

#  ______________User Profile____________________________________
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=10, blank=True, null=True, validators=[mobile_validator])
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.username