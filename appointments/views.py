from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Appointment, AppointmentSlot
from .forms import SearchForm, BookAppointmentForm
from authorities.models import Authority, Service, TimeSlot, Doctor
from django.http import JsonResponse
from django.views.decorators.http import require_GET
import json

def search_view(request):
    """Search for authorities, services, and doctors"""
    form = SearchForm(request.GET)
    authorities = Authority.objects.filter(is_verified=True)
    
    if form.is_valid():
        search_query = form.cleaned_data.get('search_query')
        location = form.cleaned_data.get('location')
        authority_type = form.cleaned_data.get('authority_type')
        
        if search_query:
            # Search in authority name, description, services, and doctors
            authorities = authorities.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(services__name__icontains=search_query) |
                Q(doctors__name__icontains=search_query) |
                Q(doctors__specialization__icontains=search_query)
            ).distinct()
        
        if location:
            # Search in city, state, and address
            authorities = authorities.filter(
                Q(city__icontains=location) | 
                Q(state__icontains=location) | 
                Q(address__icontains=location)
            )
        
        if authority_type:
            authorities = authorities.filter(authority_type=authority_type)
    
    context = {
        'form': form,
        'authorities': authorities,
    }
    return render(request, 'appointments/search.html', context)

def authority_detail_view(request, authority_id):
    """View authority details"""
    authority = get_object_or_404(Authority, id=authority_id, is_verified=True)
    services = Service.objects.filter(authority=authority, is_active=True)
    doctors = Doctor.objects.filter(authority=authority)
    
    context = {
        'authority': authority,
        'services': services,
        'doctors': doctors,
    }
    return render(request, 'appointments/authority_detail.html', context)

def service_detail_view(request, service_id):
    """View service details"""
    service = get_object_or_404(Service, id=service_id, is_active=True)
    authority = service.authority
    doctor = service.doctor
    time_slots = TimeSlot.objects.filter(service=service, is_active=True)
    
    context = {
        'service': service,
        'authority': authority,
        'doctor': doctor,
        'time_slots': time_slots,
    }
    return render(request, 'appointments/service_detail.html', context)

@login_required
def book_appointment_view(request, service_id):
    """Book an appointment for a service"""
    service = get_object_or_404(Service, id=service_id, is_active=True)
    authority = service.authority
    
    if request.method == 'POST':
        form = BookAppointmentForm(service_id, request.user, request.POST)
        if form.is_valid():
            # Create the appointment
            appointment = form.save(commit=False)
            appointment.user = request.user
            appointment.authority = authority
            appointment.service = service
            appointment.doctor = service.doctor
            
            # Add patient information to appointment
            appointment.patient_name = form.cleaned_data.get('patient_name')
            appointment.patient_email = form.cleaned_data.get('patient_email')
            appointment.patient_phone = form.cleaned_data.get('patient_phone')
            appointment.patient_gender = form.cleaned_data.get('patient_gender')
            appointment.patient_age = form.cleaned_data.get('patient_age')
            
            # Get the selected time slot
            slot_id = form.cleaned_data.get('slot_id')
            time_slot = get_object_or_404(TimeSlot, id=slot_id)
            appointment.time_slot = time_slot
            
            # Set appointment time from the time slot
            appointment.appointment_time = time_slot.start_time
            
            # Set appointment date
            appointment.appointment_date = form.cleaned_data.get('appointment_date')
            
            # Save the appointment
            appointment.save()
            
            # Create appointment slot
            AppointmentSlot.objects.create(
                time_slot=time_slot,
                appointment=appointment,
                date=appointment.appointment_date
            )
            
            # Send email notifications
            send_appointment_notifications(request, appointment, appointment.appointment_date)
            
            messages.success(request, "Your appointment has been booked successfully! You will be notified once it's approved.")
            return redirect('my_appointments')
        else:
            # Add form errors to messages for debugging
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = BookAppointmentForm(service_id=service_id, user=request.user)
    
    context = {
        'form': form,
        'service': service,
        'authority': authority,
    }
    return render(request, 'appointments/book.html', context)

