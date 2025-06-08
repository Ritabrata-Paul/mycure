from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import User
from appointments.models import Appointment, Authority, Doctor, Service
from contact.models import ContactMessage
from .forms import UserForm, AdminCreateUserForm, AuthorityCreationForm, ContactMessageReplyForm

def is_admin(user):
    """Check if user is an admin"""
    return user.is_authenticated and user.user_type == 'ADMIN'

@login_required
@user_passes_test(is_admin)
def admin_dashboard_view(request):
    """Admin dashboard view"""
    # Count statistics
    users_count = User.objects.count()
    authorities_count = Authority.objects.count()
    pending_authorities = Authority.objects.filter(is_verified=False).count()
    appointments_count = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status='PENDING').count()
    new_messages = ContactMessage.objects.filter(status='NEW').count()
    
    # Recent appointments
    recent_appointments = Appointment.objects.all().order_by('-created_at')[:5]
    
    # Recent users
    recent_users = User.objects.all().order_by('-date_joined')[:5]
    
    # New contact messages
    new_contact_messages = ContactMessage.objects.filter(status='NEW').order_by('-created_at')[:5]
    
    context = {
        'users_count': users_count,
        'authorities_count': authorities_count,
        'pending_authorities': pending_authorities,
        'appointments_count': appointments_count,
        'pending_appointments': pending_appointments,
        'new_messages': new_messages,
        'recent_appointments': recent_appointments,
        'recent_users': recent_users,
        'new_contact_messages': new_contact_messages,
    }
    return render(request, 'adminpanel/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def manage_doctors_view(request, authority_id):
    """View for managing doctors of an authority"""
    authority = get_object_or_404(Authority, id=authority_id)
    doctors = Doctor.objects.filter(authority=authority)

    context = {
        'authority': authority,
        'doctors': doctors,
    }
    return render(request, 'adminpanel/manage_doctors.html', context)

@login_required
@user_passes_test(is_admin)
def add_user_view(request):
    """Add new user"""
    if request.method == 'POST':
        form = AdminCreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.email} has been created successfully!")
            return redirect('user_detail', user_id=user.id)
    else:
        form = AdminCreateUserForm()
    
    context = {
        'form': form,
    }
    return render(request, 'adminpanel/add_user.html', context)

@login_required
@user_passes_test(is_admin)
def manage_users_view(request):
    """View for managing users"""
    users = User.objects.all().order_by('-date_joined')
    
    # Filter users by type if requested
    user_type = request.GET.get('user_type')
    if user_type:
        users = users.filter(user_type=user_type)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            email__icontains=search_query
        ) | users.filter(
            first_name__icontains=search_query
        ) | users.filter(
            last_name__icontains=search_query
        )
    
    # Pagination
    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    context = {
        'users': users_page,
        'user_type': user_type,
        'search_query': search_query,
    }
    return render(request, 'adminpanel/manage_users.html', context)

@login_required
@user_passes_test(is_admin)
def user_detail_view(request, user_id):
    """View user details with comprehensive activity tracking"""
    user = get_object_or_404(User, id=user_id)
    
    # Get user's appointments if they are a customer
    appointments = None
    if user.user_type == 'CUSTOMER':
        appointments = Appointment.objects.filter(user=user).order_by('-created_at')[:10]  # Get more for activity log
    
    # Get authority details if user is an authority
    authority = None
    if user.user_type == 'AUTHORITY':
        try:
            authority = Authority.objects.get(user=user)
        except Authority.DoesNotExist:
            pass
    
    # Prepare activity data for the template
    activity_data = {
        'account_created': user.date_joined,
        'last_login': user.last_login,
        'appointments_count': appointments.count() if appointments else 0,
        'recent_appointments': appointments[:5] if appointments else None,
        'authority_status': authority.is_verified if authority else None,
        'authority_created': authority.created_at if authority else None,
    }
    
    context = {
        'user_detail': user,
        'appointments': appointments,
        'authority': authority,
        'activity_data': activity_data,
    }
    return render(request, 'adminpanel/user_detail.html', context)

@login_required
@user_passes_test(is_admin)
def edit_user_view(request, user_id):
    """Edit user"""
    user = get_object_or_404(User, id=user_id)
    
    # Prevent editing other admin users
    if user.user_type == 'ADMIN' and user != request.user:
        messages.error(request, "You cannot edit other admin users.")
        return redirect('user_detail', user_id=user.id)
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            # Additional validation for admin users
            if user.user_type == 'ADMIN' and form.cleaned_data['user_type'] != 'ADMIN':
                messages.error(request, "Admin users cannot be changed to other user types.")
                return redirect('edit_user', user_id=user.id)
            
            form.save()
            messages.success(request, f"User {user.email} has been updated successfully!")
            return redirect('user_detail', user_id=user.id)
    else:
        form = UserForm(instance=user)
    
    context = {
        'form': form,
        'user_detail': user,
    }
    return render(request, 'adminpanel/edit_user.html', context)


