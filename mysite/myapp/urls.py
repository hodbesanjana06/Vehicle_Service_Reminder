from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [

    path('', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),

    path('dashboard/',views.dashboard, name='dashboard'),
    path('vehicle_list/', views.vehicle_list , name='vehicle_list'),
    path('add_vehicle/', views.add_vehicle, name='add_vehicle'),
    path('edit-vehicle/<int:id>/', views.edit_vehicle, name='edit_vehicle'),
    path('delete-vehicle/<int:id>/', views.delete_vehicle, name='delete_vehicle'),
    path('book_service/', views.book_service_table, name='book_service_table'),
    path('api/garages/', views.garage_list_api, name='garage_api'),
    path('book-service/<int:vehicle_id>/submit/', views.book_service_submit, name='book_service_submit'),
    path('book-service/<int:vehicle_id>/', views.book_service_form, name='book_service_form'),
    path('history/', views.booking_history, name='booking_history'),
    path('booking/<int:booking_id>/edit/', views.edit_booking, name='edit_booking'),
    path('booking/<int:booking_id>/delete/', views.delete_booking, name='delete_booking'),
    path('profile/', views.profile, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
]
