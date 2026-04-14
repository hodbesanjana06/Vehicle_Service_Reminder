from django.contrib import admin
from .models import Vehicle, ServiceBooking, Garage
# Register your models here.
admin.site.register(Vehicle)
admin.site.register(ServiceBooking)
admin.site.register(Garage)