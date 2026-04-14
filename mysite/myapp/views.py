from django.shortcuts import render, redirect, get_object_or_404
from .models import Vehicle, ServiceBooking , Garage , UserProfile
from datetime import date, timedelta, datetime
from .forms import VehicleForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
import re
# ____________________Register________________________________

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('register')

        if password != confirm_password:
            messages.error(request, 'password do not match')
            return redirect('register')
        
        if not re.fullmatch(r'[6-9]\d{9}', mobile):
            messages.error(request, "Enter a valid 10-digit mobile number starting with 6-9.")
            return redirect('register')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        UserProfile.objects.create(
            user=user,
            mobile_number=mobile,
            address=address
        )
        messages.success(request, "Account created successfully")
        return redirect('login')

    return render(request, 'register.html')

# _______________Login___________________________________________

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'login.html')

# ______________________Logout_________________________________________

def user_logout(request):
    logout(request)
    return redirect('login')


# ______________________DASHBOARD___________________

@login_required
def dashboard(request):
    vehicles = Vehicle.objects.filter(user=request.user)
    bookings = ServiceBooking.objects.filter(user=request.user)

    total_vehicles = vehicles.count()
    total_services = bookings.count()

    upcoming_service = []
    active_alerts = []
    notifications = []

    today = date.today()

    for vehicle in vehicles:
        # ---------------------------
        # Check for upcoming booking
        # ---------------------------
        booking = ServiceBooking.objects.filter(
            vehicle=vehicle,
            user=request.user,
            service_date__gte=today
        ).order_by('service_date').first()

        if booking:
            service_date = booking.service_date
        else:
            service_date = vehicle.next_service_date()  # fallback if no booking

        days_left = (service_date - today).days

        # ---------------------------
        # STATUS SECTION
        # ---------------------------
        if days_left < 0:
            status = "Overdue"
            active_alerts.append({
                'name': vehicle.name,
                'vehicle_number': vehicle.vehicle_number,
                'next_date': service_date
            })

        elif days_left <= 7:
            status = "Due Soon"
            upcoming_service.append({
                'name': vehicle.name,
                'vehicle_number': vehicle.vehicle_number,
                'next_date': service_date,
                'days_left': days_left,
                'status': status
            })

        else:
            status = "Upcoming"
            upcoming_service.append({
                'name': vehicle.name,
                'vehicle_number': vehicle.vehicle_number,
                'next_date': service_date,
                'days_left': days_left,
                'status': status
            })

        # ---------------------------
        # NOTIFICATION SECTION
        # ---------------------------
        if days_left == 0:
            message = f"⏰ {vehicle.name} service is TODAY"
            priority = 1
            color = "text-danger"

        elif days_left == 1:
            message = f"⚠️ {vehicle.name} service is TOMORROW"
            priority = 2
            color = "text-warning"

        elif 2 <= days_left <= 30:
            message = f"🔔 {vehicle.name} service is in {days_left} days"
            priority = 3
            color = "text-info"

        else:
            continue  # skip overdue or far-future

        notifications.append({
            'message': message,
            'color': color,
            'priority': priority
        })

    # ---------------------------
    # Sort notifications by priority and limit to 5
    # ---------------------------
    notifications = sorted(notifications, key=lambda x: x['priority'])[:5]

    context = {
        'total_vehicles': total_vehicles,
        'total_services': total_services,
        'upcoming_services': upcoming_service,
        'active_alerts': active_alerts,
        'notifications': notifications,
    }

    return render(request, 'dashboard.html', context)

