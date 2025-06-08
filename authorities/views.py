from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count
from django.http import JsonResponse
from django.utils.formats import date_format
from django.db import models

from .models import Authority, Service, Doctor, TimeSlot
from appointments.models import Appointment
from .forms import (
    AuthorityProfileForm, ServiceForm, DoctorForm, 
    TimeSlotForm, AppointmentResponseForm
)

def authority_required(view_func):
    """Decorator to check if the user is an authority"""
    def wrapper(request, *args, **kwargs):
        if request.user.user_type != 'AUTHORITY':
            messages.error(request, "You don't have permission to access this page.")
            return redirect('home')
        try:
            request.user.authority_profile
        except Authority.DoesNotExist:
            messages.error(request, "Your authority profile is not set up. Please contact admin.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@authority_required
def dashboard_view(request):
    """Authority dashboard view"""
    authority = request.user.authority_profile
    
    # Get statistics
    pending_appointments = Appointment.objects.filter(
        authority=authority,
        status='PENDING'
    ).count()
    
    today_appointments = Appointment.objects.filter(
        authority=authority,
        appointment_date=timezone.now().date()
    ).count()
    
    total_appointments = Appointment.objects.filter(
        authority=authority
    ).count()
    
    total_services = Service.objects.filter(
        authority=authority
    ).count()
    
    recent_appointments = Appointment.objects.filter(
        authority=authority
    ).order_by('-created_at')[:5]
    
    context = {
        'authority': authority,
        'pending_appointments': pending_appointments,
        'today_appointments': today_appointments,
        'total_appointments': total_appointments,
        'total_services': total_services,
        'recent_appointments': recent_appointments,
    }
    return render(request, 'authorities/dashboard.html', context)

@login_required
@authority_required
def appointment_detail_view(request, appointment_id):
    """View appointment details"""
    authority = request.user.authority_profile
    appointment = get_object_or_404(Appointment, id=appointment_id, authority=authority)
    context = {
        'authority': authority,
        'appointment': appointment,
    }
    return render(request, 'authorities/appointment_detail.html', context)

@login_required
@authority_required
def authority_appointments_view(request):
    """View authority's appointments with filtering"""
    authority = request.user.authority_profile
    
    # Get all appointments for this authority
    all_appointments = Appointment.objects.filter(authority=authority)
    
    # Apply filters
    service_filter = request.GET.get('service')
    doctor_filter = request.GET.get('doctor')
    date_filter = request.GET.get('date')
    status_filter = request.GET.get('status')
    
    # Start with all appointments
    filtered_appointments = all_appointments
    
    # Apply service filter
    if service_filter:
        filtered_appointments = filtered_appointments.filter(service_id=service_filter)
    
    # Apply doctor filter
    if doctor_filter:
        filtered_appointments = filtered_appointments.filter(doctor_id=doctor_filter)
    
    # Apply date filter
    if date_filter:
        filtered_appointments = filtered_appointments.filter(appointment_date=date_filter)
    
    # Apply status filter
    if status_filter:
        filtered_appointments = filtered_appointments.filter(status=status_filter)
    
    # Separate appointments by status and date
    pending_appointments = filtered_appointments.filter(
        status='PENDING'
    ).order_by('appointment_date', 'appointment_time')
    
    # Upcoming appointments: approved and date >= today
    upcoming_appointments = filtered_appointments.filter(
        status='APPROVED',
        appointment_date__gte=timezone.now().date()
    ).order_by('appointment_date', 'appointment_time')
    
    # Past appointments: any status and date < today, OR completed/rejected/cancelled regardless of date
    past_appointments = filtered_appointments.filter(
        models.Q(appointment_date__lt=timezone.now().date()) |
        models.Q(status__in=['COMPLETED', 'REJECTED', 'CANCELLED'])
    ).order_by('-appointment_date', '-appointment_time')
    
    # Get total counts for stats (unfiltered)
    total_pending = all_appointments.filter(status='PENDING').count()
    total_upcoming = all_appointments.filter(
        status='APPROVED',
        appointment_date__gte=timezone.now().date()
    ).count()
    total_past = all_appointments.filter(
        models.Q(appointment_date__lt=timezone.now().date()) |
        models.Q(status__in=['COMPLETED', 'REJECTED', 'CANCELLED'])
    ).count()
    
    # Get all services and doctors for filter dropdowns
    services = Service.objects.filter(authority=authority, is_active=True)
    doctors = Doctor.objects.filter(authority=authority, is_active=True)
    
    # Status choices for filter
    status_choices = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]
    
    context = {
        'authority': authority,
        'pending_appointments': pending_appointments,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'total_pending': total_pending,
        'total_upcoming': total_upcoming,
        'total_past': total_past,
        'total_appointments': total_pending + total_upcoming + total_past,
        'services': services,
        'doctors': doctors,
        'status_choices': status_choices,
        'current_filters': {
            'service': service_filter,
            'doctor': doctor_filter,
            'date': date_filter,
            'status': status_filter,
        }
    }
    return render(request, 'authorities/appointments.html', context)