@require_GET
def get_available_slots(request):
    """AJAX view to get available time slots for a specific date and service"""
    service_id = request.GET.get('service_id')
    date_str = request.GET.get('date')
    
    if not service_id or not date_str:
        return JsonResponse({'error': 'Service ID and date are required'}, status=400)
    
    try:
        # Parse the date
        from datetime import datetime
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        selected_weekday = selected_date.weekday()  # 0=Monday, 6=Sunday
        
        # Get the service
        service = Service.objects.get(id=service_id, is_active=True)
        
        # Get time slots that match the selected weekday and are available for this service
        time_slots = TimeSlot.objects.filter(
            services__in=[service],
            weekday=selected_weekday,
            is_active=True,
            authority=service.authority
        ).distinct()
        
        # Check for existing appointments on this date to avoid double booking
        from .models import AppointmentSlot
        booked_slots = AppointmentSlot.objects.filter(
            date=selected_date,
            time_slot__in=time_slots
        ).values_list('time_slot_id', flat=True)
        
        # Filter out booked slots
        available_slots = time_slots.exclude(id__in=booked_slots)
        
        # Format the response
        weekday_names = {
            0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
            4: 'Friday', 5: 'Saturday', 6: 'Sunday'
        }
        selected_day_name = weekday_names[selected_weekday]
        
        slot_data = []
        for slot in available_slots:
            slot_data.append({
                'id': slot.id,
                'display': f"{slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}",
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M')
            })
        
        return JsonResponse({
            'slots': slot_data,
            'selected_day': selected_day_name,
            'total_slots': len(slot_data)
        })
        
    except Service.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def send_appointment_notifications(request, appointment, appointment_date):
    """Send email notifications to authority and admin"""
    user = request.user
    authority = appointment.authority
    service = appointment.service
    doctor = appointment.doctor
    
    # Email subject
    subject = f"New Appointment Booking - {service.name}"
    
    # Authority email notification
    if authority.email:
        authority_message = f"""
        Dear {authority.name},
        
        A new appointment has been booked at your facility:
        
        Patient Details:
        - Name: {appointment.patient_name}
        - Email: {appointment.patient_email}
        - Phone: {appointment.patient_phone}
        - Gender: {appointment.get_gender_display_full()}
        - Age: {appointment.patient_age} years
        
        Appointment Details:
        - Service: {service.name}
        - Date: {appointment_date}
        - Time: {appointment.appointment_time.strftime('%I:%M %p')}
        - Doctor: {doctor.name if doctor else 'Not specified'}
        
        Patient Notes: {appointment.notes if appointment.notes else 'None'}
        
        Please login to your dashboard to approve or reject this appointment.
        
        Thank you,
        MyCure Team
        """
        
        send_mail(
            subject,
            authority_message,
            settings.DEFAULT_FROM_EMAIL,
            [authority.email],
            fail_silently=False,
        )
    
    # Admin email notification
    admin_message = f"""
    New Appointment Alert!
    
    A new appointment has been booked:
    
    Patient Details:
    - Name: {appointment.patient_name}
    - Email: {appointment.patient_email}
    - Phone: {appointment.patient_phone}
    - Gender: {appointment.get_gender_display_full()}
    - Age: {appointment.patient_age} years
    
    Booking User: {user.get_full_name()} ({user.email})
    
    Appointment Details:
    - Authority: {authority.name}
    - Service: {service.name}
    - Date: {appointment_date}
    - Time: {appointment.appointment_time.strftime('%I:%M %p')}
    - Doctor: {doctor.name if doctor else 'Not specified'}
    
    Patient Notes: {appointment.notes if appointment.notes else 'None'}
    
    This is an automated notification from MyCure.
    """
    
    send_mail(
        subject,
        admin_message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.ADMIN_EMAIL],
        fail_silently=False,
    )

@login_required
def my_appointments_view(request):
    """View user's appointments"""
    # Debug: Print user info
    print(f"User: {request.user}, User ID: {request.user.id}, User Type: {request.user.user_type}")
    
    upcoming_appointments = Appointment.objects.filter(
        user=request.user,
        appointment_date__gte=timezone.now().date()
    ).order_by('appointment_date', 'appointment_time')
    
    past_appointments = Appointment.objects.filter(
        user=request.user,
        appointment_date__lt=timezone.now().date()
    ).order_by('-appointment_date', '-appointment_time')
    
    # Debug: Print appointment counts
    print(f"Upcoming appointments: {upcoming_appointments.count()}")
    print(f"Past appointments: {past_appointments.count()}")
    
    context = {
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
    }
    return render(request, 'appointments/my_appointments.html', context)

@login_required
def appointment_detail_view(request, appointment_id):
    """View appointment details"""
    # Debug: Print request info
    print(f"Appointment ID: {appointment_id}, User: {request.user}, User ID: {request.user.id}")
    
    try:
        appointment = Appointment.objects.get(id=appointment_id, user=request.user)
        print(f"Appointment found: {appointment}")
    except Appointment.DoesNotExist:
        print(f"Appointment not found for user {request.user}")
        messages.error(request, "You don't have permission to access this appointment.")
        return redirect('my_appointments')
    
    context = {
        'appointment': appointment,
    }
    return render(request, 'appointments/appointment_detail.html', context)

@login_required
def cancel_appointment_view(request, appointment_id):
    """Cancel an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    
    if not appointment.can_cancel():
        messages.error(request, "This appointment cannot be cancelled.")
        return redirect('appointment_detail', appointment_id=appointment_id)
    
    if request.method == 'POST':
        appointment.status = 'CANCELLED'
        appointment.save()
        
        # Free up the appointment slot
        try:
            appointment_slot = appointment.booked_slot
            appointment_slot.is_available = True
            appointment_slot.save()
        except AppointmentSlot.DoesNotExist:
            pass
        
        messages.success(request, "Your appointment has been cancelled successfully.")
        return redirect('my_appointments')
    
    context = {
        'appointment': appointment,
    }
    return render(request, 'appointments/cancel_appointment.html', context)

def homepage_view(request):
    """Homepage view with hospitals, clinics, doctors, diagnostics"""
    hospitals = Authority.objects.filter(authority_type='HOSPITAL', is_verified=True)
    clinics = Authority.objects.filter(authority_type='CLINIC', is_verified=True)
    diagnostic_centers = Authority.objects.filter(authority_type='DIAGNOSTIC', is_verified=True)
    doctors = Doctor.objects.filter(is_active=True)
    
    context = {
        'hospitals': hospitals,
        'clinics': clinics,
        'diagnostic_centers': diagnostic_centers,
        'doctors': doctors,
        'authorities_count': Authority.objects.count(),
        'doctors_count': Doctor.objects.count(),
        'users_count': 10000,  # replace with dynamic count if needed
        'appointments_count': 25000,  # replace with dynamic count if needed
        'blog_posts': [],  # or remove if no blog integration
    }
    return render(request, 'homepage.html', context)