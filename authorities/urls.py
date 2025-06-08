from django.urls import path
from . import views

urlpatterns = [
    # Authority dashboard
    path('dashboard/', views.dashboard_view, name='authority_dashboard'),

    path('api/appointments/', views.get_appointments_json, name='api_appointments'),
    
    # Appointment management
    path('appointments/', views.authority_appointments_view, name='authority_appointments'),
    path('appointment/<int:appointment_id>/', views.appointment_detail_view, name='appointment_detail'),
    path('appointment/<int:appointment_id>/approve/', views.approve_appointment_view, name='approve_appointment'),
    path('appointment/<int:appointment_id>/reject/', views.reject_appointment_view, name='reject_appointment'),
    path('appointment/<int:appointment_id>/update-status/', views.update_appointment_status_view, name='update_appointment_status'),
    
    # Service management
    path('services/', views.manage_services_view, name='manage_services'),
    path('service/add/', views.add_service_view, name='add_service'),
    path('service/<int:service_id>/edit/', views.edit_service_view, name='edit_service'),
    path('service/<int:service_id>/delete/', views.delete_service_view, name='delete_service'),
    
    # Doctor management
    path('doctors/', views.manage_doctors_view, name='manage_doctors'),
    path('doctor/add/', views.add_doctor_view, name='add_doctor'),
    path('doctor/<int:doctor_id>/edit/', views.edit_doctor_view, name='edit_doctor'),
    path('doctor/<int:doctor_id>/delete/', views.delete_doctor_view, name='delete_doctor'),
    path('doctor/<int:doctor_id>/change-status/', views.change_doctor_status, name='change_doctor_status'),
    
    # Time slot management
    path('slots/', views.manage_slots_view, name='manage_slots'),
    path('slot/add/', views.add_slot_view, name='add_slot'),
    path('slot/<int:slot_id>/edit/', views.edit_slot_view, name='edit_slot'),
    path('slot/<int:slot_id>/delete/', views.delete_slot_view, name='delete_slot'),
    path('slot/<int:slot_id>/change-status/', views.change_slot_status, name='change_slot_status'),  # Added this line
    
    # Profile management
    path('profile/', views.authority_profile_view, name='authority_profile'),
    path('profile/edit/', views.edit_authority_profile_view, name='edit_authority_profile'),
]   