@login_required
@authority_required
def approve_appointment_view(request, appointment_id):
    """Approve an appointment"""
    authority = request.user.authority_profile
    appointment = get_object_or_404(Appointment, id=appointment_id, authority=authority)
    
    if appointment.status != 'PENDING':
        messages.error(request, "This appointment cannot be approved.")
        return redirect('authority_appointments')
    
    appointment.status = 'APPROVED'
    appointment.save()
    messages.success(request, "Appointment has been approved successfully.")
    return redirect('authority_appointments')

@login_required
@authority_required
def reject_appointment_view(request, appointment_id):
    """Reject an appointment"""
    authority = request.user.authority_profile
    appointment = get_object_or_404(Appointment, id=appointment_id, authority=authority)
    
    # Check if appointment can be rejected
    if appointment.status != 'PENDING':
        messages.error(request, "This appointment cannot be rejected. Only pending appointments can be rejected.")
        return redirect('authority_appointments')
    
    if request.method == 'POST':
        # Get the rejection reason directly from POST data
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        
        # Validate that rejection reason is provided
        if not rejection_reason:
            messages.error(request, "Please provide a reason for rejection.")
            context = {
                'appointment': appointment,
                'authority': authority,
                'form_error': 'Rejection reason is required.'
            }
            return render(request, 'authorities/reject_appointment.html', context)
        
        try:
            # Update appointment status
            appointment.status = 'REJECTED'
            appointment.rejection_reason = rejection_reason
            appointment.save()
            
            # Free up the appointment slot if it exists
            if hasattr(appointment, 'booked_slot') and appointment.booked_slot:
                appointment.booked_slot.is_available = True
                appointment.booked_slot.save()
            
            messages.success(request, f"Appointment #{appointment.id} has been rejected successfully.")
            return redirect('authority_appointments')
            
        except Exception as e:
            messages.error(request, f"An error occurred while rejecting the appointment: {str(e)}")
            
    # For GET request, display the form
    form = AppointmentResponseForm()
    context = {
        'form': form,
        'appointment': appointment,
        'authority': authority,
    }
    return render(request, 'authorities/reject_appointment.html', context)

@login_required
@authority_required
def manage_services_view(request):
    """Manage authority services"""
    authority = request.user.authority_profile
    services = Service.objects.filter(authority=authority)
    
    # Apply filters
    doctor_filter = request.GET.get('doctor')
    status_filter = request.GET.get('status')
    price_filter = request.GET.get('price')
    sort_by = request.GET.get('sort', 'name')
    
    # Filter by doctor
    if doctor_filter:
        services = services.filter(doctor_id=doctor_filter)
    
    # Filter by status
    if status_filter == 'active':
        services = services.filter(is_active=True)
    elif status_filter == 'inactive':
        services = services.filter(is_active=False)
    
    # Filter by price range
    if price_filter:
        if price_filter == '0-100':
            services = services.filter(price__lte=100)
        elif price_filter == '101-500':
            services = services.filter(price__gte=101, price__lte=500)
        elif price_filter == '501-1000':
            services = services.filter(price__gte=501, price__lte=1000)
        elif price_filter == '1001+':
            services = services.filter(price__gte=1001)
    
    # Apply sorting
    if sort_by == 'name':
        services = services.order_by('name')
    elif sort_by == 'price':
        services = services.order_by('price')
    elif sort_by == '-price':
        services = services.order_by('-price')
    elif sort_by == 'duration':
        services = services.order_by('duration_minutes')
    elif sort_by == '-created_at':
        services = services.order_by('-created_at')
    else:
        services = services.order_by('name')
    
    # Calculate statistics
    all_services = Service.objects.filter(authority=authority)
    active_count = all_services.filter(is_active=True).count()
    inactive_count = all_services.filter(is_active=False).count()
    
    context = {
        'authority': authority,
        'services': services,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'current_filters': {
            'doctor': doctor_filter,
            'status': status_filter,
            'price': price_filter,
            'sort': sort_by,
        }
    }
    return render(request, 'authorities/services.html', context)