@login_required
@user_passes_test(is_admin)
def delete_user_view(request, user_id):
    """Delete user"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.delete()
        messages.success(request, f"User {user.email} has been deleted successfully!")
        return redirect('manage_users')
    
    context = {
        'user_detail': user,
    }
    return render(request, 'adminpanel/delete_user.html', context)

@login_required
@user_passes_test(is_admin)
def manage_authorities_view(request):
    """View for managing authorities"""
    authorities = Authority.objects.all().order_by('-created_at')
    
    # Filter authorities by type if requested
    authority_type = request.GET.get('authority_type')
    if authority_type:
        authorities = authorities.filter(authority_type=authority_type)
    
    # Filter by verification status if requested
    verification_status = request.GET.get('verification_status')
    if verification_status:
        if verification_status == 'verified':
            authorities = authorities.filter(is_verified=True)
        elif verification_status == 'unverified':
            authorities = authorities.filter(is_verified=False)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        authorities = authorities.filter(
            name__icontains=search_query
        ) | authorities.filter(
            city__icontains=search_query
        ) | authorities.filter(
            state__icontains=search_query
        )
    
    # Count verified and unverified authorities for charts
    verified_count = Authority.objects.filter(is_verified=True).count()
    unverified_count = Authority.objects.filter(is_verified=False).count()
    
    # Count by type for charts
    hospitals_count = Authority.objects.filter(authority_type='HOSPITAL').count()
    clinics_count = Authority.objects.filter(authority_type='CLINIC').count()
    diagnostic_count = Authority.objects.filter(authority_type='DIAGNOSTIC').count()
    
    # Pagination
    paginator = Paginator(authorities, 10)  # Show 10 authorities per page
    page_number = request.GET.get('page')
    authorities_page = paginator.get_page(page_number)
    
    context = {
        'authorities': authorities_page,
        'authority_type': authority_type,
        'verification_status': verification_status,
        'search_query': search_query,
        'verified_count': verified_count,
        'unverified_count': unverified_count,
        'hospitals_count': hospitals_count,
        'clinics_count': clinics_count,
        'diagnostic_count': diagnostic_count,
    }
    
    return render(request, 'adminpanel/manage_authorities.html', context)

@login_required
@user_passes_test(is_admin)
def add_authority_view(request):
    """Add new authority"""
    if request.method == 'POST':
        form = AuthorityCreationForm(request.POST, request.FILES)
        
        # Check the account type (existing or new user)
        account_type = request.POST.get('account_type')
        
        # Validate the form first
        if form.is_valid():
            # Don't save the form yet, as we might need to create a new user
            authority = form.save(commit=False)
            
            if account_type == 'existing':
                # Using existing user - Make sure one is selected
                user_id = request.POST.get('user')
                if not user_id:
                    messages.error(request, "Please select an existing user.")
                    context = {'form': form}
                    return render(request, 'adminpanel/add_authority.html', context)
                
                # Get the selected user and set it
                authority.user = User.objects.get(id=user_id)
                
            elif account_type == 'new':
                # Creating new user
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                email = request.POST.get('user_email')
                password = request.POST.get('password')
                
                # Basic validation
                if not (first_name and last_name and email and password):
                    messages.error(request, "All user fields are required.")
                    context = {'form': form}
                    return render(request, 'adminpanel/add_authority.html', context)
                
                # Check if email already exists
                if User.objects.filter(email=email).exists():
                    messages.error(request, f"User with email {email} already exists.")
                    context = {'form': form}
                    return render(request, 'adminpanel/add_authority.html', context)
                
                # Create new user with AUTHORITY type
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    user_type='AUTHORITY'
                )
                
                # Set the new user for the authority
                authority.user = user
            
            # Now save the authority with the user assigned
            authority.save()
            messages.success(request, f"Authority {authority.name} has been added successfully!")
            return redirect('manage_authorities')
        else:
            # If form is not valid, show errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = AuthorityCreationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'adminpanel/add_authority.html', context)

@login_required
@user_passes_test(is_admin)
def authority_detail_view(request, authority_id):
    """View authority details"""
    authority = get_object_or_404(Authority, id=authority_id)
    
    # Get authority's doctors
    doctors = Doctor.objects.filter(authority=authority)
    
    # Get authority's services
    services = Service.objects.filter(authority=authority)
    
    # Get authority's appointments
    appointments = Appointment.objects.filter(authority=authority).order_by('-appointment_date')
    
    context = {
        'authority': authority,
        'doctors': doctors,
        'services': services,
        'appointments': appointments,
    }
    return render(request, 'adminpanel/authority_detail.html', context)

@login_required
@user_passes_test(is_admin)
def edit_authority_view(request, authority_id):
    """Edit authority"""
    authority = get_object_or_404(Authority, id=authority_id)
    
    if request.method == 'POST':
        form = AuthorityCreationForm(request.POST, request.FILES, instance=authority)
        if form.is_valid():
            form.save()
            messages.success(request, f"Authority {authority.name} has been updated successfully!")
            return redirect('admin_authority_detail', authority_id=authority.id)
    else:
        form = AuthorityCreationForm(instance=authority)
    
    context = {
        'form': form,
        'authority': authority,
    }
    return render(request, 'adminpanel/edit_authority.html', context)

@login_required
@user_passes_test(is_admin)
def delete_authority_view(request, authority_id):
    """Delete authority"""
    authority = get_object_or_404(Authority, id=authority_id)
    
    if request.method == 'POST':
        authority.delete()
        messages.success(request, f"Authority {authority.name} has been deleted successfully!")
        return redirect('manage_authorities')
    
    context = {
        'authority': authority,
    }
    return render(request, 'adminpanel/delete_authority.html', context)

@login_required
@user_passes_test(is_admin)
def verify_authority_view(request, authority_id):
    """Verify authority"""
    authority = get_object_or_404(Authority, id=authority_id)
    
    authority.is_verified = not authority.is_verified
    authority.save()
    
    status = "verified" if authority.is_verified else "unverified"
    messages.success(request, f"Authority {authority.name} has been {status} successfully!")
    return redirect('admin_authority_detail', authority_id=authority.id)

@login_required
@user_passes_test(is_admin)
def all_appointments_view(request):
    """View all appointments"""
    appointments = Appointment.objects.all().order_by('-appointment_date')
    
    # Filter by status if requested
    status = request.GET.get('status')
    if status:
        appointments = appointments.filter(status=status)
    
    # Filter by authority if requested
    authority_id = request.GET.get('authority')
    if authority_id:
        appointments = appointments.filter(authority_id=authority_id)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        appointments = appointments.filter(
            user__email__icontains=search_query
        ) | appointments.filter(
            user__first_name__icontains=search_query
        ) | appointments.filter(
            user__last_name__icontains=search_query
        ) | appointments.filter(
            authority__name__icontains=search_query
        )
    
    # Get the filtered queryset for statistics
    filtered_appointments = appointments
    
    # Get appointment counts by status for statistics (filtered)
    pending_count = filtered_appointments.filter(status='PENDING').count()
    approved_count = filtered_appointments.filter(status='APPROVED').count()
    completed_count = filtered_appointments.filter(status='COMPLETED').count()
    cancelled_count = filtered_appointments.filter(status='CANCELLED').count()
    
    # Get monthly data for the last 6 months (filtered)
    from django.utils import timezone
    from datetime import datetime, timedelta
    from django.db.models import Count
    from django.db.models.functions import TruncMonth
    
    # Calculate date 6 months ago
    six_months_ago = timezone.now() - timedelta(days=180)
    
    # Get monthly appointment counts (filtered)
    monthly_data = (
        filtered_appointments
        .filter(created_at__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    # Create a list of the last 6 months with counts
    monthly_appointments = []
    current_date = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    for i in range(6):
        month_date = current_date - timedelta(days=30*i)
        month_count = 0
        
        # Find count for this month in the data
        for data in monthly_data:
            if (data['month'].year == month_date.year and 
                data['month'].month == month_date.month):
                month_count = data['count']
                break
        
        monthly_appointments.insert(0, {
            'month': month_date.strftime('%b'),
            'count': month_count
        })
    
    # Pagination
    paginator = Paginator(appointments, 15)  # Show 15 appointments per page
    page_number = request.GET.get('page')
    appointments_page = paginator.get_page(page_number)
    
    # Get all authorities for filter dropdown
    authorities = Authority.objects.all()
    
    context = {
        'appointments': appointments_page,
        'status': status,
        'authority_id': authority_id,
        'search_query': search_query,
        'authorities': authorities,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'monthly_appointments': monthly_appointments,
    }
    
    return render(request, 'adminpanel/all_appointments.html', context)


@login_required
@user_passes_test(is_admin)
def appointment_detail_view(request, appointment_id):
    """View appointment details"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    context = {
        'appointment': appointment,
    }
    return render(request, 'adminpanel/appointment_detail.html', context)


