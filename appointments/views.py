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
                Q(nameicontains=search_query) | 
                Q(descriptionicontains=search_query) |
                Q(servicesnameicontains=search_query) |
                Q(doctorsnameicontains=search_query) |
                Q(doctorsspecializationicontains=search_query)
            ).distinct()
        if location:
            # Search in city, state, and address
            authorities = authorities.filter(
                Q(cityicontains=location) | 
                Q(stateicontains=location) | 
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
        form = BookAppointmentForm(service_id, request.POST)
        if form.is_valid():
            # Create the appointment
            appointment = form.save(commit=False)
            appointment.user = request.user
            appointment.authority = authority
            appointment.service = service
            appointment.doctor = service.doctor
            # Get the selected time slot
            slot_id = form.cleaned_data.get('slot_id')
            time_slot = get_object_or_404(TimeSlot, id=slot_id)
            appointment.time_slot = time_slot
            # Set appointment time from the time slot
            appointment.appointment_time = time_slot.start_time
            appointment.save()
            # Create appointment slot
            appointment_date = form.cleaned_data.get('appointment_date')
            AppointmentSlot.objects.create(
                time_slot=time_slot,
                appointment=appointment,
                date=appointment_date
            )
            
            # Send email notifications
            send_appointment_notifications(request, appointment, appointment_date)
            
            messages.success(request, "Your appointment has been booked successfully! You will be notified once it's approved.")
            return redirect('my_appointments')
    else:
        form = BookAppointmentForm(service_id=service_id)
    context = {
        'form': form,
        'service': service,
        'authority': authority,
    }
    return render(request, 'appointments/book.html', context)

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
        
        Patient: {user.get_full_name()}
        Service: {service.name}
        Date: {appointment_date}
        Time: {appointment.appointment_time.strftime('%I:%M %p')}
        Doctor: {doctor.name if doctor else 'Not specified'}
        
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
    
    Patient: {user.get_full_name()} ({user.email})
    Authority: {authority.name}
    Service: {service.name}
    Date: {appointment_date}
    Time: {appointment.appointment_time.strftime('%I:%M %p')}
    Doctor: {doctor.name if doctor else 'Not specified'}
    
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
    upcoming_appointments = Appointment.objects.filter(
        user=request.user,
        appointment_date__gte=timezone.now().date()
    ).order_by('appointment_date', 'appointment_time')
    past_appointments = Appointment.objects.filter(
        user=request.user,
        appointment_date__lt=timezone.now().date()
    ).order_by('-appointment_date', '-appointment_time')
    context = {
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
    }
    return render(request, 'appointments/my_appointments.html', context)

@login_required
def appointment_detail_view(request, appointment_id):
    """View appointment details"""
    try:
        appointment = Appointment.objects.get(id=appointment_id, user=request.user)
    except Appointment.DoesNotExist:
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