from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import ContactForm
from .models import ContactMessage

def contact_view(request):
    """Contact form view"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Save the contact message
            contact_message = form.save(commit=False)
            # Associate with user if logged in
            if request.user.is_authenticated:
                contact_message.user = request.user
            contact_message.save()
            
            # Send email notification to admin
            subject = f"New Contact Message: {contact_message.subject}"
            message = (
                f"New message submitted via contact form:\n\n"
                f"Name: {contact_message.name}\n"
                f"Email: {contact_message.email}\n\n"
                f"Message:\n{contact_message.message}"
            )
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [settings.ADMIN_EMAIL]  # Use setting from settings.py
            
            try:
                send_mail(
                    subject,
                    message,
                    from_email,
                    recipient_list,
                    fail_silently=False,  # Keep False for debugging
                )
                messages.success(request, "Your message has been sent successfully! We'll get back to you soon.")
            except Exception as e:
                # Log the exception for debugging
                print(f"Email sending failed: {str(e)}")
                messages.warning(request, "Your message has been saved, but we encountered an issue sending the notification. Our team will still review your message.")
            
            return redirect('contact_success')
    else:
        # Pre-fill form with user info if logged in
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'name': request.user.get_full_name(),
                'email': request.user.email
            }
        form = ContactForm(initial=initial_data)
    
    context = {
        'form': form
    }
    return render(request, 'contact/contact.html', context)

def contact_success_view(request):
    return render(request, 'contact/contact_success.html')