@login_required
@authority_required
def add_service_view(request):
    """Add a new service"""
    authority = request.user.authority_profile
    
    if request.method == 'POST':
        form = ServiceForm(authority, request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.authority = authority
            service.save()
            messages.success(request, "Service has been added successfully.")
            return redirect('manage_services')
    else:
        form = ServiceForm(authority=authority)
    
    context = {
        'form': form,
        'authority': authority,
    }
    return render(request, 'authorities/add_service.html', context)

@login_required
@authority_required
def edit_service_view(request, service_id):
    """Edit a service"""
    authority = request.user.authority_profile
    service = get_object_or_404(Service, id=service_id, authority=authority)
    
    if request.method == 'POST':
        form = ServiceForm(authority, request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Service has been updated successfully.")
            return redirect('manage_services')
    else:
        form = ServiceForm(authority=authority, instance=service)
    
    context = {
        'form': form,
        'service': service,
        'authority': authority,
    }
    return render(request, 'authorities/edit_service.html', context)

@login_required
@authority_required
def delete_service_view(request, service_id):
    """Delete a service"""
    authority = request.user.authority_profile
    service = get_object_or_404(Service, id=service_id, authority=authority)
    
    if request.method == 'POST':
        service.delete()
        messages.success(request, "Service has been deleted successfully.")
        return redirect('manage_services')
    
    context = {
        'service': service,
        'authority': authority,
    }
    return render(request, 'authorities/delete_service.html', context)

@login_required
@authority_required
def manage_doctors_view(request):
    """Manage authority doctors"""
    authority = request.user.authority_profile
    doctors = Doctor.objects.filter(authority=authority)
    
    context = {
        'authority': authority,
        'doctors': doctors,
    }
    return render(request, 'authorities/doctors.html', context)

@login_required
@authority_required
def add_doctor_view(request):
    """Add a new doctor"""
    authority = request.user.authority_profile
    
    if request.method == 'POST':
        form = DoctorForm(request.POST, request.FILES)
        if form.is_valid():
            doctor = form.save(commit=False)
            doctor.authority = authority
            doctor.save()
            messages.success(request, "Doctor has been added successfully.")
            return redirect('manage_doctors')
    else:
        form = DoctorForm()
    
    context = {
        'form': form,
        'authority': authority,
    }
    return render(request, 'authorities/add_doctor.html', context)

@login_required
@authority_required
def edit_doctor_view(request, doctor_id):
    """Edit a doctor"""
    authority = request.user.authority_profile
    doctor = get_object_or_404(Doctor, id=doctor_id, authority=authority)
    
    if request.method == 'POST':
        form = DoctorForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, "Doctor has been updated successfully.")
            return redirect('manage_doctors')
    else:
        form = DoctorForm(instance=doctor)
    
    context = {
        'form': form,
        'doctor': doctor,
        'authority': authority,
    }
    return render(request, 'authorities/edit_doctor.html', context)

@login_required
@authority_required
def delete_doctor_view(request, doctor_id):
    """Delete a doctor"""
    authority = request.user.authority_profile
    doctor = get_object_or_404(Doctor, id=doctor_id, authority=authority)
    
    if request.method == 'POST':
        doctor.delete()
        messages.success(request, "Doctor has been deleted successfully.")
        return redirect('manage_doctors')
    
    context = {
        'doctor': doctor,
        'authority': authority,
    }
    return render(request, 'authorities/delete_doctor.html', context)

@login_required
@authority_required
def change_doctor_status(request, doctor_id):
    """Toggle doctor's status between active and inactive."""
    doctor = get_object_or_404(Doctor, id=doctor_id)

    # Ensure the doctor belongs to the authority's profile
    if request.user.authority_profile != doctor.authority:
        messages.error(request, "You don't have permission to modify this doctor.")
        return redirect('manage_doctors')

    # Toggle the doctor's status
    doctor.is_active = not doctor.is_active
    doctor.save()

    # Show success message
    status = 'activated' if doctor.is_active else 'deactivated'
    messages.success(request, f"Doctor has been {status} successfully.")

    return redirect('manage_doctors')

@login_required
@authority_required
def manage_slots_view(request):
    """Manage authority time slots"""
    authority = request.user.authority_profile
    # Show all slots (both active and inactive) that are not booked
    slots = TimeSlot.objects.filter(
        authority=authority,
        is_booked=False
    ).prefetch_related('services', 'doctors').order_by('weekday', 'start_time')
    
    context = {
        'authority': authority,
        'slots': slots,
    }
    return render(request, 'authorities/manage_slots.html', context)

@login_required
@authority_required
def change_slot_status(request, slot_id):
    """Toggle slot's status between active and inactive."""
    authority = request.user.authority_profile
    slot = get_object_or_404(TimeSlot, id=slot_id, authority=authority)
    
    # Don't allow status change for booked slots
    if slot.is_booked:
        messages.error(request, "Cannot change status of a booked time slot.")
        return redirect('manage_slots')
    
    # Toggle the slot's status
    slot.is_active = not slot.is_active
    slot.save()
    
    # Show success message
    status = 'activated' if slot.is_active else 'deactivated'
    messages.success(request, f"Time slot has been {status} successfully.")
    return redirect('manage_slots')



@login_required
@authority_required
def add_slot_view(request):
    """Add a new time slot"""
    authority = request.user.authority_profile
    if request.method == 'POST':
        form = TimeSlotForm(authority, request.POST)
        form.authority = authority  # Pass authority to form for validation
        if form.is_valid():
            slot = form.save(commit=False)
            slot.authority = authority
            slot.save()
            # Save many-to-many relationships
            form.save_m2m()
            messages.success(request, "Time slot has been added successfully.")
            return redirect('manage_slots')
    else:
        form = TimeSlotForm(authority=authority)
    
    context = {
        'form': form,
        'authority': authority,
    }
    return render(request, 'authorities/add_slot.html', context)

@login_required
@authority_required
def edit_slot_view(request, slot_id):
    """Edit a time slot"""
    authority = request.user.authority_profile
    slot = get_object_or_404(TimeSlot, id=slot_id, authority=authority)
    
    # Don't allow editing of booked slots
    if slot.is_booked:
        messages.error(request, "Cannot edit a time slot that has been booked.")
        return redirect('manage_slots')
    
    if request.method == 'POST':
        form = TimeSlotForm(authority, request.POST, instance=slot)
        form.authority = authority  # Pass authority to form for validation
        if form.is_valid():
            form.save()
            messages.success(request, "Time slot has been updated successfully.")
            return redirect('manage_slots')
    else:
        form = TimeSlotForm(authority=authority, instance=slot)
    
    context = {
        'form': form,
        'slot': slot,
        'authority': authority,
    }
    return render(request, 'authorities/edit_slot.html', context)

@login_required
@authority_required
def delete_slot_view(request, slot_id):
    """Delete a time slot"""
    authority = request.user.authority_profile
    slot = get_object_or_404(TimeSlot, id=slot_id, authority=authority)
    
    # Don't allow deletion of booked slots
    if slot.is_booked:
        messages.error(request, "Cannot delete a time slot that has been booked.")
        return redirect('manage_slots')
    
    if request.method == 'POST':
        slot.delete()
        messages.success(request, "Time slot has been deleted successfully.")
        return redirect('manage_slots')
    
    context = {
        'slot': slot,
        'authority': authority,
    }
    return render(request, 'authorities/delete_slot.html', context)

@login_required
@authority_required
def authority_profile_view(request):
    """View authority profile"""
    authority = request.user.authority_profile
    
    context = {
        'authority': authority,
    }
    return render(request, 'authorities/profile.html', context)

@login_required
@authority_required
def edit_authority_profile_view(request):
    """Edit authority profile"""
    authority = request.user.authority_profile
    
    if request.method == 'POST':
        form = AuthorityProfileForm(request.POST, request.FILES, instance=authority)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile has been updated successfully.")
            return redirect('authority_profile')
    else:
        form = AuthorityProfileForm(instance=authority)
    
    context = {
        'form': form,
        'authority': authority,
    }
    return render(request, 'authorities/edit_profile.html', context)


@login_required
@authority_required
def update_appointment_status_view(request, appointment_id):
    """Update the status of an appointment (Complete or Cancel)"""
    authority = request.user.authority_profile
    appointment = get_object_or_404(Appointment, id=appointment_id, authority=authority)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'complete':
            if appointment.status != 'APPROVED':
                messages.error(request, "Only approved appointments can be marked as completed.")
                return redirect('appointment_detail', appointment_id=appointment_id)
            
            appointment.status = 'COMPLETED'
            # Save any completion notes if provided
            notes = request.POST.get('notes')
            if notes:
                # You may want to add a completion_notes field to your Appointment model
                # For now, just storing in the existing notes field
                appointment.notes = f"{appointment.notes}\n\nCompletion Notes: {notes}" if appointment.notes else f"Completion Notes: {notes}"
            
            appointment.save()
            messages.success(request, "Appointment has been marked as completed.")
            
        elif action == 'cancel':
            if appointment.status != 'APPROVED':
                messages.error(request, "Only approved appointments can be cancelled.")
                return redirect('appointment_detail', appointment_id=appointment_id)
            
            cancellation_reason = request.POST.get('cancellation_reason')
            if not cancellation_reason:
                messages.error(request, "Please provide a reason for cancellation.")
                return redirect('appointment_detail', appointment_id=appointment_id)
            
            appointment.status = 'CANCELLED'
            appointment.cancellation_reason = cancellation_reason
            appointment.save()
            
            # Free up the appointment slot if applicable
            try:
                appointment_slot = appointment.booked_slot
                appointment_slot.is_available = True
                appointment_slot.save()
            except:
                pass
                
            messages.success(request, "Appointment has been cancelled.")
            
        else:
            messages.error(request, "Invalid action specified.")
    
    return redirect('appointment_detail', appointment_id=appointment_id)


@login_required
@authority_required
def get_appointments_json(request):
    """API endpoint to get all appointments for the calendar"""
    authority = request.user.authority_profile
    
    # Get all appointments for this authority
    appointments = Appointment.objects.filter(authority=authority)
    
    # Format the appointments for FullCalendar
    events = []
    for appointment in appointments:
        # Determine color based on status
        status_colors = {
            'PENDING': '#ffc107',    # warning
            'APPROVED': '#28a745',   # success
            'REJECTED': '#dc3545',   # danger
            'CANCELLED': '#6c757d',  # secondary
            'COMPLETED': '#17a2b8',  # info
        }
        
        color = status_colors.get(appointment.status, '#007bff')  # Default to primary
        
        # Format the date and time for display
        formatted_date = date_format(appointment.appointment_date, format="F j, Y", use_l10n=True)
        formatted_time = date_format(appointment.appointment_time, format="g:i A", use_l10n=True)
        
        # Create an event object for this appointment
        event = {
            'id': appointment.id,
            'title': f"{appointment.service.name} - {appointment.user.get_full_name()}",
            'start': f"{appointment.appointment_date.isoformat()}T{appointment.appointment_time.isoformat()}",
            'color': color,
            'extendedProps': {
                'patient': appointment.user.get_full_name(),
                'service': appointment.service.name,
                'status': appointment.status,
                'formattedDate': formatted_date,
                'time': formatted_time,
            }
        }
        
        events.append(event)
    
    return JsonResponse(events, safe=False)