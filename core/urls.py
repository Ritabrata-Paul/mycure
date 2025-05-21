from django.urls import path
from .views import about_view, terms_view, privacy_view, faq_view

app_name = 'core'

urlpatterns = [
    path('about/', about_view, name='about'),
    path('terms/', terms_view, name='terms'),
    path('privacy/', privacy_view, name='privacy'),
    path('faq/', faq_view, name='faq'),
]