@login_required
@user_passes_test(is_admin)
def update_appointment_view(request, appointment_id):
    """Update appointment status"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            appointment.status = 'APPROVED'
            notes = request.POST.get('notes')
            if notes:
                appointment.admin_notes = notes
            messages.success(request, f"Appointment #{appointment.id} has been approved.")
        
        elif action == 'reject':
            appointment.status = 'REJECTED'
            rejection_reason = request.POST.get('rejection_reason')
            appointment.rejection_reason = rejection_reason
            messages.success(request, f"Appointment #{appointment.id} has been rejected.")
        
        elif action == 'complete':
            appointment.status = 'COMPLETED'
            notes = request.POST.get('notes')
            if notes:
                appointment.admin_notes = notes
            messages.success(request, f"Appointment #{appointment.id} has been marked as completed.")
        
        elif action == 'cancel':
            appointment.status = 'CANCELLED'
            cancellation_reason = request.POST.get('cancellation_reason')
            appointment.cancellation_reason = cancellation_reason
            messages.success(request, f"Appointment #{appointment.id} has been cancelled.")
        
        # Record who updated the appointment
        appointment.updated_by = request.user
        appointment.save()
        
        return redirect('admin_appointment_detail', appointment_id=appointment.id)
    
    return redirect('admin_appointment_detail', appointment_id=appointment.id)

@login_required
@user_passes_test(is_admin)
def contact_messages_view(request):
    """View contact messages"""
    messages_list = ContactMessage.objects.all().order_by('-created_at')
    
    # Filter by status if requested
    status = request.GET.get('status')
    if status:
        messages_list = messages_list.filter(status=status)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        messages_list = messages_list.filter(
            name__icontains=search_query
        ) | messages_list.filter(
            email__icontains=search_query
        ) | messages_list.filter(
            subject__icontains=search_query
        )
    
    # Pagination
    paginator = Paginator(messages_list, 15)  # Show 15 messages per page
    page_number = request.GET.get('page')
    messages_page = paginator.get_page(page_number)
    
    # Get counts for chart
    new_count = ContactMessage.objects.filter(status='NEW').count()
    read_count = ContactMessage.objects.filter(status='READ').count()
    replied_count = ContactMessage.objects.filter(status='REPLIED').count()
    
    context = {
        'messages_list': messages_page,
        'status': status,
        'search_query': search_query,
        'new_count': new_count,
        'read_count': read_count,
        'replied_count': replied_count
    }
    return render(request, 'adminpanel/contact_messages.html', context)

@login_required
@user_passes_test(is_admin)
def contact_message_detail_view(request, message_id):
    """View contact message details"""
    message = get_object_or_404(ContactMessage, id=message_id)
    
    # Mark message as read if it's new
    if message.status == 'NEW':
        message.status = 'READ'
        message.save()
    
    context = {
        'message': message,
    }
    return render(request, 'adminpanel/contact_message_detail.html', context)

@login_required
@user_passes_test(is_admin)
def reply_contact_message_view(request, message_id):
    """Reply to contact message"""
    message = get_object_or_404(ContactMessage, id=message_id)
    
    if request.method == 'POST':
        form = ContactMessageReplyForm(request.POST)
        if form.is_valid():
            reply = form.cleaned_data['reply']
            message.reply = reply
            message.replied_by = request.user
            message.status = 'REPLIED'
            message.save()
            
            # Send email with the reply to the user
            subject = f"Re: {message.subject}"
            email_message = (
                f"Dear {message.name},\n\n"
                f"{reply}\n\n"
                f"Regards,\n"
                f"{request.user.get_full_name() or 'MyCure Support Team'}"
            )
            
            try:
                send_mail(
                    subject,
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [message.email],
                    fail_silently=False,
                )
                messages.success(request, "Your reply has been sent successfully!")
            except Exception as e:
                # Log the exception for debugging
                print(f"Reply email sending failed: {str(e)}")
                messages.warning(request, "Reply saved but there was an issue sending the email to the user.")
            
            return redirect('contact_message_detail', message_id=message.id)
    else:
        # Pre-fill the form if there's an existing reply
        initial_data = {}
        if message.reply:
            initial_data = {'reply': message.reply}
        form = ContactMessageReplyForm(initial=initial_data)
    
    context = {
        'form': form,
        'message': message,
    }
    return render(request, 'adminpanel/reply_contact_message.html', context)