from django import forms
from .models import Vehicle

class VehicleForm(forms.ModelForm):
    class Meta:

        model = Vehicle 
        fields = ['name', 'vehicle_number', 'vehicle_type','fuel_type','last_service_date', 'service_interval_days']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter vehicle name'}),
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. MH12AB1234'}),
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
            'fuel_type': forms.Select(attrs={'class': 'form-select'}),
            'last_service_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'service_interval_days': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 90'}),
        }