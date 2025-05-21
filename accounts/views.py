from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from .forms import LoginForm, RegisterForm, ProfileForm, CustomPasswordChangeForm
from .models import User
from appointments.models import Appointment  # Add this import


def login_view(request):
    """Handle user login"""
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('profile')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def register_view(request):
    """Handle user registration"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registration successful. Please login.")
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile_view(request):
    """Display user profile"""
    # Get recent appointments if user is a customer
    recent_appointments = None
    if request.user.user_type == 'CUSTOMER':
        recent_appointments = Appointment.objects.filter(
            user=request.user
        ).order_by('-appointment_date', '-appointment_time')[:3]
    
    context = {
        'recent_appointments': recent_appointments
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile_view(request):
    """Handle profile update"""
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            # Make sure we save the form
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        # Make sure we properly initialize the form with all user data
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})

@login_required
def change_password_view(request):
    """Handle password change"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'accounts/password_change.html', {'form': form})


def logout_view(request):
    """Handle user logout with success message"""
    if request.method == 'POST':
        logout(request)
        messages.success(request, "You have been successfully logged out.")
        return redirect('home')
    return render(request, 'accounts/logout.html')