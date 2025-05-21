from django.shortcuts import render

def about_view(request):
    """About page view"""
    return render(request, 'core/about.html')

def terms_view(request):
    """Terms and conditions page view"""
    return render(request, 'core/terms.html')

def privacy_view(request):
    """Privacy policy view"""
    return render(request, 'core/privacy.html')

def faq_view(request):
    """FAQ view"""
    return render(request, 'core/faq.html')