# ________________________________ADD VEHICLE__________________________________
@login_required
def add_vehicle(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.user = request.user
            vehicle.save()
            return redirect('dashboard')
    else:
        form = VehicleForm()
    return render(request, 'add_vehicle.html', {'form':form})

# ______________Vehicle List____________________________________________________
@login_required
def vehicle_list(request):
    
    vehicles = Vehicle.objects.filter(user=request.user)

    return render(request, 'vehicle_list.html', {'vehicles':vehicles, 'today':date.today()})

# ___________________Edit Vehicle______________________________________
@login_required
def edit_vehicle(request, id):
    vehicle = Vehicle.objects.get(id=id, user=request.user)

    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            return redirect('vehicle_list')
    else:
        form = VehicleForm(instance=vehicle)
    
    return render(request, 'add_vehicle.html',{'form':form})
# _____________________Delete Vehicle__________________
@login_required
def delete_vehicle(request, id):
    vehicle = Vehicle.objects.get(id=id, user= request.user)
    vehicle.delete()
    return redirect('vehicle_list')


# __________________booking service table_________________________
@login_required
def book_service_table(request):
    vehicles = Vehicle.objects.filter(user=request.user)
    today = timezone.now().date()
    due_soon_date = today + timedelta(days=7)

     #  Attach latest booking to each vehicle
    for v in vehicles:
        booking = ServiceBooking.objects.filter(
            vehicle=v,
            user=request.user
        ).order_by('-service_date').first()

        v.latest_booking = booking  # important

    return render(request, 'book_service_table.html', {
        'vehicles': vehicles,
        'today': today,
        'due_soon_date': due_soon_date
    })

# _____________Garage API________________________________
@login_required
def garage_list_api(request):
    city = request.GET.get('city')
    garages = Garage.objects.all()
    if city:
        garages = garages.filter(city__iexact=city)

    data = [
        {
            "id":g.id,
            "name": g.name,
            "location": g.location,
            "lat":g.lat,
            "lng": g.lng,

        }for g in garages
    ]
    return JsonResponse(data, safe=False)


# _______________(booking submmit)save Garage_______________________

@login_required
def book_service_submit(request, vehicle_id):

    vehicle = get_object_or_404(Vehicle, id=vehicle_id, user=request.user)

    city = request.POST.get("city")
    service_type = request.POST.get("service_type")
    service_date = request.POST.get("service_date")
    timeslot = request.POST.get("timeslot")
    pickup_drop = request.POST.get("pickup_drop")
    pickup_drop_address = request.POST.get("pickup_drop_address")
    additional_note = request.POST.get("additional_note")
    garage_id = request.POST.get("garage")

    if not all([city, service_type, service_date, timeslot, garage_id]):
        messages.error(request, "Please fill all required fields.")
        return redirect('book_service_form', vehicle_id=vehicle.id)

    # Validate date
    try:
        service_date_obj = datetime.strptime(service_date, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Invalid date format.")
        return redirect('book_service_form', vehicle_id=vehicle.id)

    if service_date_obj < date.today():
        messages.error(request, "Service date cannot be in the past.")
        return redirect('book_service_form', vehicle_id=vehicle.id)

    # Pickup/drop address validation
    if pickup_drop != "no" and not pickup_drop_address:
        messages.error(request, "Pickup/Drop address is required.")
        return redirect('book_service_form', vehicle_id=vehicle.id)

    # Get garage object
    garage = get_object_or_404(Garage, id=garage_id) if garage_id else None

    # Save booking
    booking = ServiceBooking.objects.create(
        user=request.user,
        vehicle=vehicle,
        service_type=service_type,
        service_date=service_date_obj,
        city=city,
        timeslot=timeslot,
        pickup_drop=pickup_drop,
        pickup_drop_address=pickup_drop_address,
        additional_note=additional_note,
        garage=garage,  # <-- now we save the garage
    )
    # Send Email
    subject = "Service Booking Confirmation"
    message = f"""
    Hello {request.user.username},

    Your vehicle service has been successfully booked.

    Details:
    Vehicle: {vehicle.name} ({vehicle.vehicle_number})
    Service: {booking.get_service_type_display()}
    Date: {service_date_obj}
    Time Slot: {timeslot}
    City: {city}
    Garage: {garage.name if garage else "N/A"}

    Thank you for using our service 🚗
    """

    send_mail(
    subject,
    message,
    settings.EMAIL_HOST_USER,
    [request.user.email],
    fail_silently=False,
    )

    messages.success(request, "Service booked successfully! Confirmation email sent.")
    return redirect('booking_history')

@login_required
def book_service_form(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, user=request.user)
    context = {
        'vehicle':vehicle,
        'service_choices':ServiceBooking.service_choices,
        'timeslot_choices':ServiceBooking.timeslot_choices,
        'pickup_drop_choices':ServiceBooking.pickup_drop_choices,
    }
    return render(request, 'book_service_form.html',context)



# ______________History__________________________________________________________________
@login_required
def booking_history(request):
    user = request.user
    bookings = ServiceBooking.objects.filter(user=user).order_by('-service_date')

    today = date.today()
    
    for b in bookings:
        if b.service_date < today and not b.is_completed:
            b.status = "Completed"

            # ✅ Update vehicle service date
            vehicle = b.vehicle
            vehicle.last_service_date = b.service_date
            vehicle.save()

            # ✅ Mark booking as completed (IMPORTANT)
            b.is_completed = True
            b.save()

        elif b.service_date == today:
            b.status = "Today"
        else:
            b.status = "Upcoming"
    context = {
        'user':user,
        'bookings':bookings
    }
    return render(request, 'booking_history.html', context)

# ____________Edit Booking_______________________________________
@login_required
def edit_booking(request, booking_id):
    booking = get_object_or_404(ServiceBooking, id=booking_id, user=request.user)

    if request.method == "POST":
        # Update fields from POST
        service_type = request.POST.get("service_type")
        service_date = request.POST.get("service_date")
        timeslot = request.POST.get("timeslot")
        pickup_drop = request.POST.get("pickup_drop")
        pickup_drop_address = request.POST.get("pickup_drop_address")
        additional_note = request.POST.get("additional_note")

        # Validate service date
        try:
            service_date_obj = datetime.strptime(service_date, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect('edit_booking', booking_id=booking.id)

        if service_date_obj < date.today():
            messages.error(request, "Service date cannot be in the past.")
            return redirect('edit_booking', booking_id=booking.id)

        # Update booking
        booking.service_type = service_type
        booking.service_date = service_date_obj
        booking.timeslot = timeslot
        booking.pickup_drop = pickup_drop
        booking.pickup_drop_address = pickup_drop_address
        booking.additional_note = additional_note
        booking.save()

        messages.success(request, "Booking updated successfully!")
        return redirect('booking_history')
    
    context = {
        'booking':booking,
        'service_choices':ServiceBooking.service_choices,
        'timeslot_choices':ServiceBooking.timeslot_choices,
        'pickup_drop_choices':ServiceBooking.pickup_drop_choices,
    }
    return render(request, 'edit_booking.html', context)

# _________________Delete Booking________________________________
@login_required
def delete_booking(request, booking_id):
    booking = get_object_or_404(ServiceBooking, id=booking_id, user=request.user)
    booking.delete()
    messages.success(request, "Booking deleted sucessfully!")
    return redirect('booking_history')

# __________________Profile____________________________________
@login_required
def profile(request):
    user = request.user
    try:
        profile = user.userprofile
    except UserProfile.DoesNotExist:
        profile = None

    context = {
        'user':user,
        'profile':profile,
        'account_created':user.date_joined,
    }
    return render(request, 'profile.html', context)


# ______________________Edit Profile__________________________
@login_required
def edit_profile(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        mobile = request.POST.get("mobile")
        address = request.POST.get("address")
        email = request.POST.get("email")

        # Email Validation
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "Email already in use.")
            return redirect('edit_profile')

        # Mobile validation
        if not re.fullmatch(r'[6-9]\d{9}', mobile):
            messages.error(request, "Enter a valid 10-digit mobile number starting with 6-9.")
            return redirect('edit_profile')

        user.email = email
        user.save()

        profile.mobile_number = mobile
        profile.address = address
        profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('profile')

    context = {
        'user': user,
        'profile': profile
    }
    return render(request, 'edit_profile.html', context)